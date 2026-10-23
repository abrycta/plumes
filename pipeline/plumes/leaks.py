"""No build-machine details in published files (storage option A1): an absolute local path (macOS, Linux, a CI runner,
Windows) or an agent scratchpad name must never reach a published file, its metadata included.

Text files are scanned as they are. PMTiles keep their metadata gzip-compressed, so it is unpacked and scanned too
(tippecanoe writes its command line, with the input and output paths, into it). Other binary files (GeoTIFF tags,
JPEG EXIF) keep text metadata uncompressed and are scanned raw.

    uv run python -m plumes.leaks <folder>
"""

from __future__ import annotations

import gzip
import pathlib
import re
import struct
import sys
import zlib

# an absolute path with at least two segments, so random bytes in compressed tile data can't match by chance
PATH = re.compile(
    rb"(?<![\w.~-])/(?:private|Users|home|tmp|var/folders|opt/homebrew|root|mnt|srv|github/workspace|runner|__w)/[\w.@+~-]+/"
    rb"|\b[A-Za-z]:\\\\?(?:Users|Windows|a|actions-runner)\\"
    rb"|claude-\d+|-Users-[\w-]+-portfolio|\bclaude\b",
    re.IGNORECASE,
)


def pmtiles_metadata(data: bytes) -> bytes:
    """The decompressed JSON metadata of a PMTiles v3 file; b"" when the file is not one."""
    if len(data) < 127 or data[:7] != b"PMTiles" or data[7] != 3:
        return b""
    off, length = struct.unpack_from("<QQ", data, 24)
    raw = data[off:off + length]
    comp = data[97]
    try:
        if comp == 2:
            return gzip.decompress(raw)
        if comp in (0, 1):
            return raw
        return zlib.decompress(raw)
    except (OSError, zlib.error):
        return raw


def scan_bytes(data: bytes) -> list[str]:
    found = [m.group(0).decode("latin-1") for m in PATH.finditer(data)]
    if meta := pmtiles_metadata(data):
        found += [m.group(0).decode("latin-1") for m in PATH.finditer(meta)]
    return sorted(set(found))


def scan(root: pathlib.Path) -> dict[str, list[str]]:
    """{relative path: matches} for every file under `root` that names a local path; {} when clean."""
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and (hits := scan_bytes(p.read_bytes())):
            out[str(p.relative_to(root))] = hits
    return out


if __name__ == "__main__":
    bad = scan(pathlib.Path(sys.argv[1]))
    for k, v in bad.items():
        print(f"{k}: {', '.join(v[:3])}")
    print(f"{len(bad)} file(s) with a local path")
    sys.exit(1 if bad else 0)
