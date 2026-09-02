"""Checks PyPI for newer MedPerf releases, and applies them for the Web UI."""

import importlib.metadata as importlib_metadata
import json
import logging
import os
import shlex
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import requests
from packaging.version import Version

import medperf.config as config
from medperf.exceptions import (
    EditableInstallUpdateError,
    ExecutionError,
    UpdateNotNeededError,
)


class UpdateManager:
    PYPI_PACKAGE_NAME = "medperf"
    PYPI_JSON_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
    PYPI_REQUEST_TIMEOUT = 5
    UPDATE_COMMAND = f"pip install -U {PYPI_PACKAGE_NAME}"
    EDITABLE_UPDATE_COMMAND = "git pull"

    def get_installed_version(self) -> str:
        """Return the version of the MedPerf code currently running."""
        from medperf import __version__

        return __version__

    def is_editable_install(self) -> bool:
        """Return True if the running `medperf` package is an editable/dev install
        (e.g. `pip install -e .`), where `pip install -U` would silently replace
        the dev checkout with a regular PyPI install instead of updating it."""
        try:
            dist = importlib_metadata.distribution(self.PYPI_PACKAGE_NAME)
            direct_url_text = dist.read_text("direct_url.json")
        except importlib_metadata.PackageNotFoundError:
            return False
        if not direct_url_text:
            return False
        try:
            direct_url = json.loads(direct_url_text)
        except json.JSONDecodeError:
            return False
        return bool(direct_url.get("dir_info", {}).get("editable", False))

    def update_command_for(self, editable: bool) -> str:
        return self.EDITABLE_UPDATE_COMMAND if editable else self.UPDATE_COMMAND

    def get_latest_version(self) -> Optional[str]:
        """Return the latest MedPerf version published on PyPI, if available."""
        try:
            response = requests.get(
                self.PYPI_JSON_URL, timeout=self.PYPI_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()["info"]["version"]
        except Exception as exc:
            logging.debug("Could not fetch latest MedPerf version from PyPI: %s", exc)
            return None

    @staticmethod
    def is_update_available(
        current_version: str, latest_version: Optional[str]
    ) -> bool:
        if latest_version is None:
            return False
        try:
            # PyPI versions follow PEP 440 (e.g. "0.3.0rc1", "0.3.0.post1"),
            # which semver.VersionInfo.parse rejects outright.
            current = Version(current_version)
            latest = Version(latest_version)
        except ValueError as exc:
            logging.debug("Could not compare MedPerf versions: %s", exc)
            return False
        return latest > current

    @staticmethod
    def _update_cache_path() -> Path:
        return Path(config.update_check_cache_file)

    @staticmethod
    def _update_cache_is_fresh(cached: dict) -> bool:
        checked_at = cached.get("checked_at")
        if not checked_at:
            return False
        try:
            parsed_checked_at = datetime.fromisoformat(checked_at)
            age_seconds = (
                datetime.now(timezone.utc) - parsed_checked_at
            ).total_seconds()
        except (ValueError, TypeError) as exc:
            logging.debug("Could not parse MedPerf update check cache age: %s", exc)
            return False
        return age_seconds < config.webui_update_check_interval_seconds

    @staticmethod
    def _read_update_cache(cache_path: Path) -> Optional[dict]:
        try:
            with open(cache_path) as cache_file:
                cached = json.load(cache_file)
        except (OSError, json.JSONDecodeError, TypeError):
            return None
        return cached

    @staticmethod
    def _write_update_cache(cache_path: Path, info: dict) -> None:
        try:
            with open(cache_path, "w") as cache_file:
                json.dump(info, cache_file)
        except (OSError, TypeError) as exc:
            logging.debug("Could not write MedPerf update check cache: %s", exc)

    def _sync_cache_with_installed(self, cached: dict, installed_version: str) -> dict:
        """Update cached fields that depend on the currently installed version."""
        info = dict(cached)
        latest_version = info.get("latest_version")
        info["current_version"] = installed_version
        info["update_available"] = self.is_update_available(
            installed_version, latest_version
        )
        editable = self.is_editable_install()
        info["is_editable_install"] = editable
        info["update_command"] = self.update_command_for(editable)
        return info

    def _make_update_info(
        self,
        current_version: str,
        latest_version: Optional[str],
        check_ok: Optional[bool] = None,
    ) -> dict:
        editable = self.is_editable_install()
        return {
            "update_available": self.is_update_available(
                current_version, latest_version
            ),
            "current_version": current_version,
            "latest_version": latest_version,
            "update_command": self.update_command_for(editable),
            "is_editable_install": editable,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "check_ok": latest_version is not None if check_ok is None else check_ok,
        }

    def get_update_info(self, force_refresh: bool = False) -> dict:
        """Return cached update metadata, refreshing when the cache expires."""
        installed_version = self.get_installed_version()
        cache_path = self._update_cache_path()
        cached = None if force_refresh else self._read_update_cache(cache_path)

        if cached and self._update_cache_is_fresh(cached):
            return self._sync_cache_with_installed(cached, installed_version)

        latest_version = self.get_latest_version()
        check_ok = latest_version is not None
        if not check_ok and cached is not None:
            # Keep the last known release rather than reporting "unknown"
            latest_version = cached.get("latest_version")

        info = self._make_update_info(installed_version, latest_version, check_ok)
        # Cached even on failure, so an unreachable PyPI costs one request per
        # interval instead of one per command
        self._write_update_cache(cache_path, info)
        return info

    def format_update_check_message(self, info: dict) -> str:
        installed_version = info.get("current_version") or "unknown"
        latest_version = info.get("latest_version")
        editable_note = (
            " This is an editable (development) install - update it with "
            f"`{self.EDITABLE_UPDATE_COMMAND}`."
            if info.get("is_editable_install")
            else ""
        )

        if info.get("update_available") and latest_version:
            return (
                f"Update available: MedPerf {latest_version} "
                f"(you have {installed_version}).{editable_note}"
            )

        if not info.get("check_ok", True):
            return (
                f"Could not check for updates (PyPI unavailable). "
                f"Installed version: {installed_version}"
            )

        return f"MedPerf is up to date (version {installed_version})"

    def validate_update(
        self,
        latest_version: Optional[str],
        current_version: Optional[str] = None,
    ) -> str:
        """Return installed version if updating to latest_version is allowed."""
        installed_version = self.get_installed_version()
        if self.is_editable_install():
            raise EditableInstallUpdateError(
                "This is an editable (development) install of MedPerf; "
                f"`pip install -U` would replace it. Run `{self.EDITABLE_UPDATE_COMMAND}` "
                "in your MedPerf checkout instead."
            )

        target_version = (latest_version or "").strip() or None
        if not target_version:
            raise UpdateNotNeededError(
                f"MedPerf is already up to date (installed {installed_version})."
            )

        # Compare against installed package and the version the UI showed the user.
        versions_to_check = {installed_version}
        if current_version:
            versions_to_check.add(current_version.strip())

        if any(
            self.is_update_available(version, target_version)
            for version in versions_to_check
        ):
            return installed_version

        raise UpdateNotNeededError(
            f"MedPerf is already up to date (installed {installed_version})."
        )

    def check_for_updates(self) -> None:
        """Check PyPI for a newer MedPerf release than the installed client."""
        info = self.get_update_info()
        if not info.get("update_available"):
            logging.debug("MedPerf client is up to date with PyPI.")
            return

        config.ui.print_warning(
            f"MedPerf {info['latest_version']} is available "
            f"(you have {info['current_version']}). "
            f"Update with: {info['update_command']}"
        )

    @staticmethod
    def build_webui_restart_argv(port: int) -> List[str]:
        """Build argv to restart the Web UI in the current Python environment."""
        bin_dir = Path(sys.executable).resolve().parent
        executable = bin_dir / "medperf_webui"
        if executable.is_file():
            return [str(executable), "--port", str(port)]
        raise ExecutionError(
            f"Could not find medperf_webui next to Python executable ({sys.executable})"
        )

    def _run_pip_update(self) -> None:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            self.PYPI_PACKAGE_NAME,
        ]
        logging.info("Updating MedPerf with: %s", shlex.join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "pip update failed").strip()
            raise ExecutionError(detail)
        logging.info("MedPerf package updated successfully")

    def schedule_webui_update(self, port: int, app_state) -> None:
        """Run pip update in the background, then trigger a graceful restart."""

        def _run_update() -> None:
            try:
                self._run_pip_update()
                restart_argv = self.build_webui_restart_argv(port)
            except Exception as exc:
                logging.exception("MedPerf Web UI update failed: %s", exc)
                app_state.update_in_progress = False
                app_state.update_error = str(exc)
                return

            if app_state.task_running or config.running_containers:
                logging.error(
                    "A task or container started while updating MedPerf; "
                    "aborting the restart to avoid killing it."
                )
                app_state.update_in_progress = False
                app_state.update_error = (
                    "A task or container started before the restart could "
                    "proceed. MedPerf was updated but not restarted; please "
                    "restart it manually."
                )
                return

            from medperf.web_ui.auth import RESTART_TOKEN_ENV, security_token

            logging.info("Restarting Web UI: %s", shlex.join(restart_argv))
            # Hands the session token to the replacement process so the user's
            # browser stays logged in across the restart
            os.environ[RESTART_TOKEN_ENV] = security_token
            app_state.pending_restart_argv = restart_argv
            os.kill(os.getpid(), signal.SIGTERM)

        threading.Thread(target=_run_update, daemon=True, name="medperf-update").start()
