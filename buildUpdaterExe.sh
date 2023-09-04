if [ ! -z "$1" ]; then
    # Enter into the venv path provided in $1
    source "$1/Scripts/activate"
fi
pyinstaller --collect-all requests updater.py

modpackName="$(python -c 'import deploy_config; print(deploy_config.modpackName)')"

cd dist
os="$(python -c 'import sys; print(sys.platform)')"
updaterZip="../${modpackName}Updater.zip"
if [ "$os" == "win32" ]; then
    7z a "$updaterZip" updater
else
    zip "$updaterZip" updater
fi

cd ..
modpackZipfileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileName)')"
modpackZipfileSha256HashFileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileSha256HashFileName)')"

source build_updater_config.sh
scp -p "$modpackZipfileName" "$modpackZipfileSha256HashFileName" "$scpDestination"
scp -p "$updaterZip" "$scpDestination"
