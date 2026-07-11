# FRcmd

[**🇨🇳 中文**](./README_zh.md) | [**🇬🇧 English**](./README.md)

FRcmd is a Windows command-line launcher for desktop applications. It collects `.lnk` shortcuts into one managed shortcut folder and lets you start applications with short terminal commands.

Examples:

```powershell
fr QQ
fr 微信
fr wyy
fr QQ wyy
```

`fr wyy` can match `网易云音乐.lnk` because FRcmd supports pinyin initials generated from Chinese shortcut names.

### Feature Overview

- Launch one or more applications from the command line.
- Match shortcut names case-insensitively.
- Match Chinese shortcut names directly.
- Match Chinese pinyin initials, for example `wyy` for `网易云音乐`.
- Create aliases quickly with `fr -a`, or edit `aliases.json` manually.
- Scan the current user Desktop, OneDrive Desktop, and public Desktop.
- Open, print, and move the active shortcut folder.
- Cache shortcut metadata for faster matching.
- Prefer packaged `dist\fr.exe` when available, with Python fallback.

### Project Structure

```text
FRcmd/
  frcmd.py        Main implementation: command parsing, matching, and config management.
  fr.cmd         Windows command entrypoint.
  install.ps1    Adds this project to user PATH and initializes FRcmd.
  build-dist.ps1      Builds dist/fr.exe with PyInstaller.
  build-release.ps1  Builds a release/fr.exe that can install itself on first run.
  test_frcmd.py  Unit tests.
  config/        Local metadata folder with config.json, index.json, and aliases.json.
  shortcuts/     Default shortcut folder for .lnk files.
```

By default, FRcmd keeps both local metadata and shortcuts inside the install directory:

```text
FRcmd\config\
  config.json    Stores the active shortcut folder path.
  index.json     Stores cached shortcut matching data.
  aliases.json   Stores custom aliases.

FRcmd\shortcuts\
  *.lnk          Application shortcuts.
```

Configs from older versions at `%APPDATA%\FRcmd\config.json` are still read; new config writes go to `FRcmd\config`.

### First Use

#### 1. Install

Open PowerShell in the project directory and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer:

- Adds the project directory to your user `PATH`.
- Initializes the FRcmd config file.
- Creates the default shortcut folder: `<FRcmd install directory>\shortcuts`.
- Scans desktop shortcuts once.
- Broadcasts the environment-variable change to Windows.

Open a new terminal after installation.

#### 2. Build the Faster Executable

If PyInstaller is installed, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-dist.ps1
```

Build output:

```text
dist\fr.exe
```

`fr.cmd` automatically uses `dist\fr.exe` when it exists. If it does not exist, it falls back to:

```text
python frcmd.py ...
```

#### 2.1 Build the Release Executable

For GitHub Releases, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-release.ps1
```

Build output:

```text
release\fr.exe
```

This executable is intended for end users to download directly. On first run it copies itself to `%LOCALAPPDATA%\Programs\FRcmd`, adds that folder to the user `PATH`, creates the default `config` and `shortcuts` folders, and scans Desktop shortcuts. After opening a new terminal, users can run `fr QQ`.

#### 3. Choose a Shortcut Folder

Move the managed shortcut folder under any parent directory:

```powershell
fr -m D:\MyProject\FRcmd
```

The actual folder will be:

```text
D:\MyProject\FRcmd\shortcuts
```

`fr -m` only moves FRcmd-managed shortcuts:

- `.lnk`

It will not move source code, `.git`, tests, `aliases.json`, or other project files. Aliases, the index, and config files stay in `FRcmd\config` by default.

#### 4. Refresh Desktop Shortcuts

```powershell
fr -f
```

FRcmd scans:

- The real current-user Desktop from Windows registry.
- OneDrive Desktop.
- `%USERPROFILE%\Desktop`.
- `C:\Users\Public\Desktop`.

### Commands

Launch applications:

```powershell
fr <name-or-alias> [name-or-alias...]
```

Examples:

```powershell
fr QQ
fr 微信
fr wyy
fr QQ wyy
```

Scan desktop shortcuts:

```powershell
fr -f
```

Open the active shortcut folder in File Explorer:

```powershell
fr -o
```

Print shortcuts in the active shortcut folder:

```powershell
fr -p
```

Add an alias interactively:

```powershell
fr -a
```

Example flow:

```text
请输入软件名：wyy
do you mean 网易云音乐?(y/n) y
请输入别名：music
已为 网易云音乐 添加别名：music
```

Move the shortcut folder:

```powershell
fr -m <parent-path>
```

Example:

```powershell
fr -m D:\Tools
```

Result:

```text
D:\Tools\shortcuts
```

Show help:

```powershell
fr help
```

### Matching Rules

FRcmd matches in two stages:

1. Exact alias match from `FRcmd\config\aliases.json`.
2. If no alias matches exactly, match shortcut file names and pinyin initials generated from Chinese names.

For non-alias matching, the priority is:

1. Exact match.
2. Partial match.
3. Prefix partial match before contains match.
4. Name sorting as the final stable fallback.

Aliases only match exactly. A partial query such as `wech` will not match an alias like `wechat`.

Example:

```text
网易云音乐.lnk
```

Can be launched with:

```powershell
fr 网易云音乐
fr 网易云
fr wyy
```

### Aliases

Use `fr -a` to create aliases:

```powershell
fr -a
```

You can also edit `FRcmd\config\aliases.json` manually:

```json
{
  "微信": ["wx", "weixin"],
  "网易云音乐": ["wyy", "netease"],
  "Visual Studio Code": ["vscode", "code"]
}
```

FRcmd automatically rebuilds the index on the next command after aliases change.

### Performance

FRcmd uses `FRcmd\config\index.json` as a shortcut index. It stores:

- Shortcut names.
- Shortcut paths.
- Aliases.
- Precomputed matching keys.

The index is rebuilt automatically when:

- `.lnk` files change.
- `aliases.json` changes.
- `fr -f` imports shortcuts.
- `fr -m` moves the shortcut folder.

For better warm-start performance, build the executable:

```powershell
.\build-dist.ps1
```

The first run of a newly built executable may be slower because Windows may scan it. Later runs should be faster.

### Development

Run tests:

```powershell
python -m unittest -v
```

Build executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-dist.ps1
```

### Release

`v1.0.0` includes:

- Source code and documentation.
- `fr.exe` as a GitHub Release asset.

Build outputs are not committed to Git. Upload them to GitHub Releases instead.

### Troubleshooting

#### `fr` Is Not Recognized

Open a new terminal after running `install.ps1`.

Check command resolution:

```powershell
where fr
```

#### Shortcut Not Found

Refresh desktop shortcuts:

```powershell
fr -f
```

Print known shortcuts:

```powershell
fr -p
```

#### Wrong Shortcut Folder

Open the active shortcut folder:

```powershell
fr -o
```

Move the shortcut folder:

```powershell
fr -m D:\SomeParentFolder
```

The new shortcut folder will be:

```text
D:\SomeParentFolder\shortcuts
```


