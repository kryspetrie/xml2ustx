"""OpenUtau launcher component tests."""
from __future__ import annotations

from pathlib import Path

from src.application import openutau_launcher


def _make_macos_app_bundle(root: Path, name: str = 'OpenUtau.app') -> Path:
    app_bundle = root / name
    executable = app_bundle / 'Contents' / 'MacOS' / 'OpenUtau'
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text('', encoding='utf-8')
    executable.chmod(0o755)
    return app_bundle


def test_resolve_prefers_explicit_path(tmp_path: Path) -> None:
    binary = tmp_path / 'OpenUtau'
    binary.write_text('', encoding='utf-8')
    binary.chmod(0o755)
    resolved = openutau_launcher.resolve_openutau_executable(str(binary))
    assert resolved == binary.resolve()


def test_resolve_skips_env_when_fallback_disabled(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / 'OpenUtau'
    binary.write_text('', encoding='utf-8')
    binary.chmod(0o755)
    monkeypatch.setenv(openutau_launcher.OPENUTAU_PATH_ENV, str(binary))

    assert openutau_launcher.resolve_openutau_executable(allow_env_fallback=False) is None
    assert openutau_launcher.resolve_openutau_executable(
        str(binary),
        allow_env_fallback=False,
    ) == binary.resolve()


def test_resolve_uses_openutau_path_env(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / 'OpenUtau'
    binary.write_text('', encoding='utf-8')
    binary.chmod(0o755)
    monkeypatch.setenv(openutau_launcher.OPENUTAU_PATH_ENV, str(binary))
    assert openutau_launcher.resolve_openutau_executable() == binary.resolve()


def test_open_in_openutau_reports_missing_binary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(openutau_launcher.OPENUTAU_PATH_ENV, raising=False)
    monkeypatch.setattr(openutau_launcher.shutil, 'which', lambda _name: None)
    ustx = tmp_path / 'song.ustx'
    ustx.write_text('name: test\n', encoding='utf-8')
    messages: list[str] = []

    opened = openutau_launcher.open_in_openutau([str(ustx)], log_fn=messages.append)

    assert opened is False
    assert any('Could not find OpenUtau' in line for line in messages)


def test_is_valid_openutau_path_accepts_macos_app_bundle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(openutau_launcher.sys, 'platform', 'darwin')
    app_bundle = _make_macos_app_bundle(tmp_path)

    assert openutau_launcher.is_valid_openutau_path(str(app_bundle)) is True


def test_resolve_macos_app_bundle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(openutau_launcher.sys, 'platform', 'darwin')
    app_bundle = _make_macos_app_bundle(tmp_path)

    resolved = openutau_launcher.resolve_openutau_executable(
        str(app_bundle),
        allow_env_fallback=False,
    )

    assert resolved == (app_bundle / 'Contents' / 'MacOS' / 'OpenUtau').resolve()


def test_openutau_launch_command_uses_open_for_macos_app(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(openutau_launcher.sys, 'platform', 'darwin')
    app_bundle = _make_macos_app_bundle(tmp_path)
    ustx = tmp_path / 'song.ustx'
    ustx.write_text('name: test\n', encoding='utf-8')

    command = openutau_launcher.openutau_launch_command(str(app_bundle), ustx)

    assert command == ['open', '-a', str(app_bundle.resolve()), str(ustx.resolve())]


def test_open_in_openutau_launches_macos_app_bundle(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(openutau_launcher.sys, 'platform', 'darwin')
    app_bundle = _make_macos_app_bundle(tmp_path)
    launched: list[list[str]] = []

    def fake_popen(args, **kwargs):
        launched.append(args)
        return object()

    monkeypatch.setattr(openutau_launcher.subprocess, 'Popen', fake_popen)

    ustx = tmp_path / 'song.ustx'
    ustx.write_text('name: test\n', encoding='utf-8')
    assert openutau_launcher.open_in_openutau(
        [str(ustx)],
        openutau_path=str(app_bundle),
        allow_env_fallback=False,
    ) is True
    assert launched == [['open', '-a', str(app_bundle.resolve()), str(ustx.resolve())]]


def test_open_in_openutau_launches_when_found(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / 'OpenUtau'
    binary.write_text('', encoding='utf-8')
    binary.chmod(0o755)
    monkeypatch.setenv(openutau_launcher.OPENUTAU_PATH_ENV, str(binary))

    launched: list[list[str]] = []

    def fake_popen(args, **kwargs):
        launched.append(args)
        return object()

    monkeypatch.setattr(openutau_launcher.subprocess, 'Popen', fake_popen)

    ustx = tmp_path / 'song.ustx'
    ustx.write_text('name: test\n', encoding='utf-8')
    assert openutau_launcher.open_in_openutau([str(ustx)]) is True
    assert launched == [[str(binary.resolve()), str(ustx.resolve())]]
