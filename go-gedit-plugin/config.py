# -*- coding: utf-8 -*-

import gtk
import sys
import os

class ConfigurationDialog:
    def __init__(self, plugin):
        self._plugin = plugin
        
        try:
            builder = gtk.Builder()
            builder.add_from_file(plugin.get_install_dir() + os.sep + plugin.__module__ + os.sep + "config.glade")

        except Exception, e:
            print str(e)
            sys.exit(1)
            
        self.dialog = builder.get_object("dialog")
        self.format_on_save_check_button = builder.get_object("format_on_save_check_button")
        self.gobin_path_button = builder.get_object("gobin_path_button") 
        
        # connect signals
        builder.connect_signals(self)
        
        # update states
        if self._plugin.model.format_on_save:
            self.format_on_save_check_button.set_active(True)
        self.gobin_path_button.set_filename(self._plugin.model.gobin_path)

    def on_ok_button_clicked(self, button):
        # format_on_save
        if self.format_on_save_check_button.get_active():
            self._plugin.model.format_on_save = True
        else:
            self._plugin.model.format_on_save = False
            
        # gobin_path
        self._plugin.model.gobin_path = self.gobin_path_button.get_filename() 
        self._plugin.update_path()
        
        # save and update current uis
        self._plugin.model.save()
        self._plugin.update_all_ui()
        
        self.dialog.destroy()
    
    def gtk_widget_destroy(self, button):
        self.dialog.destroy()
