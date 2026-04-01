import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_main_snippet(snippet: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "gbk"
    return subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_start_api_does_not_crash_with_gbk_stdout():
    result = _run_main_snippet(
        "import subprocess; import main; subprocess.run = lambda *args, **kwargs: None; main.start_api()"
    )

    assert result.returncode == 0, result.stderr


def test_agent_deprecation_message_does_not_crash_with_gbk_stdout():
    result = _run_main_snippet("import main; main.test_agent()")

    assert result.returncode == 0, result.stderr
