from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional, Union


JsonScalar = Optional[Union[str, int, float, bool]]
JsonObject = dict[str, JsonScalar]
CONVERSION_TIMEOUT_SECONDS: Final = 60


@dataclass(frozen=True)
class WaveformConversion:
    status: str
    source: Path
    path: Optional[Path] = None
    message: str = ""


def _rel(root: Path, path: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _cache_dir(fst_path: Path) -> Path:
    for parent in (fst_path.parent, *fst_path.parents):
        if parent.name == "sim":
            return parent / ".wave_cache"
    return fst_path.parent / ".wave_cache"


def _cache_path(root: Path, fst_path: Path) -> Path:
    rel = _rel(root, fst_path) or fst_path.as_posix()
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:12]
    return _cache_dir(fst_path) / f"{fst_path.stem}-{digest}.vcd"


def _fresh(cache: Path, source: Path) -> bool:
    return cache.is_file() and cache.stat().st_size > 0 and cache.stat().st_mtime >= source.stat().st_mtime


def ensure_vcd_for_fst(root: Path, fst_path: Path) -> WaveformConversion:
    converter = shutil.which("fst2vcd")
    if converter is None:
        return WaveformConversion(status="converter_missing", source=fst_path, message="fst2vcd not found in PATH")
    cache = _cache_path(root, fst_path)
    if _fresh(cache, fst_path):
        return WaveformConversion(status="cached", source=fst_path, path=cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=cache.parent,
            prefix=f".{cache.name}.",
            suffix=".tmp",
            delete=False,
        ) as out:
            tmp_path = Path(out.name)
            proc = subprocess.run(
                [converter, str(fst_path)],
                stdout=out,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                check=False,
                timeout=CONVERSION_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        return WaveformConversion(status="conversion_timeout", source=fst_path, message="fst2vcd timed out")
    except OSError as exc:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        return WaveformConversion(status="conversion_failed", source=fst_path, message=str(exc))
    if tmp_path is None:
        return WaveformConversion(status="conversion_failed", source=fst_path, message="temporary VCD path missing")
    if proc.returncode != 0:
        tmp_path.unlink(missing_ok=True)
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        return WaveformConversion(status="conversion_failed", source=fst_path, message=stderr)
    if not tmp_path.is_file() or tmp_path.stat().st_size == 0:
        tmp_path.unlink(missing_ok=True)
        return WaveformConversion(status="conversion_failed", source=fst_path, message="fst2vcd produced no VCD data")
    try:
        tmp_path.replace(cache)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        return WaveformConversion(status="conversion_failed", source=fst_path, message=str(exc))
    return WaveformConversion(status="converted", source=fst_path, path=cache)


def _vcd_entry(root: Path, path: Path, source: str, converted_from: Optional[Path] = None) -> Optional[JsonObject]:
    rel = _rel(root, path)
    if rel is None:
        return None
    st = path.stat()
    entry: JsonObject = {"path": rel, "size": st.st_size, "mtime": st.st_mtime, "source": source}
    if converted_from is not None:
        from_rel = _rel(root, converted_from)
        if from_rel is not None:
            entry["converted_from"] = from_rel
    return entry


def _error_entry(root: Path, conversion: WaveformConversion) -> JsonObject:
    return {
        "source": _rel(root, conversion.source) or conversion.source.as_posix(),
        "status": conversion.status,
        "message": conversion.message,
    }


def _visible(root: Path, path: Path, skip_dirs: set[str], max_depth: Optional[int]) -> bool:
    rel = _rel(root, path)
    if rel is None:
        return False
    parts = Path(rel).parts
    if ".wave_cache" in parts:
        return False
    if any(part in skip_dirs for part in parts):
        return False
    return max_depth is None or len(parts) <= max_depth


def list_waveform_vcd_entries(
    *,
    root: Path,
    base: Path,
    skip_dirs: set[str],
    recursive: bool,
    max_depth: Optional[int],
    convert_fst: bool,
) -> tuple[list[JsonObject], list[JsonObject]]:
    globber = base.rglob if recursive else base.glob
    entries: list[JsonObject] = []
    errors: list[JsonObject] = []
    seen: set[str] = set()
    fst_paths = [
        path
        for path in globber("*.fst")
        if convert_fst and path.is_file() and _visible(root, path, skip_dirs, max_depth)
    ]
    fst_by_sibling_vcd = {path.with_suffix(".vcd"): path for path in fst_paths}
    for path in globber("*.vcd"):
        if not path.is_file() or not _visible(root, path, skip_dirs, max_depth):
            continue
        sibling_fst = fst_by_sibling_vcd.get(path)
        if sibling_fst is not None and not _fresh(path, sibling_fst):
            continue
        entry = _vcd_entry(root, path, "native_vcd")
        if entry is not None and str(entry["path"]) not in seen:
            seen.add(str(entry["path"]))
            entries.append(entry)
    if convert_fst:
        for fst_path in fst_paths:
            sibling = fst_path.with_suffix(".vcd")
            if _fresh(sibling, fst_path):
                continue
            conversion = ensure_vcd_for_fst(root, fst_path)
            if conversion.path is None:
                errors.append(_error_entry(root, conversion))
                continue
            entry = _vcd_entry(root, conversion.path, "converted_fst", fst_path)
            if entry is not None and str(entry["path"]) not in seen:
                seen.add(str(entry["path"]))
                entries.append(entry)
    entries.sort(key=lambda item: float(item["mtime"] or 0), reverse=True)
    return entries, errors


def read_vcd_target(root: Path, target: Path) -> tuple[WaveformConversion, Optional[Path]]:
    suffix = target.suffix.lower()
    if suffix == ".vcd":
        return WaveformConversion(status="native_vcd", source=target, path=target), target
    if suffix == ".fst":
        conversion = ensure_vcd_for_fst(root, target)
        return conversion, conversion.path
    return WaveformConversion(status="unsupported_format", source=target, message="not a .vcd or .fst file"), None
