from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LATEX_DIR = ROOT / "latex"
PDF_DIR = ROOT / "pdf"
LOCAL_TECTONIC_CANDIDATES = [
    Path.home() / ".local" / "bin" / "tectonic",
    ROOT.parent.parent / ".local" / "bin" / "tectonic",
]

DOCS = [
    ("knowledge-graph-report.md", "Knowledge Graph Report"),
    ("completion-analysis.md", "Knowledge Graph Completion Analysis"),
    ("prompt-documentation.md", "Prompt Documentation"),
]


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    raise FileNotFoundError(f"Could not find required binary: {name}")


def get_pandoc_path() -> str:
    try:
        import pypandoc
    except ImportError as exc:
        raise RuntimeError(
            "pypandoc-binary is required. Install with `python3 -m pip install --user pypandoc-binary`."
        ) from exc
    return pypandoc.get_pandoc_path()


def get_tectonic_path() -> str:
    for candidate in LOCAL_TECTONIC_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    system_path = shutil.which("tectonic")
    if system_path:
        return system_path
    raise FileNotFoundError(
        "Could not find tectonic. Expected a user-local or repo-local binary, or a system installation."
    )


def run_command(args: list[str]) -> None:
    completed = subprocess.run(args, check=False, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(args)}")


def render_document(pandoc: str, tectonic: str, filename: str, title: str) -> None:
    source = ROOT / filename
    stem = source.stem
    latex_path = LATEX_DIR / f"{stem}.tex"
    pdf_path = PDF_DIR / f"{stem}.pdf"

    base_args = [
        pandoc,
        str(source),
        "--from=gfm",
        "--standalone",
        f"--metadata=title:{title}",
        "-V",
        "geometry:margin=1in",
        "-V",
        "fontsize=11pt",
        "-V",
        "papersize:a4",
    ]

    run_command(base_args + ["--to=latex", "-o", str(latex_path)])
    run_command(base_args + [f"--pdf-engine={tectonic}", "-o", str(pdf_path)])


def main() -> int:
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    pandoc = get_pandoc_path()
    tectonic = get_tectonic_path()

    for filename, title in DOCS:
        render_document(pandoc, tectonic, filename, title)

    print(f"Rendered {len(DOCS)} documents to {LATEX_DIR} and {PDF_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
