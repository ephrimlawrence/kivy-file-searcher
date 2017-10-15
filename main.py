# [imports]
import json
import sqlite3
import threading
from functools import partial

from kivy.app import App
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image

from kivymd.theming import ThemeManager
from kivymd.button import MDIconButton
from kivymd.selectioncontrols import MDCheckbox
from kivymd.list import ILeftBody, ILeftBodyTouch, IRightBodyTouch
from kivy.metrics import dp

from kivymd.label import MDLabel
from kivymd.dialog import MDDialog
from kivymd.list import MDList, OneLineAvatarIconListItem
from kivymd.list import OneLineListItem, TwoLineListItem
# [end imports]

# TODO: generate icons for both projects
# TODO: add more file extensions

db_connection = sqlite3.connect("assets/indexed-files.db")
db_cursor = db_connection.cursor()

audio_search_results = None
image_search_results = None
document_search_results = None
video_search_results = None
others = None


def search_for_files(search_string, file_type, results_variable):
    """
    Query for the file_name, and file_path
    from the 'files' table in 'indexed-files-db'
    if the file_type column == matches parameter 'file_type'

    parameters:
        search_string: The string the to search for

        file_type: The type of the file for query for. e.g. audio, document,
        imaimage

        results_variable: The variable to save the query results to. It should
        be a global variable.

    return: It returns the query in dic form.
    """
    query = "SELECT file_name, file_path FROM files WHERE file_type = " + repr(
        file_type)
    db_cursor.execute(query)

    if results_variable == 'video_search_results':
        global video_search_results
        video_search_results = {
            file_name: {file_path}
            for file_name, file_path in db_cursor
            if search_string.lower() in file_name.lower()
        }
    elif results_variable == 'audio_search_results':
        global audio_search_results
        audio_search_results = {
            file_name: {file_path}
            for file_name, file_path in db_cursor
            if search_string.lower() in file_name.lower()
        }
    elif results_variable == 'document_search_results':
        global document_search_results
        document_search_results = {
            file_name: {file_path}
            for file_name, file_path in db_cursor
            if search_string.lower() in file_name.lower()
        }
    elif results_variable == 'image_search_results':
        global image_search_results
        image_search_results = {
            file_name: {file_path}
            for file_name, file_path in db_cursor
            if search_string.lower() in file_name.lower()
        }
    print("Query Ended")

    return


class FileSearcherApp(App):
    """File Searcher App."""

    def __init__(self, **kwargs):
        super(FileSearcherApp, self).__init__(**kwargs)
        self.title = "Find Anything"
        self.theme_cls = ThemeManager()
        self.screens_list = ['home']
        self.user_settings = JsonStore('assets/user_settings.json')
        self.on_pause
        self.on_resume

        # update the theme using save user settings
        if self.user_settings.exists('theme'):
            self.theme_cls.theme_style = self.user_settings.get('theme')[
                'style']
            self.theme_cls.primary_palette = self.user_settings.get('theme')[
                'priamry_palette']
            self.theme_cls.accent_palette = self.user_settings.get('theme')[
                'accent_palette']

        if platform == 'android':
            from jnius import autoclass
            service = autoclass('com.ephrim.filesearcher.ServiceMyservice')
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            argument = 'Running Activity'
            service.start(mActivity, argument)

        from kivy.core.window import Window
        Window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *args):
        """
        hook_keyboard function This function is called on whenever the back
        button 'on android' or esc key 'on pc' is pressed.
        It returns the user to the previous screen
        """
        if key == 27 and self.root.ids._scr_mngr.current == 'home':
            return False
        elif key == 27:
            del (self.screens_list[-1])
            self.root.ids._scr_mngr.current = self.screens_list[-1]
            return True

    def on_pause(self):
        print('App Paused')
        return True

    def on_resume(self):
        print('App Resumed')
        pass

    def show_files_extensions(self, file_type):
        ''' Loads the files extension settings from the assets/file_extension.json
            it is called when either 'Document, Video, Image or Audoi' List items is pressed.
            After loading, it is shown in a dialog

            :parameters:
                file_type --> extension key in the json_file e.g 'document_extensions

            :return:
                opens a dialog
         '''

        files_extension = JsonStore('assets/files_extension.json')
        dialog_content = MDList()
        self.dialog = None

        for extension in files_extension.get(file_type):
            # trim '.' from the file extension e.g. '.pdf', and add doc_ext_
            # to itso it becomes 'doc_ext_pdf' and use it as the widget id.
            icon_right_sample_widget = IconRightSampleWidget(
                id="doc_ext_" + extension[1:])

            if files_extension.get(file_type)[extension]:
                icon_right_sample_widget.active = True

            # trim '.'from the file extension e.g. '.pdf', and
            # convert it to uppercase
            # so it comes 'PDF'
            list_item = OneLineAvatarIconListItem(text=extension[1:].upper())
            list_item.add_widget(icon_right_sample_widget)
            dialog_content.add_widget(list_item)

        self.dialog = MDDialog(
            title="Select file extensions to include in search",
            content=dialog_content,
            size_hint=(.8, None),
            height=self.root.height - dp((self.root.height / 2) / 8),
            auto_dismiss=False)

        self.dialog.add_action_button(
            "DONE", action=lambda *x: self.dialog.dismiss())

        # bind the dialog to self.save_extensions method when it is closed
        self.dialog.bind(on_dismiss=partial(self.save_extensions, file_type))
        self.dialog.open()

    def save_extensions(self, file_type, instance):
        ''' update the assets/files_extension.json file with the extensions
            selected by the user

            :parameters:
                file_type --> extension key in the json_file e.g 'document_extensions

            :return:
                nothing, just write the user extensions settings to the file
        '''

        with open('assets/files_extension.json') as in_file:
            files_extension = json.load(in_file)

        for child in instance.children:

            # get the id of the document typs icon_right_sample_widget
            # (checkbox) with this trick
            # for betting understanding, I suggest you use print statements
            for a in child.children[1].children[0].children[0].children[
                    0].children:
                for b in a.children:
                    for c in b.children:

                        # try..except is used here because,
                        # the id of some of 'c' children is 'None' and this
                        # will raise an exception and terminate the program
                        try:
                            for ext in files_extension[file_type]:

                                # trim the c.id, e.g. 'doc_ext_pdf' --> 'pdf'
                                # and add '.' to it so it become '.pdf'
                                # compare it with the value of ext
                                if "." + c.id[8:] == ext:
                                    extension = "." + c.id[8:]
                                    files_extension[file_type][
                                        extension] = c.active

                        except Exception as e:
                            # no exception is raised here
                            pass

        # write the settings to the file and close it
        with open('assets/files_extension.json', mode='w') as out_file:
            out_file.write(json.dumps(files_extension, indent=4))
        out_file.close()

    def save_user_settings(self):
        """
        update 'user_settings.json file with the settings given by the user
        """

        # save theme settings
        self.user_settings.put(
            'theme',
            style=self.theme_cls.theme_style,
            primary_palette=self.theme_cls.primary_palette,
            accent_palette=self.theme_cls.accent_palette)

        return self.user_settings

    def search_files(self):
        """Search for the text entered by the user in
            self.root.ids._search_text_field
        """

        search_text = self.root.ids._search_text_field.text

        if search_text == "" or search_text == " ":
            return

        global audio_search_results, video_search_results
        global document_search_results, image_search_results
        global others

        threading.Thread(target=search_for_files(
            search_text, 'audio', 'audio_search_results')).start()
        threading.Thread(target=search_for_files(
            search_text, 'video', 'video_search_results')).start()
        threading.Thread(target=search_for_files(
            search_text, 'image', 'image_search_results')).start()
        threading.Thread(target=search_for_files(
            search_text, 'document', 'document_search_results')).start()

        self.root.ids._search_results_list.clear_widgets()

        results = [
            audio_search_results, video_search_results,
            document_search_results, image_search_results
        ]

        for search_results in results:
            if search_results is not None:
                for i in search_results:
                    display_files = OneLineListItem(text=i)
                    display_files.bind(on_release=partial(
                        self.open_file, search_results[i].pop()))
                    self.root.ids._search_results_list.add_widget(
                        display_files)

        if len(self.root.ids._search_results_list.children) == 0:
            no_result = TwoLineListItem(
                text="No files were found for your search " +
                repr(search_text))
            self.root.ids._search_results_list.add_widget(no_result)

    def open_file(self, file_path, instance):
        if platform == 'android':
            from jnius import autoclass, cast

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')

            uri_file = File(file_path)
            uri = Uri.fromFile(uri_file)

            intent = Intent()
            intent.setAction(Intent.ACTION_VIEW)

            if file_path.endswith('.doc') or file_path.endswith('.docx'):
                intent.setDataAndType(uri, "application/msword")
            elif file_path.endswith('.ppt') or file_path.endswith('.pptx'):
                intent.setDataAndType(uri, "application/vnd.ms-powerpoint")
            elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                intent.setDataAndType(uri, "application/vnd.ms-excel")
            elif file_path.endswith('.zip') or file_path.endswith('.rar'):
                intent.setDataAndType(uri, "application/zip")
            elif file_path.endswith('.rtf'):
                intent.setDataAndType(uri, "application/rtf")
            elif file_path.endswith('.wav') or file_path.endswith('.mp3'):
                intent.setDataAndType(uri, "application/x-wav")
            elif file_path.endswith('.gif'):
                intent.setDataAndType(uri, "image/gif")
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                intent.setDataAndType(uri, "image/jpeg")
            elif file_path.endswith('.png'):
                intent.setDataAndType(uri, "image/jpeg")
            elif file_path.endswith('.pdf'):
                intent.setDataAndType(uri, "application/pdf")
            elif file_path.endswith('.txt'):
                intent.setDataAndType(uri, "text/plain")
            elif file_path.endswith('.3gp') or file_path.endswith('.mp4'):
                intent.setDataAndType(uri, "video/*")
            elif file_path.endswith('.mpg') or file_path.endswith('.mpeg'):
                intent.setDataAndType(uri, "video/*")
            elif file_path.endswith('.mpe') or file_path.endswith('.avi'):
                intent.setDataAndType(uri, "video/*")
            else:
                intent.setDataAndType(uri, "*/*")

            activity = cast('android.app.Activity', PythonActivity.mActivity)
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)

            activity.startActivity(intent)

    def show_about_dialog(self):
        """ Shows the About dialog box"""
        content = MDLabel(
            font_style='Body1',
            markup=True,
            theme_text_color='Secondary',
            text="Find Anything is developed by Lawrence Ephrim.\n\n"
            "You can find me at:\n"
            "-Facebook:\n"
            "  [color=#31C8EB][u][ref=https://www.facebook.com/profile.php?id=100004673359024]https://www.facebook.com/profile.php?id=100004673359024\n[/ref][/u][/color]"
            "-Telegram:\n"
            "  [color=#31C8EB][u][ref=t.me/ephrimlawrence]t.me/ephrimlawrence\n[/ref][/u][/color]"
            "-Email:\n"
            "  [color=#31C8EB][u]ephrimlawrence@gmail.com\n\n[/u][/color]"
            "© Copyright All Rights Reserved",
            size_hint_y=None,
            valign='top')

        content.bind(texture_size=content.setter('size'))
        content.bind(on_ref_press=self.open_link)

        self.dialog = MDDialog(
            title="About",
            content=content,
            size_hint=(.8, None),
            height=self.root.height - dp((self.root.height / 3)),
            auto_dismiss=False)

        self.dialog.add_action_button(
            "Dismiss", action=lambda *x: self.dialog.dismiss())
        self.dialog.open()

    def open_link(self, instance, value):
        """ Open a link in the default web browser """
        import subprocess
        import webbrowser
        import sys

        if sys.platform == 'darwin':
            subprocess.Popen(['open', value])
        else:
            webbrowser.open_new_tab(value)


class IconLeftSampleWidget(ILeftBodyTouch, MDIconButton):
    pass


class IconRightSampleWidget(IRightBodyTouch, MDCheckbox):
    pass


class AvatarSampleWidget(ILeftBody, Image):
    pass


if __name__ == "__main__":
    FileSearcherApp().run()
