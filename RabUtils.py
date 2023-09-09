import shutil
import os
#import ruamel.std.zipfile as zipfile # https://pypi.org/project/ruamel.std.zipfile/                                      #import zipfile
import time
import errno
import posixpath
import hashlib
import sys

########################functions - general utilities - file system########################

# https://stackoverflow.com/questions/431684/how-do-i-change-directory-cd-in-python/13197763#13197763
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def copy_nosymlinks(src, dst, keepmetadata=True):
    if keepmetadata:
        shutil.copy2(src,dst)
    else:
        shutil.copy(src,dst)

# https://stackoverflow.com/questions/4847615/copying-a-symbolic-link-in-python
def copy_keepsymlinks(src, dst, keepmetadata=True):
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
    else:
        if keepmetadata:
            shutil.copy2(src,dst)
        else:
            shutil.copy(src,dst)

# https://stackoverflow.com/questions/7419665/python-move-and-overwrite-files-and-folders #
#original:
"""def forceMergeFlatDir(srcDir, dstDir):
    if not os.path.exists(dstDir):
        os.makedirs(dstDir)
    for item in os.listdir(srcDir):
        srcFile = os.path.join(srcDir, item)
        dstFile = os.path.join(dstDir, item)
        forceCopyFile(srcFile, dstFile)

def forceCopyFile (sfile, dfile):
    if os.path.isfile(sfile):
        shutil.copy2(sfile, dfile)

def isAFlatDir(sDir):
    for item in os.listdir(sDir):
        sItem = os.path.join(sDir, item)
        if os.path.isdir(sItem):
            return False
    return True


def copyTree(src, dst):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            if not os.path.exists(dst):
                os.makedirs(dst)
            forceCopyFile(s,d)
        if os.path.isdir(s):
            isRecursive = not isAFlatDir(s)
            if isRecursive:
                copyTree(s, d)
            else:
                forceMergeFlatDir(s, d)"""

"""def forceMergeFlatDir(srcDir, dstDir, symlinks):
    if not os.path.exists(dstDir):
        os.makedirs(dstDir)
    for item in os.listdir(srcDir):
        srcFile = os.path.join(srcDir, item)
        dstFile = os.path.join(dstDir, item)
        if os.path.isfile(srcFile) or (symlinks and os.path.islink(srcFile)):
            print("copy " + srcFile)
            forceCopyFile(srcFile, dstFile)

def forceCopyFile (sfile, dfile, symlinks):
    if symlinks:
        copy_keepsymlinks(sfile, dfile, keepmetadata=True)
    else:
        copy_nosymlinks(sfile, dfile, keepmetadata=True)

def isAFlatDir(sDir):
    for item in os.listdir(sDir):
        sItem = os.path.join(sDir, item)
        if os.path.isdir(sItem):
            return False
    return True

#a version of shutil.copytree() that doesnt error if the detination directory exists!
def copytree(src, dst, symlinks=False):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s) or (symlinks and os.path.islink(s)):
            if not os.path.exists(dst):
                os.makedirs(dst)
            forceCopyFile(s,d,symlinks)
        elif os.path.isdir(s):
            isRecursive = not isAFlatDir(s)
            if isRecursive:
                copytree(s, d, symlinks)
            else:
                forceMergeFlatDir(s, d, symlinks)"""
#^nvm, doesnt work.. [OH... does work maybe , it was jus tthat i did it wrong in my OWN code that was passing dest as NOT including folders from the path in "src".. wow.]

##

#(made by me)
#returns True if the file at file1path is older than the file at file2path.
def isFileOlder(file1path, file2path):
    return os.path.getmtime(file1path) < os.path.getmtime(file2path)

#my own function to "update" a directory, via comparing modified times of files from src folder to dest folder (provided as paths) OR can provide src and dest as FILES.
#symlinks: whether to follow symbolic links.
def copy_update(src, dest, symlinks=False):
    #find out if "src" exists
    if not os.path.exists(src):
        raise Exception('Source path "' + src + '" does not exist.')

    #find out if "src" is a file, and if so, update it and be done
    if os.path.isfile(src):
        #make sure dest is a file. if it is a dir or symlink, delete it [nvm, what if a file has the same name as a folder.. that should be ok!..]
        #if os.path.isdir(dest) or os.path.islink(dest):
        #    shutil.rmtree(dest)
        #copy src to dest
        try:
            if isFileOlder(dest, src): #if destination file is older, replace it
                copy(src, dest, symlinks)
        except OSError as e:
            #the file in src might not exist in dest, so copy it anyway
            copy(src, dest, symlinks)
        return
    
    #at this point, we know src is a folder.
    #first, scan the dest folder and compare what it has to the src folder, updating files that are out of date and also seeing if any files are in dest that are NOT in src. if any, delete them.
    for root, dirs, files in os.walk(top=dest, followlinks=symlinks):
        for file in files:
            fsrc = os.path.join(src, file)
            fdest = os.path.join(root, file)
            try:
                if isFileOlder(fdest, fsrc): #if destination file is older, replace it
                    copy(fsrc, fdest, symlinks)
            except OSError as e:
                #print('Error updating "' + fdest + '" with "' + fsrc + '": %s' % e)
                #a file in dest might not exist in src. so, delete the file from dest:
                if not os.path.isfile(fdest):
                    try:
                        os.remove(fdest)
                    except OSError as e:
                        print('Error deleting "' + dest + '": %s' % e)
    
    #now, we need to copy everything over from src to dest by scanning src, skipping copying existing files in dst to dst from src.
    try:
        os.makedirs(dest)
    except OSError:
        pass
    for root, dirs, files in os.walk(top=src, followlinks=symlinks):
        for file in files:
            fsrc = os.path.join(root, file)
            fdest = os.path.join(dest, file)
            if not os.path.isfile(fdest): #TODO: what if we have a file that is the same name as a folder?!
                copy(fsrc, fdest, symlinks)

# https://www.pythoncentral.io/how-to-recursively-copy-a-directory-folder-in-python/
#symlinks: whether to follow symbolic links.
def copy(src, dest, symlinks=False):
    try:
        #copytree(src, dest, symlinks)
        shutil.copytree(src, dest, symlinks)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            if symlinks:
                copy_keepsymlinks(src, dest)
            else:
                copy_nosymlinks(src, dest)
        else:
            print('Directory not copied. Error: %s' % e)
    """except NotADirectoryError:
        #same as above - copy the file because it isnt a directory
        if symlinks:
            copy_keepsymlinks(src, dest)
        else:
            copy_nosymlinks(src, dest)"""

#alternative to os.path.join; uses unix rules - forward slashes instead of backslashes
def unixPathJoin(pathBeginning, pathAddon):
    #doesnt work for some reason!:#
    #pathBeginning_ = pathBeginning.replace('/', os.path.sep)
    #pathAddon_ = pathAddon.replace('/', os.path.sep)
    #path_ = os.path.join(pathBeginning_, pathAddon_)
    #print("->" + path_)
    #path_ = path_.replace(os.path.sep, '/')
    # #

    pathBeginning_ = pathBeginning.replace(os.path.sep, '/')
    pathAddon_ = pathAddon.replace(os.path.sep, '/')
    path_ = posixpath.join(pathBeginning_, pathAddon_)
    return path_;

def convertToUnixPathAndNormalize(path):
    #arcname = posixpath.normpath(os.path.normpath(arcname)) #if we don't do this, we end up with paths such as "mods\\\\x.jar"
    # https://mail.python.org/pipermail/tutor/2011-July/084788.html
    path_ = path.replace(os.path.sep, '/')
    path_ = posixpath.normpath(path_)
    return path_

def removeLeadingSlashes(path):
    path_ = trimFromBeginning(path, '/')
    if os.path.sep == '\\':
        path_ = trimFromBeginning(path_, os.path.sep) #fixes {*}
    return path_

def removeTrailingSlashes(path):
    path_ = trimFromEnd(path, '/')
    if os.path.sep == '\\':
        path_ = trimFromEnd(path_, os.path.sep) #fixes {*}
    return path_

def directoryHasEventualParent(path
                               , inAnyOf # list which will be used to
                                         # check which, if any, paths
                                         # are parents of `path`. If a
                                         # path in this list is a
                                         # parent of `path`, the path
                                         # from the list will be
                                         # returned. Otherwise, None
                                         # will be returned.
                               ):
    inAnyOf = [convertToUnixPathAndNormalize(x) for x in inAnyOf]
    path = convertToUnixPathAndNormalize(path)
    path = path + '/' if not path.endswith('/') else path # to fix `RabUtils.directoryHasEventualParent('C:/asd/', ['C:/'])` not working (should return `C:/` but it returns None)
    inAnyOf = [x + '/' if not x.endswith('/') else x for x in inAnyOf] # to fix `RabUtils.directoryHasEventualParent('C:/asd/', ['C:/'])` not working (should return `C:/` but it returns None)
    # print(path)
    # print(inAnyOf)
    
    # Based on https://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
    # os.path.commonpath(paths) : "Return the longest common sub-path of each pathname in the sequence paths. Raise ValueError if paths contain both absolute and relative pathnames, the paths are on the different drives or if paths is empty. Unlike commonprefix(), this returns a valid path." ( https://docs.python.org/3/library/os.path.html )
    try:
        common = None
        for x in inAnyOf:
            common = os.path.commonpath([path, x])
            if isinstance(common, str):
                common = convertToUnixPathAndNormalize(common)
                common = common + '/' if not common.endswith('/') else common
                if common in inAnyOf:
                    return common
    except ValueError:
        return None
    # print(common)
    # print(inAnyOf)
    # if common in inAnyOf:
    #     return common
    return None

#makes directories as needed in order to provide a space for the given file path
def prepareDirectories(filePath):
    fileDir = os.path.dirname(filePath)
    # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    if not os.path.exists(fileDir):
        os.makedirs(fileDir)
        # try:
        #     os.makedirs(fileDir)
        # except OSError as exc: # Guard against race condition
        #     if exc.errno != errno.EEXIST:
        #         raise

# Warning: not using this since md5 is crackable/breakable
def computeMD5ForFile(filepath):
    with open(filepath, 'rb') as content_file:
        content = content_file.read() # https://stackoverflow.com/questions/7409780/reading-entire-file-in-python
        return hashlib.md5(content).hexdigest() #[works, matches winmd5's hash of the modpack zip]  #WOW!! this is WAY faster than winmd5! this takes like 1.5 seconds, while winmd5 takes 7 seconds or so.

def computeSha256ForFile(filepath):
    with open(filepath, 'rb') as content_file:
        content = content_file.read() # https://stackoverflow.com/questions/7409780/reading-entire-file-in-python
        return hashlib.sha256(content).hexdigest()

# https://stackoverflow.com/questions/9181859/getting-percentage-complete-of-an-md5-checksum
# def computeMD5ForFile(filepath):
#     def digest_with_progress(filename, chunk_size):
#         read_size = 0
#         last_percent_done = 0
#         digest = hashlib.md5()
#         total_size = os.path.getsize(filename)

#         data = True
#         f = open(filename)
#         while data:
#             # Read and update digest.
#             data = f.read(chunk_size)
#             read_size += len(data)
#             digest.update(data)

#             # Calculate progress.
#             percent_done = 100 * read_size / total_size
#             if percent_done > last_percent_done:
#                 print '%d%% done' % percent_done
#                 last_percent_done = percent_done
#         f.close()
#         return digest.hexdigest()
#     return digest_with_progress(filepath, #NOTE: different chunk_size could cause wrong hash to be computed....

########################Functions - general utilities - zip archives########################

#converts the time in a zipfile zipinfo object into "time in seconds since the epoch as a floating point number"
def zipfileInfoTimeToUnixTime(zipinfoObjectFromArchive):
    return time.mktime(zipinfoObjectFromArchive.date_time + (0, 0, -1))

#(made by me)
#(convenience function)
def isFileInArchiveOlder_c(filepath, zipinfoObjectFromArchive):
    # import code
    # code.InteractiveConsole(locals=locals()).interact()
    return os.path.getmtime(filepath) - zipfileInfoTimeToUnixTime(zipinfoObjectFromArchive) > 2
    #^ time.mktime() is like time.time() because it returns "the time in seconds since the epoch as a floating point number" ( https://docs.python.org/2/library/time.html#time.time )

def isFileInArchiveNewer_c(filepath, zipinfoObjectFromArchive):
    # import code
    # code.InteractiveConsole(locals=locals()).interact()
    diff = zipfileInfoTimeToUnixTime(zipinfoObjectFromArchive) - os.path.getmtime(filepath)
    return diff > 2, diff

#(made by me)
#note from https://en.wikipedia.org/wiki/Zip_(file_format) :
    #"The FAT filesystem of DOS has a timestamp resolution of only two seconds; ZIP file records mimic this.
    #As a result, the built-in timestamp resolution of files in a ZIP archive is only two seconds, though extra fields can be used to store more precise timestamps.
    #The ZIP format has no notion of time zone, so timestamps are only meaningful if it is known what time zone they were created in."
def isFileInArchiveOlder(file_mtime, fileInArchive_mtime):
    return file_mtime - fileInArchive_mtime > 2

# https://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory
#demo:
"""
if __name__ == '__main__':
    zipf = zipfile.ZipFile('Python.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir('tmp/', zipf)
    zipf.close()
"""
#(Optional) base_arcname: the base folder name to use in the archive for all files in the directory made relative to it.
    #^When setting the path to write to in the archive, this base_arcname will simply be inserted before whatever the path to a file in the provided path(argument 1) is.
    #( https://docs.python.org/2/library/zipfile.html#zipfile.ZipFile.write )
#NOTE: doesn't check if destination files exist! if you want to do this and avoid duplicate file names in the zip file, use the alternative for this function: zipdir_update()
#followlinks: "By default, walk() will not walk down into symbolic links that resolve to directories. Set followlinks to True to visit directories pointed to by symlinks, on systems that support them." ( https://docs.python.org/2/library/os.html )
#NOTE: this uses os.walk, which MAY NOT SUPPORT (im not sure) using change directory (os.chdir(), or the cd class in Rabutils)
def zipdir(path, ziph, base_arcname=None, followlinks=False):
    # ziph is zipfile handle
    if base_arcname is None:
        for root, dirs, files in os.walk(top=path, followlinks=followlinks): #os.walk(path):
            for file in files:
                ziph.write(os.path.join(root, file))
    else:
        for root, dirs, files in os.walk(top=path, followlinks=followlinks):
            for file in files:
                fname = os.path.join(root, file)
                arcname = os.path.join(base_arcname, fname)
                ziph.write(fname, arcname)

#path: path on hard drive to use to update the zip file's contents
#followlinks: "By default, walk() will not walk down into symbolic links that resolve to directories. Set followlinks to True to visit directories pointed to by symlinks, on systems that support them." ( https://docs.python.org/2/library/os.html )
#ziph: zipfile object ("h" stands for handle..)
#zipfileName: file name for the zip file itself
#openZipfileFunc: a function that can reopen the zip file how you want it, and returns a ZipFile object (usually use what you did initially to open the zip file, but pass that as in a function)
#base_arcname: location in zip file to update
#NOTE: this uses os.walk, which MAY NOT SUPPORT (im not sure) using change directory (os.chdir(), or the cd class in Rabutils)
def zipdir_update(path, ziph, zipfileName, openZipfileFunc, base_arcname=None, followlinks=False):
    # ziph is zipfile handle
    filesToReplaceFromZipfile = [];
    filesToReplaceFromZipfile_correspondingFileOnDisk = [];
    
    def proc(root, file):
        fname = os.path.join(root, file)
        if base_arcname is not None:
            arcname = os.path.join(base_arcname, fname)
            arcname = convertToUnixPathAndNormalize(arcname)
        else:
            arcname = convertToUnixPathAndNormalize(fname)
        fname = convertToUnixPathAndNormalize(fname)
        try:
            # print("1: ")
            # import code
            # code.InteractiveConsole(locals=locals()).interact()

            info = ziph.getinfo(arcname)
            #file exists if we get this far. verify the date modified of the file on the disk - make sure it is the same as the existing file in the archive:
            #date_time = time.mktime(info.date_time + (0, 0, -1)) # https://stackoverflow.com/questions/9813243/extract-files-from-zip-file-and-retain-mod-date-python-2-7-1-on-windows-7
            if isFileInArchiveOlder_c(fname, info): #if date_time < os.path.getmtime(fname): #then we have an outdated file in the zip to replace        #AH HA!!!! i see!: "The FAT filesystem of DOS has a timestamp resolution of only two seconds; ZIP file records mimic this. As a result, the built-in timestamp resolution of files in a ZIP archive is only two seconds, though extra fields can be used to store more precise timestamps. The ZIP format has no notion of time zone, so timestamps are only meaningful if it is known what time zone they were created in." ( https://en.wikipedia.org/wiki/Zip_(file_format) ) ---THAT IS WHY the comparisons are off by 0.5, or 1, or so!! we need to be within 2 seconds of leeway only! ha!!
                #print(date_time)
                #print(os.path.getmtime(fname))
                print("Replacing older file in zip:", fname)
                filesToReplaceFromZipfile.append(info.filename)
                filesToReplaceFromZipfile_correspondingFileOnDisk.append(fname)
        except KeyError as e: #then the file doesnt exist, so just write it
            print("Adding new file to zip as", arcname, ":", fname)
            # print("KeyError: "); print(e)
            # import code
            # code.InteractiveConsole(locals=locals()).interact()
            if base_arcname is None:
                ziph.write(fname)
            else:
                ziph.write(fname, arcname)

    # Handle just a file
    if os.path.isfile(path):
        proc(os.path.dirname(path), os.path.basename(path))
    else:
        # Handle directory
        for root, dirs, files in os.walk(top=path, followlinks=followlinks):
            for file in files:
                proc(root, file)
    
    #delete all filesToReplaceFromZipfile from the zip file
    # print("2: ")
    # import code
    # code.InteractiveConsole(locals=locals()).interact()
    if not len(filesToReplaceFromZipfile) == 0:
        #ziph.close()
        ##zipfile.delete_from_zip_file(zipfileName, pattern=None, file_names=filesToReplaceFromZipfile) #TODO: delete_from_zip_file is still not as fast as winrar.. it seems to have to rebuild the entire archive and recompress EVERYTHING (<zipfile.writestr does that i heard on stack overflow) (7zip is probably faster than winrar even!)
        #ziph = openZipfileFunc()

        for x in filesToReplaceFromZipfile:
            ziph.remove(x)
    #add all filesToReplaceFromZipfile to the zip file
    for i in range(len(filesToReplaceFromZipfile)):
        ziph.write(filesToReplaceFromZipfile_correspondingFileOnDisk[i], filesToReplaceFromZipfile[i])

def extractzipdir_update_defaultDeleteFile(pathToFile):
    try:
        os.remove(pathToFile)
    except OSError as e:
        print('Error deleting "' + pathToFile + '": %s' % e)
    
#path: path to extract to
#ziph: zipfile object ("h" stands for handle..)
#zipfilepath: folder to extract from the zip
#base_arcname: location in zip file to convert into being within the provided "path" argument as a root sort of directory
#followlinks: "By default, walk() will not walk down into symbolic links that resolve to directories. Set followlinks to True to visit directories pointed to by symlinks, on systems that support them." ( https://docs.python.org/2/library/os.html )
#onFileNeedsToBeDeletedFromDisk: a function to execute, given a path to a file as an argument, when a file needs to be deleted.
def extractzipdir_update(path, ziph, zipfilepath, base_arcname=None, followlinks=False, onFileNeedsToBeDeletedFromDisk=extractzipdir_update_defaultDeleteFile):
    base_arcname_ = trimFromBeginning(base_arcname, '/')
    
    # ziph is zipfile handle
    #remove files that are on disk but arent in the zipfile.. #TODO: ask user if want to delete special configs maybe they set up, or mods they added.
    for root, dirs, files in os.walk(top=path, followlinks=followlinks):
        for file in files:
            fname = os.path.join(root, file)
            if base_arcname is not None:
                # print(fname)
                # print(base_arcname_)
                arcname = trimFromBeginning(fname, path)
                arcname = removeLeadingSlashes(arcname)
                # print(": " + arcname)
                arcname = unixPathJoin(base_arcname_, arcname)
                # print(arcname)
                arcname = convertToUnixPathAndNormalize(arcname)
            try:
                # print(arcname)
                info = ziph.getinfo(arcname)
                #file exists in the archive if we get this far.
            except KeyError as e: #then the file doesnt exist in the archive, so remove it
                onFileNeedsToBeDeletedFromDisk(fname)
    
    #zf is zipfile handle
    def extract(zf, zipfileinfo, extractfname):
        #ziph.extract(zipfileinfo, extractpath)
        # https://stackoverflow.com/questions/44079913/renaming-the-extracted-file-from-zipfile
        prepareDirectories(extractfname)
        MAX_PATH = 260
        if sys.platform == 'win32' and len(extractfname) > MAX_PATH:
            raise Exception("Filename too long (is " + str(len(extractfname)) + " characters instead of the maximum of " + str(MAX_PATH) + "): " + str(extractfname))
        with open(extractfname, "wb") as f:  # open the output path for writing    # (NOTE: fails if path too long on windows and just says "No such file or directory"... yikes.. also shown on https://stackoverflow.com/questions/36219317/pathname-too-long-to-open )
            f.write(zf.read(zipfileinfo))  # save the contents of the file in it
        os.utime(extractfname, times=(os.stat(extractfname).st_atime, zipfileInfoTimeToUnixTime(zipfileinfo))) #use the same access time as is already in the file (atime), but change modified time (mtime) to the same as what was in the zipfile.  # https://stackoverflow.com/questions/11348953/how-can-i-set-the-last-modified-time-of-a-file-from-python
    
    #add new files if needed
    allFilesAndFolders = ziph.infolist()
    for info in allFilesAndFolders:
        #print("Checking", info.filename, "to see if it is contained in this path within the zip file:", zipfilepath)
        if info.filename.startswith(zipfilepath):
            arcfname = info.filename
            if base_arcname is not None:
                extractfname = os.path.join(path, trimFromBeginning(trimFromBeginning(arcfname, base_arcname_), '/'))
            else:
                extractfname = os.path.join(path, arcfname)
            #extractpath = os.path.dirname(extractfname) # https://docs.python.org/3/library/os.path.html#os.path.split : "os.path.split(path): Split the pathname path into a pair, (head, tail) where tail is the last pathname component and head is everything leading up to that. The tail part will never contain a slash; if path ends in a slash, tail will be empty. If there is no slash in path, head will be empty. If path is empty, both head and tail are empty. Trailing slashes are stripped from head unless it is the root (one or more slashes only). In all cases, join(head, tail) returns a path to the same location as path (but the strings may differ). Also see the functions dirname() and basename()."
            #print("Processing", extractfname)
            try:
                isNewer, diff = isFileInArchiveNewer_c(extractfname, info)
                if isNewer:
                    print("Extracting since the one on disk is older by", diff, "second(s):", extractfname)
                    extract(ziph, info, extractfname)
            except FileNotFoundError: #then the file doesnt exist, so just write it
                # import code
                # code.InteractiveConsole(locals=locals()).interact()
                print("Extracting since doesn't exist:", extractfname)
                extract(ziph, info, extractfname)
        # else:
        #     print("Doesn't start with", zipfilepath, ":", info.filename)

########################functions - general utilities - strings########################

#my own function to simplify "slicing" ( https://www.digitalocean.com/community/tutorials/how-to-index-and-slice-strings-in-python-3 ) a string.
#s: the string
#begin: the index of the first character to take out
#end: the index of the last character to take out up to. If is provided as None, will use len(s) (length of the provided string "s")
def substr(s, begin=0, end=None):
    if end is None:
        end = len(s)
    return s[begin:end]

# https://stackoverflow.com/questions/21498939/how-to-circumvent-the-fallacy-of-pythons-os-path-commonprefix
def commonprefix(l):
    # this unlike the os.path.commonprefix version
    # always returns path prefixes as it compares
    # path component wise
    cp = []
    ls = [p.split('/') for p in l]
    ml = min( len(p) for p in ls )

    for i in range(ml):

        s = set( p[i] for p in ls )         
        if len(s) != 1:
            break

        cp.append(s.pop())

    return '/'.join(cp)

def trimFromBeginning(string, textToTrim):
    if string.startswith(textToTrim): # https://stackoverflow.com/questions/599953/how-to-remove-the-left-part-of-a-string
        first, second = string.split(textToTrim, 1)
        return second
    return string

def trimFromEnd(string, textToTrim):
    if string.endswith(textToTrim):
        first, second = string.rsplit(textToTrim, 1)
        return second
    return string
