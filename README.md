# ModpackDeployer

Intended for Minecraft modpack creators to distribute custom modpacks for [MultiMC](https://multimc.org/), providing a deployable updater GUI powered by Python tkinter.

## Dependency installation

Using Python 3 (only 3.7 was tested):
1. Optionally use a virtualenv:
   - Windows: `python -m venv .venv` and then `.venv\Scripts\activate.bat`
   - macOS or Linux: `python3 -m venv .venv` and then `source .venv/bin/activate`
2. Install pip packages (use `pip3` instead of `pip` if on macOS or Linux):
   1. Install packages for deploy.py: `pip install ruamel.std.zipfile`
   2. Install packages for updater.py: `pip install pyinstaller requests`

## Usage

Be sure to run these commands within the virtualenv created in [Dependency installation](## Dependency installation) if you are using a virtualenv:
1. Clone this repo with submodules: `git clone --recursive https://github.com/sbond75/ModpackDeployer.git`, or run `git submodule update --init --recursive` within the repo root if already cloned.
2. Set the modpack name in `Client/Modpack - MultiMC Instance/instance.cfg` next to `name=`.
3. Add mods to `Client/mods`, configs to `Client/config`, resource packs to `Client/resourcepacks`, and/or shaders to `Client/shaderpacks`. If needed, you can add server-only mods to `Client/mods/Server Only` (create the directory).
4. Deploy the modpack to a zip file using `deploy.py`: first, copy `template/deploy_config.py` into the repo root directory first, then edit `deploy_config.py` as needed. Then you can run `python deploy.py` (use `python3` on macOS or Linux) to generate a zip file for the modpack and a sha256sum file.
5. Test the modpack updater using `updater.py`: first, copy `template/updater_config.py` into the repo root directory first, then edit `updater_config.py` as needed. Then you can run `python updater.py` (use `python3` on macOS or Linux) to see how the updater works:
   - Within the updater, you can set the path to the instance of the modpack within MultiMC. Users must add the zip to MultiMC first. The complete steps are under [Using a modpack](## Using a modpack). You can modify these steps according to where the modpack is hosted. `scp` can be used to copy the file to a remote server for hosting if needed, explained in the next step below.
6. To build an updater application and deploy it with `scp` to a server to be hosted, copy `template/build_updater_config.py` into the repo root directory first, then edit `build_updater_config.py` as needed. Then run `bash buildUpdaterExe.sh` (use `python3` on macOS or Linux). This requires 7zip to be installed on Windows, as it uses the `7z` command; on other operating systems, `zip` is used.

## Releasing a modpack

Be sure to run this command within the virtualenv created in [Dependency installation](## Dependency installation) if you are using a virtualenv by replacing `venvPathHere` with the path to your venv (such as `.venv`), or leave it unprovided to not use a virtualenv:
1. To compile the updater into an application that others can execute *and* to update your local copy at the path configured within the updater GUI, run `./deployAndUpdate.bat venvPathHere` in [Git Bash](https://git-scm.com/downloads) on Windows (bash is required since it is invoked within the file) or `bash ./deployAndUpdate.sh venvPathHere` on macOS or Linux. You can also perform individual steps from this process using the steps under [Usage](##Usage).

## Using a modpack

#### These are example steps; modify URLs, etc. as needed.

Installing the modpack:
1. Download the modpack: http://hostedUrlHere/ModpackNameHere.zip
2. Download MultiMC (a Minecraft launcher) from [https://multimc.org/#Download](https://multimc.org/#Download) and extract it.
3. Run MultiMC.exe (or whatever the program name is). If you get a message saying "Windows Defender SmartScreen prevented an unrecognized app from starting. Running this app might put your PC at risk.", you can click "More info" and then "Run anyway" to bypass it.
4. Add your Minecraft account at the top right.
5. Click "Add Instance" at the top left.
6. Click "Import from zip" on the left.
7. Click "Browse" and choose the modpack zip file which was downloaded in step 1.
8. Click "OK" and wait for it to extract and install the modpack.
9. Double-click the new modpack icon that appears inside MultiMC, and the game will start up.

If you get an error before the game starts such as "RuntimeException: No OpenGL context found in the current thread.", you may need to update Forge under Edit Instance -> Version -> Install Forge. Select the version at the top (latest), not the one that has a star next to it.

To update the modpack:
1. Download, extract, and run the modpack updater:
   - Windows: http://hostedUrlHere/ModpackNameHereUpdater.zip
   - macOS: http://hostedUrlHere/ModpackNameHereUpdater_macOS.zip
   - Linux: http://hostedUrlHere/ModpackNameHereUpdater_Linux.zip
2. In the text box, enter the path to your MultiMC instance which can be gotten from the "Instance Folder" button on the right sidebar of the MultiMC window (only needs to be entered in once, since it will be remembered)
3. Press the update button.
