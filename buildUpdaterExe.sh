justDeployUpdater="$2" # Optionally set this argument to "1" to only deploy the updater, not the other zips.

if [ ! -z "$1" ]; then
    # Enter into the venv path provided in $1
    if [ -e "$1/Scripts/activate" ]; then
	source "$1/Scripts/activate"
    elif [ -e "$1/bin/activate" ]; then
	source "$1/bin/activate"
    else
	echo "\"activate\" script in virtualenv at $1 not found. Exiting."
	exit 1
    fi
fi
modpackName="$(python -c 'import deploy_config; print(deploy_config.modpackName)')"
name="$modpackName Modpack Updater"
# `--noconfirm`: "Replace output directory (default: SPECPATH/dist/SPECNAME) without asking for confirmation" ( https://pyinstaller.org/en/stable/usage.html#options )
pyinstaller --noconfirm "--name=$name" --windowed --collect-all requests updater.py

cd dist
os="$(python -c 'import sys; print(sys.platform)')"

if [ "$os" == "win32" ]; then # Windows
    updaterZip="../${modpackName}Updater.zip"
elif [ "$os" == "darwin" ]; then # macOS
    updaterZip="../${modpackName}Updater_macOS.zip"
else # assume Linux
    updaterZip="../${modpackName}Updater_Linux.zip"
fi

if [ "$os" == "win32" ]; then
    7z a "$updaterZip" "$name"
elif [ "$os" == "darwin" ]; then # macOS
    zip -r "$updaterZip" "${name}.app"
else # assume Linux
    zip -r "$updaterZip" updater
fi

cd ..
modpackZipfileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileName)')"
modpackZipfileSha256HashFileName="$(python -c 'import deploy_config; print(deploy_config.modpackZipfileSha256HashFileName)')"

source build_updater_config.sh
if [ "$justDeployUpdater" == "1" ]; then
    scp -p "dist/$updaterZip" "$scpDestination"
else
    scp -p "$modpackZipfileName" "$modpackZipfileSha256HashFileName" "dist/$updaterZip" "$scpDestination"
fi
