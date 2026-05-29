"""Inspect a VICAR file from the command line.

This is a no-GUI smoke test for checking whether rms-vicar can read a file.

Example on Windows PowerShell:
    python inspect_vicar.py "G:\My Drive\Sci Fi Story\Voyager Pics\data\voyager\VGISS_0004\PHOEBE\C4346108_RAW.IMG"
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import vicar  # type: ignore


def get_value(vic: Any, key: str, default: str = "unknown") -> Any:
    try:
        return vic.get(key, default)
    except Exception:
        return default


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a VICAR file without opening the GUI.")
    parser.add_argument("file", help="Path to a VICAR image file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    vic = vicar.VicarImage(str(path))
    arr = np.asarray(vic.array2d if getattr(vic, "array2d", None) is not None else vic.array)

    print(f"File: {path}")
    print(f"Shape: {arr.shape}")
    print(f"Dtype: {arr.dtype}")
    print(f"Min: {np.nanmin(arr)}")
    print(f"Max: {np.nanmax(arr)}")
    print(f"Mean: {np.nanmean(arr):.3f}")
    print()
    print("Selected VICAR label fields:")
    for key in ("LBLSIZE", "FORMAT", "TYPE", "ORG", "NL", "NS", "NB", "MISSION_NAME", "TARGET_NAME", "IMAGE_TIME"):
        print(f"  {key}: {get_value(vic, key)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
