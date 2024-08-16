import sublime
import sublime_plugin

import os
import json

from typing import Optional

def is_remote(window: sublime.Window) -> bool:
    folders = window.folders()
    for folder in folders:
        if os.path.isfile(os.path.join(folder, "sftp-config.json")):
            return True

    return False

def remote_sync(window: sublime.Window):
    # Re-sync the active window folders. Really only need the root folder, but this is probably fine.
    syncArgs = {
        "paths": window.folders()
    }

    window.run_command("sftp_sync_both", syncArgs)

class RemoteAssistEventListener(sublime_plugin.EventListener):
    # On folder loads, force a full SFTP sync to gather any new directory changes, such as new files.
    def on_new_window_async(self, window):
        if is_remote(window):
            remote_sync(window)

            window.status_message("[REMOTE]")

    # When deleting files locally, delete them on the remote as well.
    def on_window_command(self, window: sublime.Window, command_name: str, args):
        if command_name == "delete_file":
            if is_remote(window):
                deleteArgs = {
                    "files": args["files"],
                }

                window.run_command("sftp_delete_remote_path", deleteArgs)

        if command_name == "delete_folder":
            if is_remote(window):
                deleteArgs = {
                    "dirs": args["dirs"],
                }

                window.run_command("sftp_delete_remote_path", deleteArgs)

        return None

class RemoteSyncCommand(sublime_plugin.WindowCommand):
    def run(self):
        remote_sync(self.window)

# Helper to only execute commands when the current window is a remote folder.
class ExecuteIfRemoteCommand(sublime_plugin.WindowCommand):
    def run(self, command: str, args: dict = {}, false_command: Optional[str] = None, false_args: dict = {}):
        if is_remote(self.window):
            self.window.run_command(command, args)
        elif false_command is not None:
            self.window.run_command(false_command, false_args)

class OpenRemoteFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel("Remote login:", "user@hostname", self.on_login_prompt, None, None)
        #arg = {"args": {"placeholder": "test", "point": 2237}, "command": "lsp_symbol_rename", "overlay": "command_palette"}
        #self.window.run_command("show_overlay", arg)

    def on_login_prompt(self, text):
        print(f"on_login_prompt: {text}")
        self.window.show_input_panel("Remote password:", "", self.on_password_prompt, None, None)

    def on_password_prompt(self, text):
        print(f"on_password_prompt: {text}")
        sublime.select_folder_dialog(self.on_local_folder_prompt, multi_select=False)

    def on_local_folder_prompt(self, local_folder):
        print(f"on_local_folder_prompt: str={local_folder}")

        # This prompts the user again, not correct
        self.window.run_command("open_dir", { "dir": local_folder })

        print("HERE IN NEW CONTEXT!!")
        print(f"folders={self.window.folders()}")

        remoteHost = ""
        remoteUser = ""
        remotePath = ""

        # Generate the sftp-config.json
        sftpConfig = {
            "type": "sftp",
            "sync_down_on_open": True,
            "sync_same_age": True,
            "host": remoteHost,
            "user": remoteUser,
            "remote_path": remotePath,
            "connect_timeout": 30,
            "confirm_downloads": False,
            "confirm_sync": False,
            "confirm_overwrite_newer": False,
            "upload_on_save": False,
        }

        # Determine this from the new window?
        localFolder = self.window.folders()[0]

        print(f"my localFolder is {localFolder}")
        return

        with open(os.path.join(localFolder, "sftp-config.json")) as sftpFile:
            sftpFile.write(json.dumps(sftpConfig))
