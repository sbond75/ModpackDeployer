#Wrapper around importing Tkinter

# https://stackoverflow.com/questions/25905540/importerror-no-module-named-tkinter
try:
    # for Python2
    import Tkinter as tk   ## notice capitalized T in Tkinter
    import tkFileDialog
    import tkMessageBox
except ImportError:
    # for Python3
    import tkinter as tk   ## notice lowercase 't' in tkinter here
    import tkinter.filedialog as tkFileDialog # https://stackoverflow.com/questions/28590669/tkinter-tkfiledialog-doesnt-exist
    import tkinter.messagebox as tkMessageBox # https://pythonspot.com/tk-message-box/
