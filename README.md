# FRcmd

FRcmd is a Windows command-line launcher for desktop applications. It lets you start software from the terminal with short commands such as:

```powershell
fr QQ
fr wx
fr wyy
fr QQ wyy
```

FRcmd works by collecting `.lnk` shortcut files into one managed shortcut folder, then matching your command input against shortcut names, aliases, and Chinese pinyin initials.

## Features

- Start one or more applications from the command line.
- Match shortcut names case-insensitively.
- Match Chinese shortcut names directly.
- Match Chinese pinyin initials, for example `fr wyy` for `网易云音乐.lnk`.
- Support custom aliases through `aliases.json`.
- Scan both the current user desktop and the public desktop.
- Support OneDrive redirected Desktop folders.
- Move the managed shortcut folder to a custom location.
- Print or open the current shortcut folder.
- Cache shortcut metadata in an index for faster matching.
- Prefer the packaged `fr.exe` when available, with Python fallback.

## Project Structure

```text
FRcmd/
  frcmd.py        Main Python implementation.
  fr.cmd         Windows command entrypoint.
  install.ps1    Adds this project to user PATH and initializes FRcmd.
  build.ps1      Builds dist/fr/fr.exe with PyInstaller.
  test_frcmd.py  Unit tests.
  shortcuts/     Managed shortcut folder after `fr -m <this project path>`.
```

FRcmd also stores small metadata files under:

```text
%APPDATA%\FRcmd\
  config.json    Stores the active shortcut folder path.
  index.json     Stores cached shortcut matching data.
```

## First Use

### 1. Install

Open PowerShell in the project directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

This script:

- Adds the project directory to your user `PATH`.
- Initializes FRcmd's config file.
- Creates the default shortcut folder if needed.
- Scans desktop shortcuts once.
- Broadcasts the environment-variable change to Windows.

Open a new terminal after installation.

### 2. Build the Faster Executable

If PyInstaller is installed, build the packaged executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The output is:

```text
dist\fr\fr.exe
```

`fr.cmd` automatically uses `dist\fr\fr.exe` when it exists. If it does not exist, `fr.cmd` falls back to:

```text
python frcmd.py ...
```

### 3. Choose a Shortcut Folder

Move the managed shortcut folder into this project, or any other parent directory:

```powershell
fr -m D:\MyProject\FRcmd
```

This creates and uses:

```text
D:\MyProject\FRcmd\shortcuts
```

FRcmd moves only managed config items:

- `.lnk`
- `aliases.json`

It will not move source code, `.git`, test files, or other project files.

### 4. Refresh Shortcuts

Scan desktop shortcuts into the current shortcut folder:

```powershell
fr -f
```

FRcmd scans:

- The real current-user Desktop from Windows registry.
- OneDrive Desktop if present.
- `%USERPROFILE%\Desktop`.
- `C:\Users\Public\Desktop`.

## Commands

```powershell
fr <name> [name...]
```

Start one or more matched shortcuts.

Examples:

```powershell
fr QQ
fr 微信
fr wyy
fr QQ wyy
```

```powershell
fr -f
```

Scan desktop `.lnk` files into the current shortcut folder.

```powershell
fr -o
```

Open the current shortcut folder in File Explorer.

```powershell
fr -p
```

Print the shortcuts currently available in the shortcut folder.

```powershell
fr -m <parent-path>
```

Move the managed shortcut folder to:

```text
<parent-path>\shortcuts
```

Example:

```powershell
fr -m D:\Tools
```

Result:

```text
D:\Tools\shortcuts
```

```powershell
fr help
```

Print help.

## Matching Rules

FRcmd checks each shortcut using:

- Shortcut file name, without `.lnk`.
- Aliases from `aliases.json`.
- Pinyin initials generated from Chinese names.

Priority:

1. Exact match.
2. Partial match.
3. Prefix partial match before contains match.
4. Alphabetical order as the final tie-breaker.

Example:

```text
网易云音乐.lnk
```

Can be started with:

```powershell
fr 网易云音乐
fr 网易云
fr wyy
```

## Aliases

Create an `aliases.json` file inside the active shortcut folder:

```json
{
  "微信": ["wx", "weixin"],
  "网易云音乐": ["wyy", "netease"],
  "Visual Studio Code": ["vscode", "code"]
}
```

Then run:

```powershell
fr -p
```

or any normal launch command. FRcmd will rebuild the index automatically when aliases change.

## Performance

FRcmd uses `%APPDATA%\FRcmd\index.json` as a shortcut index. The index stores:

- Shortcut names.
- Shortcut paths.
- Aliases.
- Precomputed matching keys.

The index is rebuilt automatically when:

- `.lnk` files change.
- `aliases.json` changes.
- `fr -f` imports new shortcuts.
- `fr -m` moves the shortcut folder.

For best startup speed, build the executable with:

```powershell
.\build.ps1
```

The first run of a newly built executable can be slower because Windows may scan it. Later runs should be faster.

## Development

Run tests:

```powershell
python -m unittest -v
```

Build executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

## Release

Version `v1.0.0` is intended to ship with:

- Source changes.
- `dist\fr\fr.exe` as the release executable asset.

The build output is ignored by Git and should be uploaded to GitHub Releases instead of committed.

## Troubleshooting

### `fr` Is Not Recognized

Open a new terminal after running `install.ps1`.

Confirm PATH resolution:

```powershell
where fr
```

### Shortcut Not Found

Refresh desktop shortcuts:

```powershell
fr -f
```

Then list known shortcuts:

```powershell
fr -p
```

### Wrong Shortcut Folder

Open the current shortcut folder:

```powershell
fr -o
```

Move it:

```powershell
fr -m D:\SomeParentFolder
```

The new shortcut folder will be:

```text
D:\SomeParentFolder\shortcuts
```
