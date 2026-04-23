# -*- coding: utf-8 -*-
import os
import sys
from types import SimpleNamespace

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from builder.builder_core import BuilderCore  # noqa: E402


class TestBuilderCoreSigning:
    def test_sign_output_skips_when_disabled(self, monkeypatch, tmp_path):
        core = BuilderCore()
        exe_path = tmp_path / "output.exe"
        exe_path.write_text("stub", encoding="utf-8")

        called = False

        def fake_run(*args, **kwargs):
            nonlocal called
            called = True
            return SimpleNamespace(returncode=0, stdout="")

        monkeypatch.setattr("builder.builder_core.subprocess.run", fake_run)
        core._sign_output(str(exe_path), {"enable_signing": False})

        assert called is False

    def test_sign_output_runs_sign_and_verify(self, monkeypatch, tmp_path):
        core = BuilderCore()
        exe_path = tmp_path / "output.exe"
        cert_path = tmp_path / "cert.pfx"
        exe_path.write_text("stub", encoding="utf-8")
        cert_path.write_text("cert", encoding="utf-8")

        commands = []

        def fake_run(cmd, **kwargs):
            commands.append(cmd)
            return SimpleNamespace(returncode=0, stdout="ok")

        monkeypatch.setattr(core, "_resolve_signtool_path", lambda _: "signtool.exe")
        monkeypatch.setattr("builder.builder_core.subprocess.run", fake_run)

        core._sign_output(
            str(exe_path),
            {
                "enable_signing": True,
                "signing_cert_path": str(cert_path),
                "signing_password": "secret",
                "timestamp_url": "http://timestamp.digicert.com",
            },
        )

        assert len(commands) == 2
        assert commands[0][:6] == ["signtool.exe", "sign", "/fd", "SHA256", "/f", str(cert_path)]
        assert "/p" in commands[0]
        assert "secret" in commands[0]
        assert "/tr" in commands[0]
        assert "http://timestamp.digicert.com" in commands[0]
        assert commands[0][-1] == str(exe_path)
        assert commands[1] == ["signtool.exe", "verify", "/pa", str(exe_path)]
