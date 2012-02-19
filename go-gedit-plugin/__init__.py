# -*- coding: utf-8 -*-

import gedit
import gtk
from window import GoWindowHelper
from config import ConfigurationDialog
from settings import SettingsModel
import sys
import os

class GoPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self._instances = {}
        self.views = {}
        self.icons = {}
        self._icons_path = self.get_install_dir() + os.sep + self.__module__ + os.sep + "icons" + os.sep

        self.model = SettingsModel(self)
        self.model.load()
        self.update_path()

        # load completion icons
        self._load_completion_icons()

    def activate(self, window):
        self._instances[window] = GoWindowHelper(self, window)

    def deactivate(self, window):
        self._instances[window].deactivate()
        del self._instances[window]

    def update_ui(self, window):
        self._instances[window].update_ui()

    def update_all_ui(self):
        for instance in self._instances:
            self.update_ui(instance)

    def is_configurable(self):
        return True

    def create_configure_dialog(self):
        return ConfigurationDialog(self).dialog

    def update_path(self):
        # make sure $GOBIN is in $PATH
        if self.model.gobin_path not in os.getenv("PATH", "").split(":"):
            os.environ["PATH"] += ":" + self.model.gobin_path

    def _load_completion_icons(self):
        self.icons['var'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "var16.png")
        self.icons['const'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "const16.png")
        self.icons['func'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "func16.png")
        self.icons['interface'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "interface16.png")
        self.icons['package'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "package16.png")
        self.icons['struct'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "struct16.png")
        self.icons['gopher'] = gtk.gdk.pixbuf_new_from_file(self._icons_path + "gopher16.png")
