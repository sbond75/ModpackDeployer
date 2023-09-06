import RabUtils
import RabTkUtils
from RabTkWrapper import *
import shutil
import os
import subprocess
#import zipfile
import ruamel.std.zipfile as zipfile # https://pypi.org/project/ruamel.std.zipfile/                                      #import zipfile
import time
import requests
import io
import traceback
import sys
import updater_config
import deploy_config

# https://stackoverflow.com/questions/107705/disable-output-buffering #
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

import sys
if sys.stdout is not None:
   sys.stdout = Unbuffered(sys.stdout)
if sys.stderr is not None:
   sys.stderr = Unbuffered(sys.stderr)
# #

#ConfigParser import#
try:
    #python 2
    import ConfigParser as configparser
    ConfigParser = configparser.SafeConfigParser # https://stackoverflow.com/questions/840969/how-do-you-alias-a-python-class-to-have-another-name-without-using-inheritance
except ImportError:
    #python 3
    if sys.version_info[0] >= 3 and sys.version_info[1] >= 2: #python 3.2, where SafeConfigParser was renamed to ConfigParser.    # https://stackoverflow.com/questions/9079036/detect-python-version-at-runtime
        import configparser
        ConfigParser = configparser.ConfigParser
    else:
        import configparser
        ConfigParser = configparser.SafeConfigParser
# #

justUpdate = len(sys.argv) > 1 and sys.argv[1] == '--just-update'

# https://stackoverflow.com/questions/24942760/is-there-a-way-to-gray-out-disable-a-tkinter-frame #
def disableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ('Frame','Labelframe','TFrame','TLabelframe'):
            try:
                child.configure(state='disable')
            except tk.TclError: # `_tkinter.TclError: unknown option "-state"` is sometimes thrown on some UI elements
                pass
        else:
            disableChildren(child)

def enableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        #print (wtype)
        if wtype not in ('Frame','Labelframe','TFrame','TLabelframe'):
            try:
               child.configure(state='normal')
            except tk.TclError: # `_tkinter.TclError: unknown option "-state"` is sometimes thrown on some UI elements
               pass
        else:
            enableChildren(child)
# #

########################variables - arguments########################

g_multiMC_zipToDownload = updater_config.multiMC_zipToDownload
g_multiMC_zip_sha256sumToDownload = updater_config.multiMC_zip_sha256sumToDownload
g_errorText = "Error"
g_config = ConfigParser() #configparser.SafeConfigParser()
g_saveZip_filename = updater_config.saveZip_filename

#load config#
False_ = 0
True_ = 1
g_configfname = 'UpdaterConfig.ini' #'config.ini'
g_config.read(g_configfname)
g_config_values = dict()
g_config_values['multiMC_instanceDirectory'] = g_config.get('Main', 'multiMC_instanceDirectory', fallback="")
g_config_values['deleteFilesNotInModpackZip'] = g_config.get('Main', 'deleteFilesNotInModpackZip', fallback=True_)
g_config_values['saveZip'] = g_config.get('Main', 'saveZip', fallback=True_)
g_config_values['forceDownload'] = g_config.get('Main', 'forceDownload', fallback=False_)
# #
def saveConfig(app):
    #save config#
    if not g_config.has_section('Main'):
        g_config.add_section('Main')
    g_config.set('Main', 'multiMC_instanceDirectory', app.multiMC_instanceDirectory.get())
    g_config.set('Main', 'deleteFilesNotInModpackZip', str(app.deleteFilesNotInModpackZip.get()))
    g_config.set('Main', 'saveZip', str(app.saveZip.get()))
    g_config.set('Main', 'forceDownload', str(app.forceDownload.get()))

    with open(g_configfname, 'w') as f:
        g_config.write(f)
    # #

########################functions - specialized for this script########################

def copy(src, dest, symlinks=True):
    RabUtils.copy(src, dest, symlinks)

def copy_update(src, dest, symlinks=False):
    RabUtils.copy_update(src, dest, symlinks)

def extractzipdir_update(path, ziph, zipfilepath, base_arcname=None, followlinks=True, onFileNeedsToBeDeletedFromDisk='extractzipdir_update_deleteFile', whitelistNeverDelete=[]):
    def extractzipdir_update_deleteFile(pathToFile):
        # import code
        # code.InteractiveConsole(locals=locals()).interact()
       
        #print(pathToFile, RabUtils.convertToUnixPathAndNormalize(pathToFile), whitelistNeverDelete)
        if RabUtils.directoryHasEventualParent(pathToFile, inAnyOf=whitelistNeverDelete) is not None:
            return
        # import code
        # code.InteractiveConsole(locals=locals()).interact()

        result = tkMessageBox.askyesnocancel("Confirm Deletion", 'To update the modpack, the file "' + pathToFile + '" must be deleted.\n\nWould you like to delete it?', icon='warning')
        #print(result) # Note: is False for "No"
        if result == 'yes' or result == True:
            try:
                os.remove(pathToFile)
            except OSError as e:
                tkMessageBox.showinfo(g_errorText, 'Error deleting "' + pathToFile + '": %s' % e)
        elif result == 'cancel' or result is None:
            exit()
        #else:
            #print "I'm Not Deleted Yet"

    if onFileNeedsToBeDeletedFromDisk == 'extractzipdir_update_deleteFile':
       onFileNeedsToBeDeletedFromDisk = extractzipdir_update_deleteFile
    
    RabUtils.extractzipdir_update(path, ziph, zipfilepath, base_arcname, followlinks, onFileNeedsToBeDeletedFromDisk)

progressBar = None
progressLabel = None
pblength = 280
root = None
def progressReport(percentage):
    progressBar.grid() # Put it back so it isn't invisible anymore (i.e. after .grid_remove()) ( https://stackoverflow.com/questions/3819354/in-tkinter-is-there-any-way-to-make-a-widget-invisible )
    progressBar['value'] = pblength * percentage
    progressLabel.set(str(int(percentage * 100)) + '% complete') # https://stackoverflow.com/questions/2603169/update-tkinter-label-from-variable
    #root.update_idletasks()
    root.update()

#returns a pair consisting of: status message + True if succeeded, False if not.
def updateClient(multiMC_instanceDirectory, multiMC_zipToDownload, multiMC_zip_sha256sumToDownload, saveZip, forceDownload):
    #constants
    dotMCDirectory = RabUtils.convertToUnixPathAndNormalize(os.path.join(multiMC_instanceDirectory, ".minecraft"))
    modsDirectory = dotMCDirectory + "/mods"
    configDirectory = dotMCDirectory + "/config"
    resourcepacksDirectory = dotMCDirectory + "/resourcepacks"
    shaderpacksDirectory = dotMCDirectory + "/shaderpacks"

    zipf_modpackDirectory = "" #"ModpackNameHere/"
    zipf_dotMCDirectory = zipf_modpackDirectory + ".minecraft"
    zipf_dotMCDirectory_length = len(zipf_dotMCDirectory)
    zipf_modsDirectory = zipf_dotMCDirectory + "/mods"
    zipf_configDirectory = zipf_dotMCDirectory + "/config"
    zipf_resourcepacksDirectory = zipf_dotMCDirectory + "/resourcepacks"
    zipf_shaderpacksDirectory = zipf_dotMCDirectory + "/shaderpacks"
    # #

    print("Updating...")
    progressReport(0)
    if saveZip:
        print("Contacting server...")
        sha256sum = requests.get(multiMC_zip_sha256sumToDownload)
        print("Done contacting server.")
        if not forceDownload and os.path.isfile(g_saveZip_filename):
            if sha256sum.content == bytes(RabUtils.computeSha256ForFile(g_saveZip_filename), encoding='utf-8'):
                progressReport(1)
                return lambda: tkMessageBox.showinfo("Updater", "Already up to date"), True
    print("Getting zip file...")
    progressReport(0.025)
    result = requests.get(multiMC_zipToDownload, stream=True)
    progressReport(0.075)
    print("Done getting zip file.")
    print("Mods location:", modsDirectory)
    print("Config location:", configDirectory)
    if os.path.isdir(modsDirectory) and os.path.isdir(configDirectory):
        zipf = zipfile.ZipFile(io.BytesIO(result.content)) # https://stackoverflow.com/questions/9419162/download-returned-zip-file-from-url
        progressReport(0.09)
        allFilesAndFolders = zipf.infolist()
        """for info in allFilesAndFolders:
            #print(info.filename) #prints something like: ModpackNameHere/.minecraft/mods/x.jar
            if info.filename.startswith(zipf_dotMCDirectory):
                if info.filename.startswith("/mods", zipf_dotMCDirectory_length):
                    #[nvm] delete the user's existing mods
                    #copy in the mods
                    RabUtils.extractzipdir_update(
                elif info.filename.startsWith("/config", beg=zipf_dotMCDirectory_length):
                    #[nvm] delete existing configs
                    #copy in configs
                    """
        #update mods
        try:
            print("Extracting mods...")
            extractzipdir_update(modsDirectory, zipf, zipf_modsDirectory, base_arcname=zipf_modsDirectory, whitelistNeverDelete=[ os.path.join(modsDirectory, 'memory_repo'),
                                                                                                                                  os.path.join(modsDirectory, '1.12.2'),
                                                                                                                                  os.path.join(modsDirectory, 'OpenTerrainGenerator'),
                                                                                                                                  os.path.join(modsDirectory, 'Disabled'),
                                                                                                                                 ])
            progressReport(0.65)
            print("Extracted mods.")
        except (KeyboardInterrupt, SystemExit): # https://stackoverflow.com/questions/4990718/about-catching-any-exception -> http://effbot.org/zone/stupid-exceptions-keyboardinterrupt.htm
            raise
        except: #(catches all other errors besides the above)
            # report error and proceed
            t1 = sys.exc_info()[1]
            t2 = traceback.format_exc()
            return lambda: tkMessageBox.showerror(g_errorText, "Error while updating mods: " + str(t1) + "\n\nMore details:\n" + t2), False
            #https://stackoverflow.com/questions/8238360/how-to-save-traceback-sys-exc-info-values-in-a-variable :
            """
            sys.exc_info() returns a tuple with three values (type, value, traceback).

            1. Here type gets the exception type of the Exception being handled
            2. value is the arguments that are being passed to constructor of exception class
            3. traceback contains the stack information like where the exception occurred etc.

            For Example, In the following program

            try:

                a = 1/0

            except Exception,e:

                exc_tuple = sys.exc_info()
            Now If we print the tuple the values will be this.

            exc_tuple[0] value will be "ZeroDivisionError"
            exc_tuple[1] value will be "integer division or modulo by zero" (String passed as parameter to the exception class)
            exc_tuple[2] value will be "trackback object at (some memory address)"
            The above details can also be fetched by simply printing the exception in string format.

            print str(e)
            """
        #update configs
        try:
            print("Extracting configs...")
            extractzipdir_update(configDirectory, zipf, zipf_configDirectory, base_arcname=zipf_configDirectory, whitelistNeverDelete=[ configDirectory # currently, all config files are kept if new ones are added, since we try to keep the modpack minimal and otherwise use the defaults if possible
                                                                                                                                        ,
                                                                                                                                       ])
            progressReport(0.8)
            print("Extracted configs.")
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # report error and proceed
            t1 = sys.exc_info()[1]
            t2 = traceback.format_exc()
            return lambda: tkMessageBox.showerror(g_errorText, "Error while updating configs: " + str(t1) + "\n\nMore details:\n" + t2), False
        
        #update resource packs
        try:
            print("Extracting resource packs...")
            progressReport(0.86)
            extractzipdir_update(resourcepacksDirectory, zipf, zipf_resourcepacksDirectory, base_arcname=zipf_resourcepacksDirectory, whitelistNeverDelete=[ resourcepacksDirectory # currently, all config files are kept if new ones are added, since we try to keep the modpack minimal and otherwise use the defaults if possible
                                                                                                                                        ,
                                                                                                                                       ])
            print("Extracted resource packs.")
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # report error and proceed
            t1 = sys.exc_info()[1]
            t2 = traceback.format_exc()
            return lambda: tkMessageBox.showerror(g_errorText, "Error while updating resource packs: " + str(t1) + "\n\nMore details:\n" + t2), False

        #update shader packs
        try:
            print("Extracting shader packs...")
            progressReport(0.86)
            extractzipdir_update(shaderpacksDirectory, zipf, zipf_shaderpacksDirectory, base_arcname=zipf_shaderpacksDirectory, whitelistNeverDelete=[ shaderpacksDirectory # currently, all config files are kept if new ones are added, since we try to keep the modpack minimal and otherwise use the defaults if possible
                                                                                                                                        ,
                                                                                                                                       ])
            print("Extracted shader packs.")
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # report error and proceed
            t1 = sys.exc_info()[1]
            t2 = traceback.format_exc()
            return lambda: tkMessageBox.showerror(g_errorText, "Error while updating shader packs: " + str(t1) + "\n\nMore details:\n" + t2), False
        
        #(optional) save the zip file to reuse later
        if saveZip:
            print("Saving zip file to", g_saveZip_filename + "...")
            with open(g_saveZip_filename, 'wb') as f:
                f.write(result.content)
            print("Saved zip file to", g_saveZip_filename + ".")
        #finished with the zip, so close it
        zipf.close()
        
        if saveZip:
            # Verify contents
            print("Verifying zip file contents using known sha256", str(sha256sum.content) + "...")
            progressReport(0.9)
            res = RabUtils.computeSha256ForFile(g_saveZip_filename)
            if sha256sum.content != bytes(res, encoding='utf8'):
                return lambda: tkMessageBox.showerror(g_errorText, "sha256 doesn't match: " + str(sha256sum.content) + " and " + str(res)), False
            print("Verified zip file contents using known sha256", str(sha256sum.content) + ".")

        print("Done updating")
        progressReport(1)
        return lambda: "Done updating", True
    else: #not all folders are there. likely, the user did not install the multimc modpack
        return lambda: tkMessageBox.showerror(g_errorText, "The given MultiMC instance location does not appear to have a mods and/or config folder."), False #(previously had: tkMessageBox.showinfo (see https://pythonspot.com/tk-message-box/ for all))
        

# http://effbot.org/tkinterbook/tkinter-hello-again.htm
class App:
    master = None #the "Master Frame"
    multiMC_instanceDirectory = None
    multiMC_instanceDirectory_browse_displayName = "Location of the MultiMC instance for the modpack to update\nExample: C:/Users/.../mmc-stable-win32/MultiMC/instances/" + deploy_config.modpackName + "\n"
    multiMC_instanceDirectory_entry = None
    deleteFilesNotInModpackZip = None
    saveZip = None
    forceDownload = None
    
    def __init__(self, master):
        self.master = master
        master.title("Modpack Updater")
        frame = tk.Frame(master, padx=5, pady=5) # https://www.tutorialspoint.com/how-to-add-a-margin-to-a-tkinter-window
        frame.grid()

        #instance directory choosing area#
        groupBasic = tk.Frame(frame, padx=5, pady=5)
        groupBasic.grid(row=0, column=0, sticky="n")
        self.multiMC_instanceDirectory_label = tk.Label(groupBasic, text=self.multiMC_instanceDirectory_browse_displayName, justify=tk.LEFT, anchor="w") # https://stackoverflow.com/questions/31140590/how-to-line-left-justify-label-and-entry-boxes-in-tkinter-grid
        self.multiMC_instanceDirectory_label.grid(row=0, sticky='w')

        groupBasic2 = tk.Frame(groupBasic, padx=5, pady=0)
        groupBasic2.grid(row=1, column=0, sticky="nw")
        self.multiMC_instanceDirectory = tk.StringVar()
        self.multiMC_instanceDirectory.set(g_config_values['multiMC_instanceDirectory'])
        self.multiMC_instanceDirectory_entry = tk.Entry(groupBasic2, textvariable=self.multiMC_instanceDirectory, width=60)#, width=50)
        self.multiMC_instanceDirectory_entry.grid(row=1, column=0, sticky='w')
        self.multiMC_instanceDirectory_browseButton = tk.Button(groupBasic2, text="Browse", command=self.multiMC_instanceDirectory_browse)
        self.multiMC_instanceDirectory_browseButton.grid(row=1, column=1, padx=(10,0))
        # #

        group = tk.LabelFrame(frame, text="Advanced Options", padx=5, pady=5) #"Group" # http://effbot.org/tkinterbook/labelframe.htm
        group.grid(row=0, column=2)
        #group.pack(padx=10, pady=10)
        tk.Label(group, text="Advanced Options")

        wraplength = 350
        
        #delete files not in modpack zip choosing area#
        self.deleteFilesNotInModpackZip = tk.IntVar()
        self.deleteFilesNotInModpackZip.set(g_config_values['deleteFilesNotInModpackZip'])
        self.deleteFilesNotInModpackZip_checkbutton = tk.Checkbutton(group,
                                                                     text="Ask before deleting config files or mods that are in your MultiMC instance but not in the modpack archive being downloaded",
                                                                     variable=self.deleteFilesNotInModpackZip,
                                                                     justify=tk.LEFT,
                                                                     wraplength=wraplength,
                                                                     onvalue=1, offvalue=0)
        self.deleteFilesNotInModpackZip_checkbutton.grid(row=0, column=0)
        # #

        #save zip choosing area#
        self.saveZip = tk.IntVar()
        self.saveZip.set(g_config_values['saveZip'])
        self.saveZip_checkbutton = tk.Checkbutton(group,
                                                  text="Save the modpack zip file to the hard drive for future use (speeds up subsequent updates)",
                                                  variable=self.saveZip,
                                                  justify=tk.LEFT,
                                                  wraplength=wraplength,
                                                  onvalue=1, offvalue=0)
        self.saveZip_checkbutton.grid(row=1, column=0)
        # #

        # Force download area #
        self.forceDownload = tk.IntVar()
        self.forceDownload.set(g_config_values['forceDownload'])
        self.forceDownload_checkbutton = tk.Checkbutton(group,
                                                  text="Force download even if considered up-to-date",
                                                  variable=self.forceDownload,
                                                  justify=tk.LEFT,
                                                  wraplength=wraplength,
                                                  onvalue=1, offvalue=0)
        self.forceDownload_checkbutton.grid(row=2, column=0)
        # #
        
        #running update client area#
        self.updateClient_button = tk.Button(master, text="Update", command=self._updateClient)
        self.updateClient_button.grid(row=1, column=0, sticky="news") # https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
        # #

        # progress bar #
        # https://www.pythontutorial.net/tkinter/tkinter-progressbar/
        from tkinter import ttk
        pb = ttk.Progressbar(
           master,
           orient='horizontal',
           #mode='indeterminate',
           length=pblength
        )
        global progressLabel
        progressLabel = tk.StringVar()
        l = tk.Label(master, textvariable=progressLabel)
        l.grid(column=1, row=3)
        self.progressLabelLabel = l
        # place the progressbar
        pb.grid(column=0, row=3, sticky="news")#, columnspan=2, padx=10, pady=20)
        pb['value'] = 0
        pb.grid_remove() # hide
        global progressBar
        progressBar = pb
        # #
        
        # finally, pack the container in the root window
        #frame.pack(side="top", fill="x") # https://stackoverflow.com/questions/3931386/how-to-display-a-sequence-of-widgets-on-the-same-row

        if justUpdate:
           self._updateClient()
           exit()

    def multiMC_instanceDirectory_browse(self):
        multiMC_instanceDirectory = tkFileDialog.askdirectory(parent=self.master) #tkFileDialog.askdirectory(parent=self.master, mode='rb', title=multiMC_instanceDirectory_browse_displayName)
        self.multiMC_instanceDirectory.set(multiMC_instanceDirectory)

    def _updateClient(self):
        print(0)
        saveConfig(self)

        disableChildren(root)
        self.progressLabelLabel.configure(state='normal') # except for disabling progressLabel
        msg, status = updateClient(self.multiMC_instanceDirectory.get(), g_multiMC_zipToDownload, g_multiMC_zip_sha256sumToDownload, self.saveZip.get(), self.forceDownload.get())
        enableChildren(root)

        msg()

########################main########################

root = tk.Tk()

app = App(root)

root.mainloop()

if not justUpdate:
   saveConfig(app)

try:
    root.destroy()
except tk.TclError: #except:
    pass #it could have been destroyed already?: https://stackoverflow.com/questions/35686580/tclerror-cant-invoke-destroy-command-application-has-been-destroyed


####update the client####
