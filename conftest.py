# conftest.py
"""Global pytest configuration.

The project ships two Python environments on purpose:

* ``.venv``          -> CUDA build of PyTorch (GPU tests actually run)
* global ``python``  -> CPU-only build (GPU tests are skipped)

Run the suite through ``.venv`` (``scripts/runTests.ps1``) to execute the GPU
tests. Passing ``--require-gpu`` turns a silent skip into a hard failure so a
misconfigured interpreter never hides untested GPU code paths.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import torch

VENV_PYTHON = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the strict GPU option."""
    parser.addoption(
        "--require-gpu",
        action="store_true",
        default=False,
        help="Fail instead of skipping when CUDA is unavailable.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Refuse to skip GPU tests when they are explicitly required."""
    if config.getoption("--require-gpu") and not _cudaAvailable():
        raise pytest.UsageError(
            "CUDA is unavailable in this interpreter. Run the suite with "
            f"'{_interpreterHint()}' or drop --require-gpu."
        )


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Expose the PyTorch device used for this test session."""
    if _cudaAvailable():
        return [
            f"pytorch: {torch.__version__} (CUDA available, device 0: "
            f"{torch.cuda.get_device_name(0)})"
        ]
    return [f"pytorch: {torch.__version__} (CPU only - GPU tests will be skipped)"]


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """Explain how to run the GPU tests when they were skipped."""
    if _cudaAvailable() or os.getenv("RIAH_REQUIRE_GPU") == "1":
        return

    skipped = terminalreporter.stats.get("skipped", [])
    if not any("CUDA" in str(report.longrepr) for report in skipped):
        return

    if VENV_PYTHON.is_file():
        terminalreporter.write_sep(
            "-",
            "GPU tests skipped: rerun with .venv (scripts/runTests.ps1) to execute them",
        )


def _cudaAvailable() -> bool:
    """Return True when the active interpreter exposes a CUDA device."""
    return bool(torch.cuda.is_available())


def _interpreterHint() -> str:
    """Return the interpreter command expected to expose CUDA."""
    if VENV_PYTHON.is_file():
        return str(VENV_PYTHON)
    return sys.executable
