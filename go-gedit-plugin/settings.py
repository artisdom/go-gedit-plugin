# -*- coding: utf-8 -*-

import json
import os

class SettingsModel:

    def __init__(self, plugin):
        self._plugin = plugin

        self.format_on_save = False
        self.gobin_path = os.getenv("GOBIN", "")

        self.path = plugin.get_data_dir() + os.sep

        self._persistenceService = JSONStorageService(self)

    def load(self):
        self._persistenceService.load()

    def save(self):
        self._persistenceService.save()

class JSONStorageService():

    def __init__(self, model):
        self.model = model

        self.json_path = os.path.expanduser("%s%s" % (self.model.path, "settings.json"))
        self.settings = dict()

    def load(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r") as f:
                self.settings = json.load(f)

            self.model.format_on_save = self.settings["format_on_save"]
            self.model.gobin_path = self.settings["gobin_path"]

    def save(self):
        self.settings["format_on_save"] = self.model.format_on_save
        self.settings["gobin_path"] = self.model.gobin_path
        with open(self.json_path, "w") as f:
            json.dump(self.settings, f)
