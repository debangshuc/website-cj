import json
import os
import subprocess
import sys
from pathlib import Path

# Configuration regression tests.

REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/tests/.. -> repo root
BACKEND_DIR = REPO_ROOT / "backend"         # where app/ and .env live
ENV_FILE_PATH = BACKEND_DIR / ".env"

APP_DIR = BACKEND_DIR / "app"


def test_env_file_is_anchored_to_backend_directory():
    """Settings.model_config must resolve to the absolute backend/.env path.

    Regression: env_file='.env' resolved relative to cwd, so starting uvicorn
    from the repository root silently used defaults (e.g. ADMIN_EMAILS
    allowlist) instead of backend/.env.
    """
    from app.core.config import Settings

    env_file = Settings.model_config.get("env_file")
    assert env_file is not None
    assert Path(env_file).is_absolute()
    assert Path(env_file) == ENV_FILE_PATH


def test_settings_load_from_anchored_env_file_in_distinct_cwd(tmp_path):
    """The application's real Settings() must load correctly from a working
    directory unrelated to the repository.

    Runs a subprocess with cwd set to this test's tmp directory (never the
    repo root or backend/) and asserts structural facts only:
    - the anchored env_file path is what the child resolves,
    - OS environment variables take precedence over the env file (sentinel
      injected through the child's environment),
    - configuration fields still parse to their declared types.

    No values from the real backend/.env are printed or asserted, so the
    test is CI-safe (works with or without a local .env) and never exposes
    secrets.
    """
    script = (
        "import json, sys\n"
        f"sys.path.insert(0, r'{BACKEND_DIR}')\n"
        "from app.core.config import Settings\n"
        "settings = Settings()\n"
        "env_file = Settings.model_config.get('env_file')\n"
        "print(json.dumps({\n"
        "    'env_file': str(env_file),\n"
        "    'audience': settings.SUPABASE_JWT_AUDIENCE,\n"
        "    'admin_emails_is_list': isinstance(settings.ADMIN_EMAILS, list),\n"
        "}))\n"
    )
    child_env = os.environ.copy()
    child_env["SUPABASE_JWT_AUDIENCE"] = "child-proc-audience"
    # Ensure no other test/developer process leaks a conflicting audience.
    child_env.pop("SUPABASE_AUDIENCE", None)

    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])

    resolved = Path(payload["env_file"])
    assert resolved.is_absolute()
    assert resolved == ENV_FILE_PATH
    assert payload["audience"] == "child-proc-audience"  # OS env > env file
    assert payload["admin_emails_is_list"] is True
    assert proc.stderr == ""


def test_admin_authorization_matches_allowlist_via_production_logic(monkeypatch):
    """Actual AuthenticatedUser.is_admin behavior: case/space-insensitive
    matching against ADMIN_EMAILS; empty allowlist grants nothing."""
    from app.core.security import AuthenticatedUser
    from app.core.config import settings

    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["allowlist-test-admin@example.com"])
    # Token email with different case and surrounding whitespace still matches.
    user = AuthenticatedUser(user_id="u1", email="  AllowList-Test-Admin@Example.COM ")
    assert user.is_admin is True

    # Allowlist entry stored in a different case still matches.
    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["ALLOWLIST-TEST-ADMIN@EXAMPLE.COM"])
    user = AuthenticatedUser(user_id="u2", email="allowlist-test-admin@example.com")
    assert user.is_admin is True

    # A user not on the allowlist is never an admin.
    user = AuthenticatedUser(user_id="u3", email="someoneelse@example.com")
    assert user.is_admin is False

    # An empty allowlist grants nothing — even a matching address.
    monkeypatch.setattr(settings, "ADMIN_EMAILS", [])
    user = AuthenticatedUser(user_id="u4", email="allowlist-test-admin@example.com")
    assert user.is_admin is False


def test_disposable_flag_is_not_an_application_setting():
    """INTEGRATION_DB_DISPOSABLE is a test-process-only contract.

    The flag may be legitimately present in whatever environment runs the
    integration tests (or absent entirely); this test verifies the application
    *configuration contract* instead of the ambient OS environment:
    - Settings exposes no such field,
    - no application module reads it directly.
    """
    from app.core.config import settings

    assert not hasattr(settings, "INTEGRATION_DB_DISPOSABLE")
    offenders = [
        str(p.relative_to(APP_DIR))
        for p in APP_DIR.rglob("*.py")
        if "INTEGRATION_DB_DISPOSABLE" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"Application code must not consume INTEGRATION_DB_DISPOSABLE: {offenders}"
