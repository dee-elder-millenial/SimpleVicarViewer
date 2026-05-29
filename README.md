# Simple VICAR Viewer

A very small Python desktop viewer for JPL VICAR image files, built around the [`rms-vicar`](https://github.com/SETI/rms-vicar) package.

This is meant to be simple on purpose: open a `.IMG`, `.VIC`, `.VICAR`, or other VICAR-format file, display the image, and show the VICAR label text.

## Features

- Opens local VICAR image files using `vicar.VicarImage`
- Displays 2-D images directly
- Handles multi-band / 3-D data by showing one band at a time
- Previous / next controls for moving through loadable VICAR files in the same folder
- Contrast controls using percentile stretch
- Grayscale and common matplotlib colormaps
- Shows basic image metadata and the raw VICAR label
- Can save the currently displayed view as PNG

## Installation

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python simple_vicar_viewer.py
```

Or open a file directly:

```bash
python simple_vicar_viewer.py path/to/image.img
```

## Controls

- `Open VICAR…`: choose a VICAR image file
- `Previous` / `Next`: load the previous or next loadable `.img`, `.vic`, or `.vicar` file in the same folder
- Left arrow / Right arrow: same as previous / next
- `Save PNG…`: save the currently displayed view

## Notes

The underlying `rms-vicar` package exposes VICAR image data as `vic.array` and `vic.array2d`. This viewer uses those arrays and does only light normalization for screen display.

If a file has more than one band, use the band selector at the bottom of the window.

## Project status

Tiny first pass. No drama. No database. No daemon. Just one file, a window, and some ancient spacecraft pixels trying their best.
