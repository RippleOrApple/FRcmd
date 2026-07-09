import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import frcmd


WECHAT = "\u5fae\u4fe1"
WECHAT_READING = "\u5fae\u4fe1\u8bfb\u4e66"
NETEASE_MUSIC = "\u7f51\u6613\u4e91\u97f3\u4e50"


class MatchShortcutTests(unittest.TestCase):
    def test_exact_name_wins(self):
        shortcuts = [
            frcmd.Shortcut(WECHAT_READING, Path(f"{WECHAT_READING}.lnk"), ("wxds",)),
            frcmd.Shortcut(WECHAT, Path(f"{WECHAT}.lnk"), ("wx", "\u5fae")),
        ]

        self.assertEqual(frcmd.match_shortcut(WECHAT, shortcuts).name, WECHAT)

    def test_exact_alias_wins(self):
        shortcuts = [
            frcmd.Shortcut(WECHAT, Path(f"{WECHAT}.lnk"), ("wx",)),
            frcmd.Shortcut(NETEASE_MUSIC, Path(f"{NETEASE_MUSIC}.lnk"), ("wyy",)),
        ]

        self.assertEqual(frcmd.match_shortcut("wyy", shortcuts).name, NETEASE_MUSIC)

    def test_case_insensitive(self):
        shortcuts = [frcmd.Shortcut("QQ", Path("QQ.lnk"), ("qq",))]

        self.assertEqual(frcmd.match_shortcut("qq", shortcuts).name, "QQ")

    def test_pinyin_initials_match_chinese_name(self):
        shortcuts = [frcmd.Shortcut(NETEASE_MUSIC, Path(f"{NETEASE_MUSIC}.lnk"))]

        self.assertEqual(frcmd.match_shortcut("wyy", shortcuts).name, NETEASE_MUSIC)

    def test_prefix_partial_wins_over_contains(self):
        shortcuts = [
            frcmd.Shortcut("dabc", Path("dabc.lnk")),
            frcmd.Shortcut("abcd", Path("abcd.lnk")),
        ]

        self.assertEqual(frcmd.match_shortcut("abc", shortcuts).name, "abcd")

    def test_returns_none_when_not_found(self):
        shortcuts = [frcmd.Shortcut("QQ", Path("QQ.lnk"))]

        self.assertIsNone(frcmd.match_shortcut("wx", shortcuts))


class ShortcutLoadingTests(unittest.TestCase):
    def test_list_shortcuts_loads_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / f"{WECHAT}.lnk").write_text("", encoding="utf-8")
            (root / "aliases.json").write_text(
                '{"\u5fae\u4fe1": ["wx", "\u5fae"]}',
                encoding="utf-8",
            )

            shortcuts = frcmd.list_shortcuts(root)

            self.assertEqual(
                shortcuts,
                [frcmd.Shortcut(WECHAT, root / f"{WECHAT}.lnk", ("wx", "\u5fae"))],
            )

    def test_list_shortcuts_uses_valid_index_cache(self):
        with tempfile.TemporaryDirectory() as appdata_temp, tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "QQ.lnk").write_text("", encoding="utf-8")

            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}):
                first = frcmd.list_shortcuts(root)
                with mock.patch.object(frcmd, "build_shortcut_index") as build_index:
                    second = frcmd.list_shortcuts(root)

        self.assertEqual(first, second)
        build_index.assert_not_called()

    def test_list_shortcuts_rebuilds_when_directory_changes(self):
        with tempfile.TemporaryDirectory() as appdata_temp, tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "QQ.lnk").write_text("", encoding="utf-8")

            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}):
                first = frcmd.list_shortcuts(root)
                (root / f"{WECHAT}.lnk").write_text("", encoding="utf-8")
                second = frcmd.list_shortcuts(root)

        self.assertEqual([shortcut.name for shortcut in first], ["QQ"])
        self.assertEqual([shortcut.name for shortcut in second], ["QQ", WECHAT])

    def test_match_shortcut_uses_precomputed_keys(self):
        shortcut = frcmd.Shortcut(NETEASE_MUSIC, Path(f"{NETEASE_MUSIC}.lnk"), (), ("wyy",))

        with mock.patch.object(frcmd, "pinyin_initials", side_effect=AssertionError("should not run")):
            match = frcmd.match_shortcut("wyy", [shortcut])

        self.assertEqual(match.name, NETEASE_MUSIC)


class TransferShortcutTests(unittest.TestCase):
    def test_desktop_dirs_includes_onedrive_desktop(self):
        with tempfile.TemporaryDirectory() as home_temp, tempfile.TemporaryDirectory() as onedrive_temp:
            home = Path(home_temp)
            onedrive = Path(onedrive_temp)
            (onedrive / "Desktop").mkdir()

            with mock.patch.object(frcmd, "user_desktop_dirs_from_registry", return_value=[]), mock.patch.object(
                frcmd.Path, "home", return_value=home
            ), mock.patch.dict(os.environ, {"OneDrive": str(onedrive), "PUBLIC": ""}):
                dirs = frcmd.desktop_dirs()

        self.assertIn(onedrive / "Desktop", dirs)

    def test_desktop_dirs_deduplicates_registry_and_fallback_paths(self):
        with tempfile.TemporaryDirectory() as home_temp:
            home = Path(home_temp)
            desktop = home / "Desktop"
            desktop.mkdir()

            with mock.patch.object(frcmd, "user_desktop_dirs_from_registry", return_value=[desktop]), mock.patch.object(
                frcmd.Path, "home", return_value=home
            ), mock.patch.dict(os.environ, {"PUBLIC": ""}):
                dirs = frcmd.desktop_dirs()

        self.assertEqual(dirs.count(desktop), 1)

    def test_transfer_copies_lnk_and_skips_existing(self):
        with tempfile.TemporaryDirectory() as source_temp, tempfile.TemporaryDirectory() as target_temp:
            source = Path(source_temp)
            target = Path(target_temp)
            (source / "QQ.lnk").write_text("qq", encoding="utf-8")
            (source / "note.txt").write_text("ignored", encoding="utf-8")
            (target / f"{WECHAT}.lnk").write_text("existing", encoding="utf-8")
            (source / f"{WECHAT}.lnk").write_text("new", encoding="utf-8")

            with mock.patch.object(frcmd, "desktop_dirs", return_value=[source]):
                added, skipped = frcmd.transfer_shortcuts(target)

            self.assertEqual((added, skipped), (1, 1))
            self.assertTrue((target / "QQ.lnk").exists())
            self.assertEqual((target / f"{WECHAT}.lnk").read_text(encoding="utf-8"), "existing")
            self.assertFalse((target / "note.txt").exists())


class ConfigTests(unittest.TestCase):
    def test_ensure_configured_bootstraps_default_config(self):
        with tempfile.TemporaryDirectory() as appdata_temp:
            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}), mock.patch.object(
                frcmd, "transfer_shortcuts", return_value=(0, 0)
            ) as transfer:
                shortcut_dir = frcmd.ensure_configured()

            self.assertEqual(shortcut_dir, Path(appdata_temp) / "FRcmd" / "shortcuts")
            self.assertTrue((Path(appdata_temp) / "FRcmd" / "config.json").exists())
            transfer.assert_called_once_with(shortcut_dir)

    def test_open_config_dir_uses_file_manager(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with mock.patch.object(frcmd, "ensure_configured", return_value=root), mock.patch.object(
                frcmd.os, "startfile", create=True
            ) as startfile:
                code = frcmd.open_config_dir()

        self.assertEqual(code, 0)
        startfile.assert_called_once_with(str(root))

    def test_main_open_config_dir_command(self):
        with mock.patch.object(frcmd, "open_config_dir", return_value=0) as open_config_dir:
            code = frcmd.main(["-o"])

        self.assertEqual(code, 0)
        open_config_dir.assert_called_once_with()

    def test_print_config_shortcuts_lists_shortcut_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "QQ.lnk").write_text("", encoding="utf-8")
            (root / f"{WECHAT}.lnk").write_text("", encoding="utf-8")

            with mock.patch.object(frcmd, "ensure_configured", return_value=root), mock.patch(
                "builtins.print"
            ) as print_mock:
                code = frcmd.print_config_shortcuts()

        self.assertEqual(code, 0)
        printed = [call.args[0] for call in print_mock.call_args_list]
        self.assertIn("QQ", printed)
        self.assertIn(WECHAT, printed)

    def test_config_dir_under_parent_adds_shortcuts_folder(self):
        self.assertEqual(frcmd.config_dir_under_parent("D:\\Tools"), Path("D:\\Tools") / "shortcuts")

    def test_move_config_dir_moves_items_and_updates_config(self):
        with tempfile.TemporaryDirectory() as appdata_temp, tempfile.TemporaryDirectory() as current_temp, tempfile.TemporaryDirectory() as target_temp:
            current = Path(current_temp)
            target_parent = Path(target_temp) / "new-parent"
            target = target_parent / "shortcuts"
            (current / "QQ.lnk").write_text("qq", encoding="utf-8")

            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}), mock.patch.object(
                frcmd, "ensure_configured", return_value=current
            ):
                code = frcmd.move_config_dir(str(target_parent))

            config = json.loads((Path(appdata_temp) / "FRcmd" / "config.json").read_text(encoding="utf-8"))

            self.assertEqual(code, 0)
            self.assertTrue((target / "QQ.lnk").exists())
            self.assertFalse((current / "QQ.lnk").exists())
            self.assertEqual(config["shortcut_dir"], str(target))

    def test_move_config_dir_does_not_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as appdata_temp, tempfile.TemporaryDirectory() as current_temp, tempfile.TemporaryDirectory() as target_temp:
            current = Path(current_temp)
            target_parent = Path(target_temp)
            target = target_parent / "shortcuts"
            target.mkdir()
            (current / "QQ.lnk").write_text("source", encoding="utf-8")
            (target / "QQ.lnk").write_text("target", encoding="utf-8")

            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}), mock.patch.object(
                frcmd, "ensure_configured", return_value=current
            ):
                code = frcmd.move_config_dir(str(target_parent))

            self.assertEqual(code, 0)
            self.assertEqual((target / "QQ.lnk").read_text(encoding="utf-8"), "target")
            self.assertEqual((current / "QQ.lnk").read_text(encoding="utf-8"), "source")

    def test_move_config_dir_only_moves_managed_config_items(self):
        with tempfile.TemporaryDirectory() as appdata_temp, tempfile.TemporaryDirectory() as current_temp, tempfile.TemporaryDirectory() as target_temp:
            current = Path(current_temp)
            target = Path(target_temp) / "shortcuts"
            (current / ".git").mkdir()
            (current / "frcmd.py").write_text("code", encoding="utf-8")
            (current / "QQ.lnk").write_text("qq", encoding="utf-8")
            (current / "aliases.json").write_text("{}", encoding="utf-8")

            with mock.patch.dict(os.environ, {"APPDATA": appdata_temp}), mock.patch.object(
                frcmd, "ensure_configured", return_value=current
            ):
                code = frcmd.move_config_dir(target_temp)

            self.assertEqual(code, 0)
            self.assertTrue((target / "QQ.lnk").exists())
            self.assertTrue((target / "aliases.json").exists())
            self.assertTrue((current / ".git").exists())
            self.assertTrue((current / "frcmd.py").exists())
            self.assertFalse((target / ".git").exists())
            self.assertFalse((target / "frcmd.py").exists())

    def test_main_print_and_move_commands(self):
        with mock.patch.object(frcmd, "print_config_shortcuts", return_value=0) as print_shortcuts:
            print_code = frcmd.main(["-p"])

        with mock.patch.object(frcmd, "move_config_dir", return_value=0) as move_config:
            move_code = frcmd.main(["-m", "D:\\FRcmdShortcuts"])

        self.assertEqual(print_code, 0)
        self.assertEqual(move_code, 0)
        print_shortcuts.assert_called_once_with()
        move_config.assert_called_once_with("D:\\FRcmdShortcuts")

    def test_main_rejects_move_command_with_missing_or_extra_path(self):
        with mock.patch.object(frcmd, "launch_many") as launch_many:
            missing_code = frcmd.main(["-m"])
            extra_code = frcmd.main(["-m", "D:\\One", "D:\\Two"])

        self.assertEqual(missing_code, 1)
        self.assertEqual(extra_code, 1)
        launch_many.assert_not_called()

    def test_main_rejects_unknown_option(self):
        with mock.patch.object(frcmd, "launch_many") as launch_many:
            code = frcmd.main(["-x"])

        self.assertEqual(code, 1)
        launch_many.assert_not_called()


class LaunchManyTests(unittest.TestCase):
    def test_launch_many_continues_after_missing_query(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "QQ.lnk").write_text("", encoding="utf-8")

            with mock.patch.object(frcmd, "ensure_configured", return_value=root), mock.patch.dict(
                os.environ, {"FRCMD_DRY_RUN": "1"}
            ):
                code = frcmd.launch_many(["missing", "qq"])

        self.assertEqual(code, 1)

    def test_launch_many_scans_when_config_dir_is_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def create_shortcut(_shortcut_dir):
                (root / "QQ.lnk").write_text("", encoding="utf-8")
                return (1, 0)

            with mock.patch.object(frcmd, "ensure_configured", return_value=root), mock.patch.object(
                frcmd, "transfer_shortcuts", side_effect=create_shortcut
            ), mock.patch.dict(os.environ, {"FRCMD_DRY_RUN": "1"}):
                code = frcmd.launch_many(["qq"])

        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
