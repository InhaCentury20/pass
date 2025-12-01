from __future__ import annotations

import logging
import subprocess
import threading
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_SCRAPER_DIR = PROJECT_ROOT / "homepass-scraper"


class ScraperRunner:
    """Launches the Scrapy crawler in a background thread."""

    def __init__(self):
        self._lock = threading.Lock()
        self._is_running = False
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._is_running

    def start(self, start_board_id: Optional[int] = None, days_limit: Optional[int] = None) -> None:
        with self._lock:
            if self._is_running:
                raise RuntimeError("Scraper is already running")
            self._is_running = True

        thread = threading.Thread(
            target=self._run_scraper,
            kwargs={
                "start_board_id": start_board_id or settings.SCRAPER_START_BOARD_ID,
                "days_limit": days_limit or settings.SCRAPER_DAYS_LIMIT,
            },
            daemon=True,
        )
        thread.start()
        self._thread = thread

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _resolve_paths(self) -> tuple[Path, Path]:
        scraper_dir = Path(settings.SCRAPER_DIR or DEFAULT_SCRAPER_DIR).resolve()
        if not scraper_dir.exists():
            raise FileNotFoundError(f"Scraper directory not found: {scraper_dir}")

        if settings.SCRAPER_VENV_PYTHON:
            python_path = Path(settings.SCRAPER_VENV_PYTHON).expanduser()
        else:
            candidate = scraper_dir / "venv" / "bin" / "python"
            python_path = candidate if candidate.exists() else Path("python")

        return scraper_dir, python_path

    def _run_scraper(self, start_board_id: int, days_limit: int) -> None:
        try:
            scraper_dir, python_path = self._resolve_paths()
            self._run_soco_spider(scraper_dir, python_path, start_board_id, days_limit)
            self._run_lh_import(scraper_dir, python_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Scraper pipeline failed: %s", exc)
        finally:
            with self._lock:
                self._is_running = False

    def _run_soco_spider(self, scraper_dir: Path, python_path: Path, start_board_id: int, days_limit: int) -> None:
        cmd = [
            str(python_path),
            "-m",
            "scrapy",
            "crawl",
            "soco_board_spider",
            "-a",
            f"start_board_id={start_board_id}",
            "-a",
            f"days_limit={days_limit}",
        ]
        self._run_subprocess(cmd, scraper_dir, "SOCO spider")

    def _run_lh_import(self, scraper_dir: Path, python_path: Path) -> None:
        lh_script = scraper_dir / "Lh.py"
        if not lh_script.exists():
            logger.warning("LH importer script not found at %s; skipping", lh_script)
            return
        cmd = [str(python_path), str(lh_script)]
        self._run_subprocess(cmd, scraper_dir, "LH importer")

    def _run_subprocess(self, cmd: list[str], cwd: Path, label: str) -> None:
        logger.info("Starting %s: %s", label, " ".join(cmd))
        subprocess.run(cmd, cwd=str(cwd), check=True)
        logger.info("%s finished successfully", label)


scraper_runner = ScraperRunner()


