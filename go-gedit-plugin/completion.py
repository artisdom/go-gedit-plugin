# -*- coding: utf-8 -*-

import gobject
import gtksourceview2 as gsv
from gettext import gettext as _
import utils
import gtk
import subprocess
import glib
import json

class GoProvider(gobject.GObject, gsv.CompletionProvider):
    __gtype_name__ = 'GoProvider'

    def __init__(self, plugin):
        gobject.GObject.__init__(self)
        self._plugin = plugin

    def do_get_start_iter(self, context, proposal):
        return utils.get_iter_cursor(context.get_iter().get_buffer())

    def do_get_name(self):
        return _("Go code completion")
    
    def do_get_icon(self):
        return self._plugin.icons['gopher']

    def do_match(self, context):
        lang = context.get_iter().get_buffer().get_language()

        if not lang:
            return False

        if lang.get_id() != 'go':
            return False

        return True

    def do_populate(self, context):
        buffer = context.get_iter().get_buffer()
        odata = self._get_odata(buffer, utils.get_iter_cursor(buffer))

        if not odata:
            # no proposals
            return context.add_proposals(self, [], True)
        
        proposals = []
        for po in self._get_podata(odata):
                proposals.append(gsv.CompletionItem(po[0], po[1], po[2], po[3]))

        context.add_proposals(self, proposals, True)

    def do_get_activation(self):
        return gsv.COMPLETION_ACTIVATION_USER_REQUESTED

    def _get_odata(self, buffer, cursor_iter):
        """
        Return gocode object data.
        """ 
        cursor_offset = cursor_iter.get_offset()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        byte_offset = len(buffer.get_text(buffer.get_start_iter(), buffer.get_iter_at_offset(cursor_offset)))
        try:
            p = subprocess.Popen([self._plugin.model.gobin_path + '/gocode',
                                '-f=json',
                                'autocomplete',
                                buffer.get_uri_for_display(),
                                str(byte_offset)],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        except OSError as e:
            dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                       type=gtk.MESSAGE_ERROR,
                                       buttons=gtk.BUTTONS_OK)
            dialog.set_markup(_("An error occurred when <i>gocode</i> was attempted to run:"))
            dialog.format_secondary_markup('<span font_family="monospace">' +
                                           glib.markup_escape_text(str(e)) +
                                           '</span>')
            dialog.run()
            dialog.destroy()
            return []

        stdoutdata, stderrdata = p.communicate(text)

        if len(stderrdata) != 0:
            dialog = gtk.MessageDialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                       type=gtk.MESSAGE_ERROR,
                                       buttons=gtk.BUTTONS_OK)
            dialog.set_markup(_("An error occurred while running <i>gocode</i>:"))
            if len(stderrdata) > utils.MAX_ERR_MSG_LEN: # cut down too long error messages
                stderrdata = stderrdata[:utils.MAX_ERR_MSG_LEN] + "..."
            dialog.format_secondary_markup('<span font_family="monospace">' +
                                           glib.markup_escape_text(stderrdata) +
                                           '</span>')
            dialog.run()
            dialog.destroy()
            return []

        try:
            return json.loads(stdoutdata)
        except ValueError:
            print "ERROR: gocode input was invalid."
            return []

    def _get_podata(self, odata):
        """
        Return parsed gocode's object data.
        """
        podata = []
        for candidate in odata[1]:
            if candidate['class'] == "func":
                info = candidate['class'] + " " + candidate['name'] + candidate['type'][len("func"):]
                icon = self._plugin.icons['func']
            else:
                info = candidate['class'] + " " + candidate['name'] + " " + candidate['type']

                icon = self._plugin.icons['var'] # default
                if candidate['class'] == "const":
                    icon = self._plugin.icons['const']
                elif candidate['class'] == "package":
                    icon = self._plugin.icons['package']
                elif candidate['class'] == "type":
                    if candidate['type'] == "interface":
                        icon = self._plugin.icons['interface']
                    elif candidate['type'] == "struct":
                        icon = self._plugin.icons['struct']

            podata.append((candidate['name'],
                           candidate['name'][odata[0]:],
                           icon,
                           info))
        return podata

gobject.type_register(GoProvider)
