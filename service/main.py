"""
This is the background service file which is called when
the app is opened. It runs in the foreground untill the use
reboot or the system kill it when there is not enough space
on the system.
It indexes the files on the sdcard(s) every 30 minutes and
saves them to a database
"""

# [imports]
import os
import json
import sqlite3
from time import sleep
from kivy.utils import platform
# [end]

# recieves argument from main.app file
arg = os.getenv('PYTHON_SERVICE_ARGUMENT')

"""
1. Checks the platform (for testing)
2. Gets the path to the both the internal and external
    sdcard(s) if any.
3. Creates a database connection to 'assets/indexed-files.db' file
4. Reads the file extensions to check for when indexing
    from 'assets/files_extension.json' file
"""
if platform == 'android':
    from jnius import autoclass
    java_system = autoclass("java.lang.System")
    sdcard_paths = [java_system.getenv("EXTERNAL_STORAGE"),
                    java_system.getenv("SECONDARY_STORAGE")]
    exclude_folders = [".com.", ".org.", "."]
    db_connection = sqlite3.connect('assets/indexed-files.db')
    with open('assets/files_extension.json') as in_file:
        file_extensions = json.load(in_file)
else:
    # will be removed after testing before release
    sdcard_paths = ['/home/lephrim']
    exclude_folders = [".com.", ".org.", "."]
    db_connection = sqlite3.connect('assets/indexed-files.db')
    with open('assets/files_extension.json') as in_file:
        file_extensions = json.load(in_file)


def get_extensions(extension_name):
    """Returns all the extensions in the
    'file_extensions.json' in the give 'extension_name'

    parameters:
        extension_name: The type of extension for return.
            e.g. 'document_extensions', 'audio_extensions'
    """
    extensions = [x for x in file_extensions[extension_name]]
    return extensions

# creat db connection cursor
db_cursor = db_connection.cursor()

# creates list of file extensions
extensions = [y for x in file_extensions for y in file_extensions[x]
            if file_extensions[x][y]]

# Enters the main loop
if __name__ == "__main__":
    while True:
        # Clear the database, index the files, wait for 30 minutes
        # and index again
        db_cursor.execute("DELETE FROM files")
        db_connection.commit()

        for root_dir in sdcard_paths:

            if root_dir is None:
                break

            for path, dirs, files in os.walk(root_dir):
                for folder in dirs:
                    if folder.startswith(tuple(exclude_folders)) or folder == "Android":
                        print(folder)
                        dirs.remove(folder)

                for fname in files:

                    for ext in extensions:
                        if ext in get_extensions('document_extensions'):
                            file_type = "document"
                        elif ext in get_extensions('audio_extensions'):
                            file_type = "audio"
                        elif ext in get_extensions('video_extensions'):
                            file_type = "video"
                        elif ext in get_extensions('image_extensions'):
                            file_type = "image"

                        if fname.endswith(tuple(ext)):
                             query = "INSERT INTO files (file_name, file_path, file_type) VALUES (%s, %s, %s)" % (repr(fname), repr(os.path.join(path, fname)), repr(file_type))
                             try:
                                 db_cursor.execute(query)
                             except Exception as e:
                                 print(e)

            db_connection.commit()

        print("Next Indexing will beging in the next 30 minutes")
        sleep(1800)
