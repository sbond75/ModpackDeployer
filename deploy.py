import RabUtils
import shutil
import os
import subprocess
import zipextended.zipextended.zipfileextended as zipfile #import zipfile #import ruamel.std.zipfile as zipfile # https://pypi.org/project/ruamel.std.zipfile/                                      #import zipfile
import time
import hashlib # https://docs.python.org/2/library/md5.html [<--deprecated] -> https://docs.python.org/2/library/hashlib.html#module-hashlib
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
sys.stdout = Unbuffered(sys.stdout)
sys.stderr = Unbuffered(sys.stderr)
# #

########################functions - specialized for this script########################

def copy(src, dest, symlinks=True):
    RabUtils.copy(src, dest, symlinks)

def copy_update(src, dest, symlinks=False):
    RabUtils.copy_update(src, dest, symlinks)

modpackZipfileName = deploy_config.modpackZipfileName
modpackZipfileSha256HashFileName = deploy_config.modpackZipfileSha256HashFileName
def openModpackZipfile():
    #print(dir(zipfile))
   try:
      return zipfile.ZipFileExtended(modpackZipfileName, 'a', zipfile.ZIP_DEFLATED) #zipfile.ZipFile(modpackZipfileName, 'a', zipfile.ZIP_DEFLATED) #<"Open a ZIP file, where file can be either a path to a file (a string) or a file-like object. The mode parameter should be 'r' to read an existing file, 'w' to truncate and write a new file, or 'a' to append to an existing file. If mode is 'a' and file refers to an existing ZIP file, then additional files are added to it. If file does not refer to a ZIP file, then a new ZIP archive is appended to the file. This is meant for adding a ZIP archive to another file (such as python.exe)." ( https://docs.python.org/2/library/zipfile.html#zipfile-objects )
   except FileNotFoundError:
      # https://stackoverflow.com/questions/1158076/implement-touch-using-python #
      from pathlib import Path
      Path(modpackZipfileName).touch()
      # #
      return zipfile.ZipFileExtended(modpackZipfileName, 'w', zipfile.ZIP_DEFLATED)

#(Optional) base_arcname: the base folder name to use in the archive for all files in the directory made relative to it.
    #^When setting the path to write to in the archive, this base_arcname will simply be inserted before whatever the path to a file in the provided path(argument 1) is.
def zipdir(path, ziph, base_arcname=None, zipfileName=modpackZipfileName, openZipfileFunc=openModpackZipfile):
    RabUtils.zipdir_update(path, ziph, zipfileName, openZipfileFunc, base_arcname, followlinks=True)

########################main########################

####zip + deploy the Client####
print("--Zip and deploy the Client")
#constants
clientDirectory = "./Client"
clientModsDirectory = clientDirectory + "/mods"
# #

with RabUtils.cd(clientDirectory):
    #(we are in the value contained in "clientDirectory")
    
    #update the current archive (to make an archive for the first time, make and export a MultiMC minecraft instance)#
    zipf_dotMCDirectory = ".minecraft"
    zipf_dotMCDirectory_length = len(zipf_dotMCDirectory)
    zipf_modsDirectory = zipf_dotMCDirectory + "/mods"
    zipf_configDirectory = zipf_dotMCDirectory + "/config"
    zipf = openModpackZipfile()
    
    #testing#
    #[WORKS!!!:] print(zipf.fp.read()) # https://docs.python.org/3/library/io.html#io.BufferedRandom  #io.BufferedIOBase.read(): "Read and return up to size bytes. If the argument is omitted, None, or negative, data is read and returned until EOF is reached. An empty bytes object is returned if the stream is already at EOF." ( https://docs.python.org/3/library/io.html#io.BufferedIOBase )   #print(zipf.fp.read(zipf.fp.BufferedReader.buffer_size)) #print(zipf.fp.readall())#print(zipf.fp.__class__.__name__)
    #exit()
    # #
    
    filesToDeleteFromTheZipfile = []
    #try:
    allFilesAndFolders = zipf.infolist()         #zipf.getinfo(zipf_modsDirectory) #<"Return a ZipInfo object with information about the archive member name. Calling getinfo() for a name not currently contained in the archive will raise a KeyError." ( https://docs.python.org/2/library/zipfile.html#zipfile.ZipFile.getinfo )
    for info in allFilesAndFolders:
        #print(info.filename) #prints something like: ModpackNameHere/.minecraft/mods/x.jar
        if info.filename.startswith(zipf_dotMCDirectory):
            if info.filename.startswith("/mods", zipf_dotMCDirectory_length): #(<begins the search at this ("zipf_dotMCDirectory_length"'s) position)
                #(then we found an existing mod or subfolder inside the mods folder)
                fileOrFolderName = info.filename[zipf_dotMCDirectory_length+1:] #substring from zipf_dotMCDirectory_length to the end of the string. this should give us something like "mods/x.jar"
                #print(fileOrFolderName)
                """if os.path.isfile(fileOrFolderName): #if we have a mod in our Client folder that is in this zip file already, verify the date modified - make sure it is the same as the existing file:
                    date_time = time.mktime(info.date_time + (0, 0, -1)) # https://stackoverflow.com/questions/9813243/extract-files-from-zip-file-and-retain-mod-date-python-2-7-1-on-windows-7
                    if date_time < os.path.getmtime(fileOrFolderName): #then we have an outdated file in the zip to replace
                        zipf.write(fileOrFolderName, info.filename)
                elif not os.path.isdir(fileOrFolderName): #then the mod exists in the archive, but doesn't exist in the modpack files in the "clientModsDirectory" - so we will remove that mod!
                    print("[Note] \"" + info.filename + "\" exists in the archive, but doesn't exist in the modpack files in \"" + clientModsDirectory + "\" - so it will be deleted.")
                    filesToDeleteFromTheZipfile.append(info.filename)"""
                if not os.path.exists(fileOrFolderName): #then the mod exists in the archive, but doesn't exist in the modpack files in the "clientModsDirectory" - so we will remove that mod!
                    print("[Note] \"" + info.filename + "\" exists in the archive, but doesn't exist in the modpack files in \"" + clientModsDirectory + "\" - so it will be deleted.")
                    filesToDeleteFromTheZipfile.append(info.filename)
            #elif info.filename.startsWith("/config", beg=zipf_dotMCDirectory_length):
                #(then we found an existing config or subfolder inside the config folder)
    #except KeyError:
        #do nothing
    if not len(filesToDeleteFromTheZipfile) == 0:
        #zipf.close()
        #zipfile.delete_from_zip_file(modpackZipfileName, pattern=None, file_names=filesToDeleteFromTheZipfile) #TODO: delete_from_zip_file is still not as fast as winrar.. it seems to have to rebuild the entire archive and recompress EVERYTHING (<zipfile.writestr does that i heard on stack overflow) (7zip is probably faster than winrar even!)
        for x in filesToDeleteFromTheZipfile:
            zipf.remove(x)
        #zipf = openModpackZipfile()

    #now, add the mods, configs, resource packs, and miscellaneous MultiMC-related files into the zip
    zipdir("mods", zipf, zipf_dotMCDirectory)#, zipf_modsDirectory)
    zipdir("config", zipf, zipf_dotMCDirectory)#, zipf_configDirectory)
    zipdir("resourcepacks", zipf, zipf_dotMCDirectory)
    zipdir("shaderpacks", zipf, zipf_dotMCDirectory)
    with RabUtils.cd("Modpack - MultiMC Instance"):
       zipdir(".packignore", zipf)
       zipdir("instance.cfg", zipf)
       zipdir("mmc-pack.json", zipf)
    
    zipf.close()
    #save sha256 hash#
    with open(modpackZipfileSha256HashFileName, 'w') as f:
        f.write(RabUtils.computeSha256ForFile(modpackZipfileName))
    # #
    # #
####           ####

#### Upload the Client ####
#sftp deploy_config.username + "@" + deploy_config.ip + ":" + 
####                   ####

####copy from Client to Server####
print("--Copy from Client to Server")
#constants#
serverDirectory = "./Server"
serverModsDirectory = serverDirectory + "/mods"
serverOnly = "Server Only"
client_serverOnlyDirectory = clientModsDirectory + "/" + serverOnly
modsOnlyInClient = ["ArmorStatusHUD", "InventoryTweaks", "Neat", "Sound-Physics"]
# #

#[NVM] delete Server's mods so we start fresh
#if os.path.isdir(serverModsDirectory):
#    shutil.rmtree(serverModsDirectory)
#    os.mkdir(serverModsDirectory)

for fileOrFolderName in os.listdir(clientModsDirectory):
    curF = clientModsDirectory + "/" + fileOrFolderName #(curF = current file or folder)
    isdir = os.path.isdir(curF)
    
    #check if this is a client-only mod (aka, a member of "modsOnlyInClient")
    if any(filenamePart in fileOrFolderName for filenamePart in modsOnlyInClient):
        continue;
    #check if we found a server-only mod folder
    if isdir and serverOnly in fileOrFolderName:
        #copy all in "Server Only" to the Server
        copy_update(src=client_serverOnlyDirectory, dest=serverModsDirectory)
        continue #dont copy it below this copy

    #if isdir: print(curF)
    copy_update(src=curF, dest=serverModsDirectory + "/" + fileOrFolderName)

# Check for a mod in the server but not in client_serverOnlyDirectory and not in clientModsDirectory
for fileOrFolderName in os.listdir(serverModsDirectory):
    curF = serverModsDirectory + "/" + fileOrFolderName #(curF = current file or folder)
    if not os.path.exists(os.path.join(clientModsDirectory, fileOrFolderName)) and not os.path.exists(os.path.join(client_serverOnlyDirectory, fileOrFolderName)):
        print("[Note] Deleting", curF)
        if os.path.isdir(curF):
            shutil.rmtree(curF)
        else:
            os.remove(curF)
####                          ####

print("--Done")
