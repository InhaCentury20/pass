from __future__ import annotations

import logging
import subprocess
import threading
import time
from datetime import datetime
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
        logger.info("=" * 80)
        logger.info("🚀 Scraper Runner 시작 요청")
        logger.info(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   파라미터: start_board_id={start_board_id}, days_limit={days_limit}")
        
        with self._lock:
            if self._is_running:
                logger.warning("⚠️ 이미 실행 중인 스크래퍼가 있습니다.")
                raise RuntimeError("Scraper is already running")
            self._is_running = True
            logger.info("✅ 스크래퍼 시작 가능 (잠금 획득)")

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
        logger.info(f"🧵 백그라운드 스레드 시작됨 (Thread ID: {thread.ident})")
        logger.info("=" * 80)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _resolve_paths(self) -> tuple[Path, Path]:
        logger.info("📁 경로 확인 중...")
        
        scraper_dir = Path(settings.SCRAPER_DIR or DEFAULT_SCRAPER_DIR).resolve()
        logger.info(f"   스크래퍼 디렉토리: {scraper_dir}")
        
        if not scraper_dir.exists():
            logger.error(f"❌ 스크래퍼 디렉토리를 찾을 수 없음: {scraper_dir}")
            raise FileNotFoundError(f"Scraper directory not found: {scraper_dir}")
        logger.info(f"   ✅ 스크래퍼 디렉토리 확인됨")

        if settings.SCRAPER_VENV_PYTHON:
            python_path = Path(settings.SCRAPER_VENV_PYTHON).expanduser()
        else:
            candidate = scraper_dir / "venv" / "bin" / "python"
            python_path = candidate if candidate.exists() else Path("python")
        
        logger.info(f"   Python 경로: {python_path}")
        logger.info(f"   Python 존재 여부: {python_path.exists() if python_path != Path('python') else 'system python'}")

        return scraper_dir, python_path

    def _run_scraper(self, start_board_id: int, days_limit: int) -> None:
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("🔧 Scraper Pipeline 실행 시작")
        logger.info(f"   start_board_id: {start_board_id}")
        logger.info(f"   days_limit: {days_limit}")
        logger.info("=" * 80)
        
        try:
            scraper_dir, python_path = self._resolve_paths()
            
            # Step 1: SOCO Spider
            logger.info("=" * 80)
            logger.info("📡 [1/2] SOCO Spider 실행")
            logger.info("=" * 80)
            step1_start = time.time()
            self._run_soco_spider(scraper_dir, python_path, start_board_id, days_limit)
            step1_elapsed = time.time() - step1_start
            logger.info(f"✅ [1/2] SOCO Spider 완료 (소요 시간: {step1_elapsed:.2f}초)")
            
            # LH importer는 제외 (사용자 요청으로 실행하지 않음)
            # self._run_lh_import(scraper_dir, python_path)
            
            # Step 2: Extractor
            logger.info("=" * 80)
            logger.info("🔬 [2/2] New Extractor 실행")
            logger.info("=" * 80)
            step2_start = time.time()
            self._run_extractor(scraper_dir, python_path)
            step2_elapsed = time.time() - step2_start
            logger.info(f"✅ [2/2] New Extractor 완료 (소요 시간: {step2_elapsed:.2f}초)")
            
            total_elapsed = time.time() - start_time
            logger.info("=" * 80)
            logger.info("🎉 Scraper Pipeline 전체 완료!")
            logger.info(f"   총 소요 시간: {total_elapsed:.2f}초")
            logger.info(f"   종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - start_time
            logger.error("=" * 80)
            logger.exception("💥 Scraper pipeline failed (소요 시간: %.2f초): %s", elapsed, exc)
            logger.error("=" * 80)
        finally:
            with self._lock:
                self._is_running = False
                logger.info("🔓 스크래퍼 잠금 해제됨")

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

    def _run_extractor(self, scraper_dir: Path, python_path: Path) -> None:
        extractor_script = scraper_dir / "new_extractor.py"
        logger.info(f"📄 Extractor 스크립트 경로: {extractor_script}")
        
        if not extractor_script.exists():
            logger.warning("⚠️ Extractor script not found at %s; skipping", extractor_script)
            return
        
        logger.info("✅ Extractor 스크립트 확인됨")
        cmd = [str(python_path), str(extractor_script)]
        self._run_subprocess(cmd, scraper_dir, "New extractor")

    def _run_subprocess(self, cmd: list[str], cwd: Path, label: str) -> None:
        logger.info("-" * 80)
        logger.info(f"▶️  {label} 시작")
        logger.info(f"   작업 디렉토리: {cwd}")
        logger.info(f"   실행 명령어: {' '.join(cmd)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, 
                cwd=str(cwd), 
                check=True,
                capture_output=True,
                text=True
            )
            elapsed = time.time() - start_time
            
            logger.info("-" * 80)
            logger.info(f"✅ {label} 성공 (소요 시간: {elapsed:.2f}초)")
            
            # stdout 출력 (new_extractor.py의 로그)
            if result.stdout:
                logger.info(f"📝 {label} 출력:")
                for line in result.stdout.splitlines():
                    logger.info(f"   {line}")
            
            # stderr가 있으면 경고로 출력
            if result.stderr:
                logger.warning(f"⚠️ {label} 경고/에러 출력:")
                for line in result.stderr.splitlines():
                    logger.warning(f"   {line}")
            
            logger.info("-" * 80)
            
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            logger.error("-" * 80)
            logger.error(f"❌ {label} 실패 (소요 시간: {elapsed:.2f}초)")
            logger.error(f"   종료 코드: {e.returncode}")
            
            if e.stdout:
                logger.error(f"   표준 출력:")
                for line in e.stdout.splitlines():
                    logger.error(f"      {line}")
            
            if e.stderr:
                logger.error(f"   에러 출력:")
                for line in e.stderr.splitlines():
                    logger.error(f"      {line}")
            
            logger.error("-" * 80)
            raise


scraper_runner = ScraperRunner()


