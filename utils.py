import sublime
import sublime_plugin

import inspect
import json
import os
import sys

from sublime_plugin import application_command_classes
from sublime_plugin import window_command_classes
from sublime_plugin import text_command_classes

# Utility to view all commands and their arguments, from ODatNurd
# https://stackoverflow.com/a/48657046
class ListAllCommandsCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.view.set_name("Command List")

        self.list_category("Application Commands", application_command_classes)
        self.list_category("Window Commands", window_command_classes)
        self.list_category("Text Commands", text_command_classes)

    def append(self, line):
        self.view.run_command("append", {"characters": line + "\n"})

    def list_category(self, title, command_list):
        self.append(title)
        self.append(len(title)*"=")

        for command in command_list:
            self.append("{cmd} {args}".format(
                cmd=self.get_name(command),
                args=str(inspect.signature(command.run))))

        self.append("")

    def get_name(self, cls):
        clsname = cls.__name__
        name = clsname[0].lower()
        last_upper = False
        for c in clsname[1:]:
            if c.isupper() and not last_upper:
                name += '_'
                name += c.lower()
            else:
                name += c
            last_upper = c.isupper()
        if name.endswith("_command"):
            name = name[0:-8]
        return name

# Plugin hot-patching
# TODO: wrap in on_plugin_load() callback or something?
#####################

# Hack SFTP's licensing code
def sftp_ff(v):
    def _(components):
        return True

    return _

def sftp_pk(k):
    return False

if "SFTP.sftp.commands" in sys.modules:
    print("Patching SFTP...")
    sftpCmdModule = sys.modules["SFTP.sftp.commands"]
    sftpCmdModule._ff = sftp_ff
    sftpCmdModule._pk = sftp_pk

# Remove SFTP's file menu (use remote assist instead)
sftpMainMenuPath = os.path.join(sublime.packages_path(), "SFTP", "Main.sublime-menu")
if os.path.isfile(sftpMainMenuPath):
    sftpMenu = None
    modified = False

    with open(sftpMainMenuPath, "r") as sftpMenuFile:
        sftpMenu = json.loads(sftpMenuFile.read())

        for i, element in enumerate(sftpMenu):
            if "id" in element and element["id"] == "file":
                del sftpMenu[i]
                modified = True

    if modified:
        with open(sftpMainMenuPath, "w") as sftpMenuFile:
            sftpMenuFile.write(json.dumps(sftpMenu, indent=4))
