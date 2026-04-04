import os
import shutil
import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _prepare_temp_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "scripts").mkdir(parents=True)
    (project / "frontend").mkdir(parents=True)
    (project / ".venv" / "bin").mkdir(parents=True)
    (project / "frontend" / "node_modules").mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "start_project.sh", project / "start_project.sh")
    shutil.copy2(REPO_ROOT / "stop_project.sh", project / "stop_project.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "start_backend.sh", project / "scripts" / "start_backend.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "start_frontend.sh", project / "scripts" / "start_frontend.sh")

    python_proxy = project / ".venv" / "bin" / "python"
    python_proxy.write_text("#!/usr/bin/env bash\nexec python3 \"$@\"\n", encoding="utf-8")
    python_proxy.chmod(0o755)
    return project


def _prepare_fake_bin(tmp_path: Path) -> tuple[Path, Path]:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    capture_file = tmp_path / "capture.log"

    (fake_bin / "uv").write_text(
        "#!/usr/bin/env bash\n"
        "printf 'uv %s\\n' \"$*\" >> \"$CAPTURE_FILE\"\n",
        encoding="utf-8",
    )
    (fake_bin / "npm").write_text(
        "#!/usr/bin/env bash\n"
        "printf 'npm %s | proxy=%s\\n' \"$*\" \"${VITE_API_PROXY_TARGET:-}\" >> \"$CAPTURE_FILE\"\n",
        encoding="utf-8",
    )
    (fake_bin / "nohup").write_text(
        "#!/usr/bin/env bash\n"
        "printf 'nohup %s\\n' \"$*\" >> \"$CAPTURE_FILE\"\n",
        encoding="utf-8",
    )
    (fake_bin / "pkill").write_text(
        "#!/usr/bin/env bash\n"
        "printf 'pkill %s\\n' \"$*\" >> \"$CAPTURE_FILE\"\n",
        encoding="utf-8",
    )
    for path in fake_bin.iterdir():
        path.chmod(0o755)
    return fake_bin, capture_file


def test_start_backend_omits_reload_when_env_disables_it(tmp_path):
    project = _prepare_temp_project(tmp_path)
    fake_bin, capture_file = _prepare_fake_bin(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)
    env["MEAL_PLANNER_API_RELOAD"] = "0"

    result = subprocess.run(
        ["bash", str(project / "scripts" / "start_backend.sh"), "9123"],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    captured = capture_file.read_text(encoding="utf-8")
    assert "--port 9123" in captured
    assert "--reload" not in captured


def test_start_frontend_accepts_explicit_frontend_port_and_strict_port(tmp_path):
    project = _prepare_temp_project(tmp_path)
    fake_bin, capture_file = _prepare_fake_bin(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)

    result = subprocess.run(
        ["bash", str(project / "scripts" / "start_frontend.sh"), "9123", "5179"],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    captured = capture_file.read_text(encoding="utf-8")
    assert "proxy=http://127.0.0.1:9123" in captured
    assert "--port 5179" in captured
    assert "--strictPort" in captured


def test_start_project_passes_backend_and_frontend_ports_to_child_scripts(tmp_path):
    project = _prepare_temp_project(tmp_path)
    fake_bin, capture_file = _prepare_fake_bin(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)
    env["MEAL_PLANNER_API_PORT"] = "9123"
    env["MEAL_PLANNER_FRONTEND_PORT"] = "5179"

    result = subprocess.run(
        ["bash", str(project / "start_project.sh")],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Backend:  http://127.0.0.1:9123" in result.stdout
    assert "Frontend: http://127.0.0.1:5179" in result.stdout
    for _ in range(20):
        if capture_file.exists():
            break
        time.sleep(0.05)
    captured = capture_file.read_text(encoding="utf-8")
    assert "nohup" in captured
    assert "scripts/start_backend.sh 9123" in captured
    assert "scripts/start_frontend.sh 9123 5179" in captured


def test_stop_project_stops_processes_from_pidfiles(tmp_path):
    project = _prepare_temp_project(tmp_path)
    run_dir = project / ".run"
    run_dir.mkdir(parents=True)

    backend = subprocess.Popen(["sleep", "1000"])
    frontend = subprocess.Popen(["sleep", "1000"])
    (run_dir / "backend.pid").write_text(f"{backend.pid}\n", encoding="utf-8")
    (run_dir / "frontend.pid").write_text(f"{frontend.pid}\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(project / "stop_project.sh")],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    backend.wait(timeout=5)
    frontend.wait(timeout=5)
    assert (run_dir / "backend.pid").exists() is False
    assert (run_dir / "frontend.pid").exists() is False


def test_stop_project_falls_back_to_pattern_shutdown_without_pidfiles(tmp_path):
    project = _prepare_temp_project(tmp_path)
    fake_bin, capture_file = _prepare_fake_bin(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)

    result = subprocess.run(
        ["bash", str(project / "stop_project.sh")],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    captured = capture_file.read_text(encoding="utf-8")
    assert "pkill -f scripts/start_backend.sh" in captured
    assert "pkill -f scripts/start_frontend.sh" in captured


def test_stop_project_falls_back_when_pidfiles_are_stale(tmp_path):
    project = _prepare_temp_project(tmp_path)
    fake_bin, capture_file = _prepare_fake_bin(tmp_path)
    run_dir = project / ".run"
    run_dir.mkdir(parents=True)
    (run_dir / "backend.pid").write_text("999999\n", encoding="utf-8")
    (run_dir / "frontend.pid").write_text("999998\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)

    result = subprocess.run(
        ["bash", str(project / "stop_project.sh")],
        cwd=project,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    captured = capture_file.read_text(encoding="utf-8")
    assert "pkill -f scripts/start_backend.sh" in captured
    assert "pkill -f scripts/start_frontend.sh" in captured
