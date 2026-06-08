from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

BOT_MODULES = (
    "altair_bot",
    "cephei_bot",
    "cygnus_bot",
    "draco_bot",
    "hydra_bot",
    "procryon_bot",
    "rhea_bot",
    "triton_bot",
    "vega_bot",
)


def test_bot_modules_migrated_to_import_safe_package():
    for module_name in BOT_MODULES:
        migrated_path = REPO_ROOT / "bentley_bot" / "bots" / f"{module_name}.py"
        shim_path = REPO_ROOT / f"{module_name}.py"

        assert migrated_path.is_file(), f"Missing migrated file: {migrated_path}"
        assert shim_path.is_file(), f"Missing compatibility shim: {shim_path}"

        shim_source = shim_path.read_text(encoding="utf-8")
        assert f"from bentley_bot.bots.{module_name} import *" in shim_source
        assert f"runpy.run_module(\"bentley_bot.bots.{module_name}\"" in shim_source


def test_hyphenated_python_artifact_removed():
    wrong_path = REPO_ROOT / "bentley-bot" / "bots" / "altair_bot.py"
    assert not wrong_path.exists()


def test_bentley_bot_package_markers_exist():
    assert (REPO_ROOT / "bentley_bot" / "__init__.py").is_file()
    assert (REPO_ROOT / "bentley_bot" / "bots" / "__init__.py").is_file()
