#source .venvPyToExe/Scripts/activate
pyinstaller --collect-all requests updater.py
cd dist
os="$(python -c 'import sys; print(sys.platform)')"
modpackName="$(python -c 'import deploy_config; print(deploy_config.modpackName)')"
updaterZip="../${modpackName}Updater.zip"
if [ "$os" == "win32" ]; then
    7z a "$updaterZip" updater
else
    zip "$updaterZip" updater
fi

modpackZipfileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileName)')"
modpackZipfileSha256HashFileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileSha256HashFileName)')"

source build_updater_config.sh
scp -p "$modpackZipfileName" "$modpackZipfileSha256HashFileName" "$scpDestination"
scp -p "$updaterZip" "$scpDestination"
