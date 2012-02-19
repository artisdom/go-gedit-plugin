# -*- coding: utf-8 -*-

from gettext import gettext as _
import gtk
import subprocess
import glib
import utils
from completion import GoProvider
import unicodedata

# Go menu items
ui_str = """
<ui>
    <menubar name="MenuBar">
        <menu name="EditMenu" action="Edit">
            <placeholder name="EditOps_4">
                <menuitem name="ToggleComment" action="ToggleComment"/>
                <menuitem name="ToggleBlockComment" action="ToggleBlockComment"/>
            </placeholder>
        </menu>
    </menubar>
    <menubar name="MenuBar">
        <menu name="ToolsMenu" action="Tools">
            <placeholder name="ToolsOps_3">
                <menuitem name="Format" action="Format"/>
            </placeholder>
        </menu>
    </menubar>
</ui>
"""

class GoWindowHelper:
    def __init__(self, plugin, window):
        self._plugin = plugin
        self._window = window
        self._signalobjs = {"save": {}, "key-press-event": {}}

        self._provider = GoProvider(self._plugin)

        # Insert menu items
        self._insert_menu()

        for view in self._window.get_views():
            self._on_add_view(view)

        self._tab_added_id = self._window.connect('tab-added', self._on_tab_added)
        self._tab_removed_id = self._window.connect('tab-removed', self._on_tab_removed)

    def deactivate(self):
        # Remove the provider from all the views
        for view in self._window.get_views():
            view.get_completion().remove_provider(self._provider)

        # disconnect all signals in the window
        self._window.disconnect(self._tab_added_id)
        self._window.disconnect(self._tab_removed_id)

        for sobjects in self._signalobjs.values():
            for object, sid in sobjects.items():
                object.disconnect(sid)

        # Remove any installed menu items
        self._remove_menu()

        self._window = None
        self._plugin = None
        self._action_group = None

    def _on_add_view(self, view):
        completion = view.get_completion()
        completion.add_provider(self._provider)
        completion.connect('populate-context', self._on_populate_context)

    def _on_remove_view(self, view):
        completion = view.get_completion()
        completion.remove_provider(self._provider)

    def _on_tab_added(self, window, tab):
        # Add provider to the new view
        self._on_add_view(tab.get_view())

    def _on_tab_removed(self, window, tab):
        # Remove provider from the view
        self._on_remove_view(tab.get_view())

    def _on_populate_context(self, completion, context):
        completion.set_property("select-on-show", True)
        completion.set_property("accelerators", 0)
        completion.set_property("show-headers", True)
        completion.set_property("show-icons", True)
        completion.set_property("remember-info-visibility", True)

    def _insert_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Create a new action group
        self._action_group = gtk.ActionGroup("GoPluginActions")
        self._action_group.add_actions([("ToggleComment", None, _("Toggle comment"),
                                         '<Control>3', _("Toggle comment"),
                                         self._toggle_line_comment),
                                         ("ToggleBlockComment", None, _("Toggle block comment"),
                                         '<Control>4', _("Toggle block comment"),
                                         self._toggle_block_comment),
                                         ("Format", None, _("Format (gofmt)"),
                                         '<Control><Shift>f', _("Format code with the gofmt formatting tool"),
                                         self._format_action)])

        # Insert the action group
        manager.insert_action_group(self._action_group, -1)

        # Merge the UI
        self._ui_id = manager.add_ui_from_string(ui_str)

    def _remove_menu(self):
        # Get the GtkUIManager
        manager = self._window.get_ui_manager()

        # Remove the ui
        manager.remove_ui(self._ui_id)

        # Remove the action group
        manager.remove_action_group(self._action_group)

        # Make sure the manager updates
        manager.ensure_update()

    def _toggle_line_comment(self, action):
        """
        Toggles line comment in the selection.
        """
        buffer = self._window.get_active_document()

        if buffer == None:
            return

        bounds = buffer.get_selection_bounds()

        if len(bounds) == 0:
            # no selection
            start_line_nb = utils.get_iter_cursor(buffer).get_line()
            end_line_nb = start_line_nb
        else:
            start_line_nb = bounds[0].get_line()
            end_line_nb = bounds[1].get_line()

        # check if all of the lines begin with '//'
        add_mode = False
        for line_nb in xrange(start_line_nb, end_line_nb + 1):
            lcs_start = buffer.get_iter_at_line(line_nb)

            # skip indentation whitespace
            while lcs_start.get_char() in ('\t', ' '):
                lcs_start.forward_char()

            lcs_end = lcs_start.copy()
            lcs_end.forward_chars(2)

            lcs = buffer.get_slice(lcs_start, lcs_end)
            if lcs != '//':
                add_mode = True
                break

        if add_mode:
            # add '//' to beginning of all selection lines
            buffer.begin_user_action()
            for i in xrange(start_line_nb, end_line_nb + 1):
                buffer.insert(buffer.get_iter_at_line(i), "//")
            buffer.end_user_action()
        else:
            # remove '//' from beginning of all selection lines
            buffer.begin_user_action()
            for i in xrange(start_line_nb, end_line_nb + 1):
                lcs_start = buffer.get_iter_at_line(i)

                # skip indentation whitespace
                while lcs_start.get_char() in ('\t', ' '):
                    lcs_start.forward_char()

                lcs_end = lcs_start.copy()
                lcs_end.forward_chars(2)

                buffer.delete(lcs_start, lcs_end)
            buffer.end_user_action()

    def _toggle_block_comment(self, action):
        """
        Toggles block comment in the selection.
        """
        buffer = self._window.get_active_document()

        if buffer == None or len(buffer.get_selection_bounds()) == 0:
            return

        buffer.begin_user_action()

        bounds = buffer.get_selection_bounds()

        starting_block_end, ending_block_start = buffer.get_selection_bounds()
        starting_block_end.forward_chars(2)
        ending_block_start.backward_chars(2)
        if bounds[0].get_slice(starting_block_end) == '/*' and \
        ending_block_start.get_slice(bounds[1]) == '*/':
            # remove comment block
            buffer.delete(bounds[0], starting_block_end)

            bounds = buffer.get_selection_bounds()
            __, ending_block_start = buffer.get_selection_bounds()
            ending_block_start.backward_chars(2)

            buffer.delete(ending_block_start, bounds[1])
        else:
            # insert comment block 
            buffer.insert(bounds[0], "/*")

            # move starting selection bound backwards to include the starting block
            bounds = buffer.get_selection_bounds()
            bounds[0].backward_chars(2)
            buffer.move_mark_by_name("selection_bound", bounds[0])
            buffer.move_mark_by_name("insert", bounds[1])

            bounds = buffer.get_selection_bounds()
            buffer.insert(bounds[1], "*/")

        buffer.end_user_action()

    def _format_action(self, action):
        # Show error dialog
        self._format(True)

    def format_on_save(self, arg1, arg2, arg3, arg4):
        # Do not show error dialog
        self._format(False)

    def _format(self, show_err):
        buffer = self._window.get_active_document()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

        try:
            p = subprocess.Popen([self._plugin.model.gobin_path + '/gofmt'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

            stdoutdata, stderrdata = p.communicate(text)
        except OSError as e:
            if show_err:
                dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                           type=gtk.MESSAGE_ERROR,
                                           buttons=gtk.BUTTONS_OK)
                dialog.set_markup(_("An error occurred when <i>gofmt</i> was attempted to run:"))
                dialog.format_secondary_markup('<span font_family="monospace">' +
                                               glib.markup_escape_text(str(e)) +
                                               '</span>')
                dialog.run()
                dialog.destroy()

        if len(stderrdata) != 0:
            if show_err:
                dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                           type=gtk.MESSAGE_ERROR,
                                           buttons=gtk.BUTTONS_OK)
                dialog.set_markup(_("An error occurred while running <i>gofmt</i>:"))
                if len(stderrdata) > utils.MAX_ERR_MSG_LEN: # cut down too long error messages
                    stderrdata = stderrdata[:utils.MAX_ERR_MSG_LEN] + "..."
                dialog.format_secondary_markup('<span font_family="monospace">' +
                                               glib.markup_escape_text(stderrdata) +
                                               '</span>')
                dialog.run()
                dialog.destroy()
            return

        # save the cursor position before modifying the document
        cursor_iter = utils.get_iter_cursor(buffer)
        offset = cursor_iter.get_offset()
        old_buf_len = buffer.get_char_count()

        buffer.begin_user_action()

        buffer.set_text(stdoutdata)

        # attempt to return the cursor back to where it was
        new_buf_len = buffer.get_char_count()
        # adjust offset to account for indentation changes
        new_offset = offset + (new_buf_len - old_buf_len)
        buffer.place_cursor(buffer.get_iter_at_offset(new_offset))
        view = self._window.get_active_view()
        utils.scroll_to_insert(buffer, view)

        buffer.end_user_action()

    def update_ui(self):
        buffer = self._window.get_active_document()

        golang = False
        if buffer != None:
            language = buffer.get_language()
            if language != None:
                if language.get_id() == 'go':
                    golang = True

        if golang:
            if buffer != None:
                view = self._window.get_active_view()

                self._action_group.set_sensitive(True)
                # add key-press-event signal
                if view not in self._signalobjs['key-press-event']:
                    self._signalobjs['key-press-event'][view] = view.connect('key-press-event', self.on_key_press, buffer)
                # toggle format on save
                if buffer not in self._signalobjs['save']:
                    if self._plugin.model.format_on_save:
                        self._signalobjs['save'][buffer] = buffer.connect('save', self.format_on_save)
                elif not self._plugin.model.format_on_save:
                    buffer.disconnect(self._signalobjs['save'][buffer])
                    del self._signalobjs['save'][buffer]
            else:
                self._action_group.set_sensitive(False)

    def on_key_press(self, view, event, buffer):
        key_name = gtk.gdk.keyval_name(event.keyval)

        # if user deletes non-letter or non-decimal-digit unicode character then hide code completion window
        if key_name == 'BackSpace':
            delchariter = utils.get_iter_cursor(buffer)
            delchariter.backward_char()
            del_char = delchariter.get_char()
            # L == letter, Nd  == number, decimal digit
            if unicodedata.category(del_char)[0] != 'L' and unicodedata.category(del_char) != 'Nd':
                completion = view.get_completion()
                completion.hide()
