"""The Anki Miner mapping check skips only when anki_miner is absent; an API change fails the gate."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_anki_miner_mapping.py"


def run_check(pythonpath: Path) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(pythonpath)}
    return subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True)


def test_mapping_check_skips_only_when_anki_miner_is_missing(tmp_path):
    assert run_check(tmp_path).returncode == 2


def test_mapping_check_fails_when_anki_miner_api_moved(tmp_path):
    package = tmp_path / "anki_miner"
    (package / "languages").mkdir(parents=True)
    (package / "services").mkdir()
    (package / "__init__.py").write_text("")
    (package / "languages" / "__init__.py").write_text("AVAILABLE_LANGUAGES = ('de',)\n")
    (package / "languages" / "registry.py").write_text("def get_profile(code): ...\n")
    (package / "services" / "__init__.py").write_text("")
    (package / "services" / "note_presets.py").write_text("def fill_note_type_fields_v2(*a, **k): ...\n")
    result = run_check(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
