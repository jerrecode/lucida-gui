"""Validate a real Qt window instantiation with a headless platform plugin."""
import importlib.util
import os
import subprocess
import sys
import pytest

@pytest.mark.skipif(importlib.util.find_spec("PySide6") is None, reason="PySide6 unavailable in local environment")
def test_qt_offscreen_launch(tmp_path):
    env = os.environ.copy()
    env.update({"QT_QPA_PLATFORM": "offscreen", "LUCIDA_HOME": str(tmp_path / "state"),
                "LUCIDA_OUTPUT_DIR": str(tmp_path / "music")})
    run = subprocess.run([sys.executable, "-m", "lucida_gui.app", "--smoke"],
                         env=env, capture_output=True, text=True, timeout=25)
    assert run.returncode == 0, run.stderr
