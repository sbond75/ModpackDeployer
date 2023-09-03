#Tkinter Utils

from RabTkWrapper import * #(need to do it with this "from" and "*", otherwise what the module imports is not imported into THIS script that is doing the importing. ( https://stackoverflow.com/questions/28794859/python-import-modules-in-another-file ))

def clearTextWidget(textwidget):
    textwidget.delete('1.0', tk.END) #clears the textbox.. wow. ( https://python-forum.io/Thread-How-to-delete-text-from-a-tkinter-Text-widget , https://stackoverflow.com/questions/27966626/how-to-clear-delete-the-contents-of-a-tkinter-text-widget )

def clearEntryWidget(entrywidget):
    entrywidget.delete(0, 'end')

