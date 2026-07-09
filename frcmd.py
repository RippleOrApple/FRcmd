from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


APP_NAME = "FRcmd"
CONFIG_FILE = "config.json"
ALIASES_FILE = "aliases.json"
INDEX_FILE = "index.json"
CONFIG_DIR_NAME = "config"
SHORTCUT_DIR_NAME = "shortcuts"
PINYIN_INITIAL_RANGES = (
    (-20319, "a"),
    (-20283, "b"),
    (-19775, "c"),
    (-19218, "d"),
    (-18710, "e"),
    (-18526, "f"),
    (-18239, "g"),
    (-17922, "h"),
    (-17417, "j"),
    (-16474, "k"),
    (-16212, "l"),
    (-15640, "m"),
    (-15165, "n"),
    (-14922, "o"),
    (-14914, "p"),
    (-14630, "q"),
    (-14149, "r"),
    (-14090, "s"),
    (-13318, "t"),
    (-12838, "w"),
    (-12556, "x"),
    (-11847, "y"),
    (-11055, "z"),
)


@dataclass(frozen=True)
class Shortcut:
    name: str
    path: Path
    aliases: tuple[str, ...] = ()
    match_keys: tuple[str, ...] = field(default=(), compare=False)


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / "AppData" / "Roaming" / APP_NAME


def install_dir() -> Path:
    env_home = os.environ.get("FRCMD_HOME")
    if env_home:
        return Path(env_home).expanduser()

    executable = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    parent = executable.parent
    if parent.name.casefold() == "fr" and parent.parent.name.casefold() == "dist":
        return parent.parent.parent
    if parent.name.casefold() == "dist":
        return parent.parent
    return parent


def config_dir() -> Path:
    return install_dir() / CONFIG_DIR_NAME


def legacy_settings_path() -> Path:
    return app_data_dir() / CONFIG_FILE


def settings_path() -> Path:
    return config_dir() / CONFIG_FILE


def index_path() -> Path:
    return config_dir() / INDEX_FILE


def aliases_path() -> Path:
    return config_dir() / ALIASES_FILE


def legacy_aliases_path(shortcut_dir: Path) -> Path:
    return shortcut_dir / ALIASES_FILE


def default_shortcut_dir() -> Path:
    return install_dir() / SHORTCUT_DIR_NAME


def normalize(value: str) -> str:
    return value.strip().casefold()


def chinese_initial(char: str) -> str:
    try:
        encoded = char.encode("gbk")
    except UnicodeEncodeError:
        return char

    if len(encoded) != 2:
        return char

    code = encoded[0] * 256 + encoded[1] - 65536
    initial = char
    for start, letter in PINYIN_INITIAL_RANGES:
        if code >= start:
            initial = letter
        else:
            break
    return initial


def pinyin_initials(value: str) -> str:
    return "".join(chinese_initial(char) for char in value)


def load_config() -> dict[str, str] | None:
    path = settings_path()
    if not path.exists():
        legacy_path = legacy_settings_path()
        if legacy_path.exists():
            path = legacy_path
        else:
            return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    shortcut_dir = data.get("shortcut_dir")
    if not isinstance(shortcut_dir, str) or not shortcut_dir.strip():
        return None
    return {"shortcut_dir": shortcut_dir}


def save_config(shortcut_dir: Path) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"shortcut_dir": str(shortcut_dir)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_shortcut_dir(config: dict[str, str]) -> Path:
    return Path(os.path.expandvars(config["shortcut_dir"])).expanduser()


def read_alias_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(f"别名文件格式错误，已忽略：{path}")
        return {}
    return data if isinstance(data, dict) else {}


def load_aliases(shortcut_dir: Path) -> dict[str, list[str]]:
    data: dict[str, object] = {}
    data.update(read_alias_file(legacy_aliases_path(shortcut_dir)))
    data.update(read_alias_file(aliases_path()))

    aliases: dict[str, list[str]] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, list):
            aliases[key] = [item for item in value if isinstance(item, str)]
    return aliases


def save_aliases(aliases: dict[str, list[str]]) -> None:
    path = aliases_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")


def add_alias(shortcut_name: str, alias: str, shortcut_dir: Path) -> bool:
    clean_alias = alias.strip()
    if not clean_alias:
        return False

    aliases = load_aliases(shortcut_dir)
    values = aliases.setdefault(shortcut_name, [])
    if any(normalize(value) == normalize(clean_alias) for value in values):
        return False
    values.append(clean_alias)
    save_aliases(aliases)
    build_shortcut_index(shortcut_dir)
    return True


def file_signature(path: Path) -> dict[str, int | None]:
    try:
        stat = path.stat()
    except OSError:
        return {"mtime_ns": None, "size": None}
    return {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}


def shortcut_dir_signature(shortcut_dir: Path) -> dict[str, int | None]:
    return file_signature(shortcut_dir)


def shortcut_names_signature(shortcut_dir: Path) -> list[str]:
    try:
        return sorted(path.name for path in shortcut_dir.glob("*.lnk"))
    except OSError:
        return []


def aliases_signature(shortcut_dir: Path) -> dict[str, int | None]:
    return {
        "config": file_signature(aliases_path()),
        "legacy": file_signature(legacy_aliases_path(shortcut_dir)),
    }


def shortcut_match_keys(name: str, aliases: Iterable[str] = ()) -> tuple[str, ...]:
    keys: list[str] = []
    for key in (name, *aliases):
        if key not in keys:
            keys.append(key)
        initial_key = pinyin_initials(key)
        if initial_key not in keys:
            keys.append(initial_key)
    return tuple(keys)


def build_shortcut_index(shortcut_dir: Path) -> list[Shortcut]:
    aliases = load_aliases(shortcut_dir)
    shortcuts: list[Shortcut] = []
    for path in sorted(shortcut_dir.glob("*.lnk"), key=lambda item: item.name.casefold()):
        shortcut_aliases = tuple(aliases.get(path.stem, []))
        shortcuts.append(
            Shortcut(
                path.stem,
                path,
                shortcut_aliases,
                shortcut_match_keys(path.stem, shortcut_aliases),
            )
        )
    save_shortcut_index(shortcut_dir, shortcuts)
    return shortcuts


def save_shortcut_index(shortcut_dir: Path, shortcuts: Iterable[Shortcut]) -> None:
    payload = {
        "shortcut_dir": str(shortcut_dir),
        "shortcut_dir_signature": shortcut_dir_signature(shortcut_dir),
        "shortcut_names": shortcut_names_signature(shortcut_dir),
        "aliases_signature": aliases_signature(shortcut_dir),
        "shortcuts": [
            {
                "name": shortcut.name,
                "path": str(shortcut.path),
                "aliases": list(shortcut.aliases),
                "match_keys": list(shortcut.match_keys),
            }
            for shortcut in shortcuts
        ],
    }

    path = index_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_shortcut_index(shortcut_dir: Path) -> list[Shortcut] | None:
    path = index_path()
    try:
        if not path.exists():
            return None
    except OSError:
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if data.get("shortcut_dir") != str(shortcut_dir):
        return None
    if data.get("shortcut_dir_signature") != shortcut_dir_signature(shortcut_dir):
        return None
    if data.get("shortcut_names") != shortcut_names_signature(shortcut_dir):
        return None
    if data.get("aliases_signature") != aliases_signature(shortcut_dir):
        return None

    raw_shortcuts = data.get("shortcuts")
    if not isinstance(raw_shortcuts, list):
        return None

    shortcuts: list[Shortcut] = []
    for item in raw_shortcuts:
        if not isinstance(item, dict):
            return None
        name = item.get("name")
        path_value = item.get("path")
        aliases = item.get("aliases")
        match_keys = item.get("match_keys")
        if not isinstance(name, str) or not isinstance(path_value, str):
            return None
        if not isinstance(aliases, list) or not all(isinstance(alias, str) for alias in aliases):
            return None
        if not isinstance(match_keys, list) or not all(isinstance(key, str) for key in match_keys):
            return None
        shortcuts.append(Shortcut(name, Path(path_value), tuple(aliases), tuple(match_keys)))

    return shortcuts


def list_shortcuts(shortcut_dir: Path) -> list[Shortcut]:
    return load_shortcut_index(shortcut_dir) or build_shortcut_index(shortcut_dir)


def match_shortcut(query: str, shortcuts: Iterable[Shortcut]) -> Shortcut | None:
    wanted = normalize(query)
    if not wanted:
        return None

    candidates = list(shortcuts)

    def keys(shortcut: Shortcut) -> tuple[str, ...]:
        return shortcut.match_keys or shortcut_match_keys(shortcut.name, shortcut.aliases)

    exact = [
        shortcut
        for shortcut in candidates
        if any(normalize(key) == wanted for key in keys(shortcut))
    ]
    if exact:
        return sorted(exact, key=lambda shortcut: normalize(shortcut.name))[0]

    partial = [
        shortcut
        for shortcut in candidates
        if any(wanted in normalize(key) for key in keys(shortcut))
    ]
    if not partial:
        return None

    def partial_rank(shortcut: Shortcut) -> tuple[int, str]:
        starts_with_query = any(normalize(key).startswith(wanted) for key in keys(shortcut))
        return (0 if starts_with_query else 1, normalize(shortcut.name))

    return sorted(partial, key=partial_rank)[0]


def append_existing_dir(dirs: list[Path], path: Path) -> None:
    resolved = Path(os.path.expandvars(str(path))).expanduser()
    if not resolved.exists():
        return

    normalized = str(resolved).casefold()
    if any(str(existing).casefold() == normalized for existing in dirs):
        return
    dirs.append(resolved)


def user_desktop_dirs_from_registry() -> list[Path]:
    if os.name != "nt":
        return []

    try:
        import winreg
    except ImportError:
        return []

    registry_locations = [
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        ),
    ]

    dirs: list[Path] = []
    for root, key_path in registry_locations:
        try:
            with winreg.OpenKey(root, key_path) as key:
                value, _value_type = winreg.QueryValueEx(key, "Desktop")
        except OSError:
            continue
        if isinstance(value, str):
            append_existing_dir(dirs, Path(value))
    return dirs


def desktop_dirs() -> list[Path]:
    dirs: list[Path] = []
    for desktop in user_desktop_dirs_from_registry():
        append_existing_dir(dirs, desktop)

    append_existing_dir(dirs, Path.home() / "Desktop")

    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    if onedrive:
        append_existing_dir(dirs, Path(onedrive) / "Desktop")

    public = os.environ.get("PUBLIC")
    if public:
        append_existing_dir(dirs, Path(public) / "Desktop")
    else:
        append_existing_dir(dirs, Path("C:/Users/Public/Desktop"))
    return dirs


def transfer_shortcuts(shortcut_dir: Path) -> tuple[int, int]:
    shortcut_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    skipped = 0
    scanned = 0

    for desktop in desktop_dirs():
        scanned += 1
        print(f"扫描桌面目录：{desktop}")
        for source in desktop.glob("*.lnk"):
            target = shortcut_dir / source.name
            if target.exists():
                skipped += 1
                continue
            shutil.copy2(source, target)
            added += 1

    if scanned == 0:
        print("未找到可扫描的桌面目录。")
    print(f"已添加 {added} 个快捷方式。")
    print(f"已跳过 {skipped} 个已存在的快捷方式。")
    build_shortcut_index(shortcut_dir)
    return added, skipped


def bootstrap_default_config(scan_desktop: bool = True) -> Path:
    shortcut_dir = default_shortcut_dir()
    shortcut_dir.mkdir(parents=True, exist_ok=True)
    save_config(shortcut_dir)
    if scan_desktop:
        transfer_shortcuts(shortcut_dir)
    return shortcut_dir


def ensure_configured() -> Path | None:
    config = load_config()
    if config is None:
        print("首次运行，正在自动初始化 FRcmd。")
        return bootstrap_default_config()

    shortcut_dir = resolve_shortcut_dir(config)
    if not shortcut_dir.exists():
        print(f"配置目录不存在，已自动重建：{shortcut_dir}")
        shortcut_dir.mkdir(parents=True, exist_ok=True)
        transfer_shortcuts(shortcut_dir)
    return shortcut_dir


def configure() -> int:
    if load_config() is not None:
        print("FRcmd 已经完成配置。")
        return 0

    answer = input("是否使用默认配置目录？(y/n) ").strip().casefold()
    if answer == "y":
        shortcut_dir = default_shortcut_dir()
    elif answer == "n":
        raw_path = input("请输入配置文件夹路径：").strip()
        if not raw_path:
            print("配置文件夹路径不能为空。")
            return 1
        shortcut_dir = Path(os.path.expandvars(raw_path)).expanduser()
    else:
        print("请输入 y 或 n。")
        return 1

    shortcut_dir.mkdir(parents=True, exist_ok=True)
    save_config(shortcut_dir)
    print(f"配置完成：{shortcut_dir}")
    transfer_shortcuts(shortcut_dir)
    return 0


def print_config_shortcuts() -> int:
    shortcut_dir = ensure_configured()
    if shortcut_dir is None:
        return 1

    shortcuts = list_shortcuts(shortcut_dir)
    print(f"配置目录：{shortcut_dir}")
    if not shortcuts:
        print("当前没有软件快捷方式。")
        return 0

    for shortcut in shortcuts:
        print(shortcut.name)
    return 0


def prompt_add_alias() -> int:
    shortcut_dir = ensure_configured()
    if shortcut_dir is None:
        return 1

    shortcuts = list_shortcuts(shortcut_dir)
    if not shortcuts:
        transfer_shortcuts(shortcut_dir)
        shortcuts = list_shortcuts(shortcut_dir)
        if not shortcuts:
            print(f"快捷方式目录中没有 .lnk 快捷方式：{shortcut_dir}")
            return 1

    query = input("请输入软件名：").strip()
    if not query:
        print("软件名不能为空。")
        return 1

    shortcut = match_shortcut(query, shortcuts)
    if shortcut is None:
        print(f"未找到：{query}")
        return 1

    answer = input(f"do you mean {shortcut.name}?(y/n) ").strip().casefold()
    if answer != "y":
        print("已取消设置别名。")
        return 0

    alias = input("请输入别名：").strip()
    if not alias:
        print("别名不能为空。")
        return 1

    if not add_alias(shortcut.name, alias, shortcut_dir):
        print(f"别名已存在或无效：{alias}")
        return 1

    print(f"已为 {shortcut.name} 添加别名：{alias}")
    return 0


def config_dir_under_parent(raw_parent: str) -> Path:
    parent = Path(os.path.expandvars(raw_parent)).expanduser()
    return parent / SHORTCUT_DIR_NAME


def is_managed_config_item(path: Path) -> bool:
    return path.is_file() and path.suffix.casefold() == ".lnk"


def move_config_dir(raw_target: str) -> int:
    shortcut_dir = ensure_configured()
    if shortcut_dir is None:
        return 1

    if not raw_target.strip():
        print("新配置目录父路径不能为空。")
        return 1

    target_dir = config_dir_under_parent(raw_target)
    try:
        same_dir = shortcut_dir.resolve() == target_dir.resolve()
    except OSError:
        same_dir = False

    if same_dir:
        print(f"配置目录已经在该路径：{shortcut_dir}")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    skipped = 0

    for source in shortcut_dir.iterdir():
        if not is_managed_config_item(source):
            continue
        target = target_dir / source.name
        if target.exists():
            skipped += 1
            continue
        shutil.move(str(source), str(target))
        moved += 1

    save_config(target_dir)
    build_shortcut_index(target_dir)
    try:
        shortcut_dir.rmdir()
    except OSError:
        pass

    print(f"配置目录已转移到：{target_dir}")
    print(f"已移动 {moved} 个项目。")
    print(f"已跳过 {skipped} 个同名项目。")
    return 0


def open_config_dir() -> int:
    shortcut_dir = ensure_configured()
    if shortcut_dir is None:
        return 1

    startfile = getattr(os, "startfile", None)
    if startfile is None:
        print("当前系统不支持打开文件管理器。")
        print(f"配置目录：{shortcut_dir}")
        return 1

    try:
        startfile(str(shortcut_dir))
    except OSError as exc:
        print(f"打开配置目录失败：{exc}")
        print(f"配置目录：{shortcut_dir}")
        return 1

    print(f"已打开配置目录：{shortcut_dir}")
    return 0


def launch_shortcut(shortcut: Shortcut) -> bool:
    if os.environ.get("FRCMD_DRY_RUN") == "1":
        print(f"将启动：{shortcut.name} -> {shortcut.path}")
        return True

    startfile = getattr(os, "startfile", None)
    if startfile is None:
        print("当前系统不支持直接启动 .lnk 快捷方式。")
        return False

    try:
        startfile(str(shortcut.path))
    except OSError as exc:
        print(f"启动失败：{shortcut.name} ({exc})")
        return False

    print(f"已启动：{shortcut.name}")
    return True


def launch_many(queries: list[str]) -> int:
    shortcut_dir = ensure_configured()
    if shortcut_dir is None:
        return 1

    shortcuts = list_shortcuts(shortcut_dir)
    if not shortcuts:
        transfer_shortcuts(shortcut_dir)
        shortcuts = list_shortcuts(shortcut_dir)
        if not shortcuts:
            print(f"配置目录中没有 .lnk 快捷方式：{shortcut_dir}")
            print("请把需要启动的软件快捷方式放到该目录，或放到桌面后重新运行 FR。")
            return 1

    failed = 0
    for query in queries:
        shortcut = match_shortcut(query, shortcuts)
        if shortcut is None:
            print(f"未找到：{query}")
            failed += 1
            continue
        if not launch_shortcut(shortcut):
            failed += 1
    return 1 if failed else 0


def print_help() -> None:
    print(
        """FRcmd 使用说明：
fr <软件名或简称> [软件名或简称...]
  启动一个或多个软件。
  示例：fr QQ
  示例：fr QQ wyy

fr -c
  初始化 FRcmd 配置。

fr -f
  扫描桌面快捷方式，并添加到当前快捷方式文件夹。

fr -o
  在文件管理器中打开当前快捷方式文件夹。

fr -p
  打印当前快捷方式文件夹中的软件快捷方式。

fr -a
  交互式为软件添加别名。

fr -m <父路径>
  在指定父路径下创建 shortcuts 文件夹，并将快捷方式移动到那里。

fr help
  显示帮助信息。"""
    )


def print_command_error(message: str) -> int:
    print(message)
    print("执行 fr help 查看用法。")
    return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0].casefold() == "help":
        print_help()
        return 0

    if args == ["-c"]:
        return configure()

    if args == ["-f"]:
        shortcut_dir = ensure_configured()
        if shortcut_dir is None:
            return 1
        transfer_shortcuts(shortcut_dir)
        return 0

    if args == ["-o"]:
        return open_config_dir()

    if args == ["-p"]:
        return print_config_shortcuts()

    if args == ["-a"]:
        return prompt_add_alias()

    if args[0] == "-m" and len(args) != 2:
        return print_command_error("fr -m 需要且只需要一个路径参数。")

    if len(args) == 2 and args[0] == "-m":
        return move_config_dir(args[1])

    if args == ["--install"]:
        shortcut_dir = bootstrap_default_config()
        print(f"FRcmd 默认配置目录：{shortcut_dir}")
        return 0

    if args[0].startswith("-"):
        return print_command_error(f"未知命令：{args[0]}")

    return launch_many(args)


if __name__ == "__main__":
    raise SystemExit(main())
