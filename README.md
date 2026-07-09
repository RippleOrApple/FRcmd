# FRcmd

<p align="center">
  <a href="#中文"><kbd>中文</kbd></a>
  <a href="#english"><kbd>English</kbd></a>
</p>

## 中文

<p align="right">
  <a href="#english"><kbd>Switch to English</kbd></a>
</p>

FRcmd 是一个面向 Windows 的命令行软件启动器。它把常用软件的 `.lnk` 快捷方式集中到一个配置文件夹里，然后让你用命令快速启动软件。

例如：

```powershell
fr QQ
fr 微信
fr wyy
fr QQ wyy
```

`fr wyy` 可以匹配 `网易云音乐.lnk`，因为 FRcmd 支持中文名称的拼音首字母匹配。

### 功能概述

- 支持从命令行启动一个或多个软件。
- 支持大小写不敏感匹配。
- 支持中文快捷方式名称。
- 支持中文拼音首字母匹配，例如 `wyy` 匹配 `网易云音乐`。
- 支持通过 `fr -a` 快速创建别名，也支持手动编辑 `aliases.json`。
- 支持扫描当前用户桌面、OneDrive 桌面和公共桌面。
- 支持打开、打印、移动当前快捷方式文件夹。
- 使用索引缓存提升匹配速度。
- 如果存在打包后的 `dist\fr.exe`，会优先使用 exe；否则回退到 Python 脚本。

### 项目结构

```text
FRcmd/
  frcmd.py        主程序，包含命令解析、匹配、配置管理等逻辑。
  fr.cmd         Windows 命令入口。
  install.ps1    安装脚本，将项目目录加入用户 PATH 并初始化配置。
  build.ps1      使用 PyInstaller 构建 dist/fr.exe。
  test_frcmd.py  单元测试。
  config/        本机配置元数据目录，包含 config.json、index.json、aliases.json。
  shortcuts/     默认快捷方式文件夹，保存 .lnk 文件。
```

默认情况下，FRcmd 会把本机配置和快捷方式都放在安装目录内：

```text
FRcmd\config\
  config.json    记录当前快捷方式配置文件夹路径。
  index.json     记录快捷方式索引缓存。
  aliases.json   记录软件别名。

FRcmd\shortcuts\
  *.lnk          软件快捷方式。
```

旧版本保存在 `%APPDATA%\FRcmd\config.json` 的配置仍会被读取；新的配置会写入 `FRcmd\config`。

### 初次使用

#### 1. 安装

在项目目录中打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

安装脚本会：

- 将当前项目目录加入用户 `PATH`。
- 初始化 FRcmd 配置文件。
- 创建默认快捷方式文件夹：`<FRcmd 安装目录>\shortcuts`。
- 扫描一次桌面快捷方式。
- 通知 Windows 环境变量已变更。

安装后请重新打开一个终端。

#### 2. 构建更快的 exe

如果已经安装 PyInstaller，可以执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

构建输出：

```text
dist\fr.exe
```

`fr.cmd` 会优先调用 `dist\fr.exe`。如果该文件不存在，则回退到：

```text
python frcmd.py ...
```

#### 3. 选择配置文件夹

你可以把快捷方式配置文件夹移动到任意父目录下：

```powershell
fr -m D:\MyProject\FRcmd
```

实际使用的目录会是：

```text
D:\MyProject\FRcmd\shortcuts
```

`fr -m` 只会移动 FRcmd 管理的快捷方式：

- `.lnk`

它不会移动源码、`.git`、测试文件、`aliases.json` 或其他项目文件。别名、索引和配置文件始终默认保存在 `FRcmd\config`。

#### 4. 刷新桌面快捷方式

```powershell
fr -f
```

FRcmd 会扫描：

- Windows 注册表中的真实当前用户桌面。
- OneDrive 桌面。
- `%USERPROFILE%\Desktop`。
- `C:\Users\Public\Desktop`。

### 命令说明

启动软件：

```powershell
fr <软件名或简称> [软件名或简称...]
```

示例：

```powershell
fr QQ
fr 微信
fr wyy
fr QQ wyy
```

扫描桌面快捷方式：

```powershell
fr -f
```

在文件管理器中打开当前快捷方式文件夹：

```powershell
fr -o
```

打印当前快捷方式文件夹中的软件快捷方式：

```powershell
fr -p
```

交互式添加别名：

```powershell
fr -a
```

流程示例：

```text
请输入软件名：wyy
do you mean 网易云音乐?(y/n) y
请输入别名：music
已为 网易云音乐 添加别名：music
```

移动配置文件夹：

```powershell
fr -m <父路径>
```

示例：

```powershell
fr -m D:\Tools
```

结果：

```text
D:\Tools\shortcuts
```

查看帮助：

```powershell
fr help
```

### 匹配规则

FRcmd 会检查：

- 快捷方式文件名，不含 `.lnk`。
- `FRcmd\config\aliases.json` 中的别名。
- 中文名称生成的拼音首字母。

优先级：

1. 完全匹配。
2. 部分匹配。
3. 部分匹配中，前缀匹配优先于包含匹配。
4. 最后按名称排序作为稳定兜底。

例如：

```text
网易云音乐.lnk
```

可以用以下命令启动：

```powershell
fr 网易云音乐
fr 网易云
fr wyy
```

### 别名配置

推荐使用 `fr -a` 创建别名：

```powershell
fr -a
```

也可以手动编辑 `FRcmd\config\aliases.json`：

```json
{
  "微信": ["wx", "weixin"],
  "网易云音乐": ["wyy", "netease"],
  "Visual Studio Code": ["vscode", "code"]
}
```

修改别名后，FRcmd 会在下一次命令执行时自动重建索引。

### 性能

FRcmd 使用 `FRcmd\config\index.json` 缓存快捷方式索引，缓存内容包括：

- 快捷方式名称。
- 快捷方式路径。
- 别名。
- 预计算的匹配 key。

索引会在以下情况自动重建：

- `.lnk` 文件发生变化。
- `aliases.json` 发生变化。
- 执行 `fr -f` 导入快捷方式。
- 执行 `fr -m` 移动快捷方式文件夹。

建议构建 exe 以获得更快的热启动速度：

```powershell
.\build.ps1
```

刚构建出的 exe 第一次运行可能较慢，因为 Windows 可能会进行安全扫描；后续运行会更快。

### 开发

运行测试：

```powershell
python -m unittest -v
```

构建 exe：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

### Release

`v1.0.0` 发布内容包括：

- 源码和文档。
- GitHub Release 中的 `fr.exe` 发布资产。

构建产物不会提交到 Git 仓库，应上传到 GitHub Releases。

### 常见问题

#### `fr` 无法识别

运行 `install.ps1` 后重新打开终端。

确认命令解析：

```powershell
where fr
```

#### 找不到快捷方式

刷新桌面快捷方式：

```powershell
fr -f
```

查看已识别的软件：

```powershell
fr -p
```

#### 快捷方式文件夹不对

打开当前快捷方式文件夹：

```powershell
fr -o
```

移动快捷方式文件夹：

```powershell
fr -m D:\SomeParentFolder
```

新的快捷方式文件夹会是：

```text
D:\SomeParentFolder\shortcuts
```

## English

<p align="right">
  <a href="#中文"><kbd>切换到中文</kbd></a>
</p>

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
  build.ps1      Builds dist/fr.exe with PyInstaller.
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
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Build output:

```text
dist\fr.exe
```

`fr.cmd` automatically uses `dist\fr.exe` when it exists. If it does not exist, it falls back to:

```text
python frcmd.py ...
```

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

FRcmd checks:

- Shortcut file names without `.lnk`.
- Aliases from `FRcmd\config\aliases.json`.
- Pinyin initials generated from Chinese names.

Priority:

1. Exact match.
2. Partial match.
3. Prefix partial match before contains match.
4. Name sorting as the final stable fallback.

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
.\build.ps1
```

The first run of a newly built executable may be slower because Windows may scan it. Later runs should be faster.

### Development

Run tests:

```powershell
python -m unittest -v
```

Build executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
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
