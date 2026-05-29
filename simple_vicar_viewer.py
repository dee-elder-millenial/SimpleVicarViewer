"""Simple VICAR Viewer.

A tiny desktop viewer for VICAR images using SETI/rms-vicar.

Run:
    python simple_vicar_viewer.py

Or:
    python simple_vicar_viewer.py path/to/image.img
"""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import numpy as np
from PIL import Image, ImageTk

try:
    # rms-vicar installs/imports as `vicar`.
    import vicar  # type: ignore
except ImportError as exc:  # pragma: no cover - handled at runtime for users
    raise SystemExit(
        "Could not import the VICAR package. Install dependencies with:\n"
        "\n    pip install -r requirements.txt\n"
        "\nThe package used here is SETI/rms-vicar."
    ) from exc


DEFAULT_CMAPS = ("gray", "viridis", "plasma", "inferno", "magma", "cividis")


class SimpleVicarViewer(tk.Tk):
    """A deliberately small Tkinter VICAR image viewer."""

    def __init__(self, initial_file: str | None = None) -> None:
        super().__init__()
        self.title("Simple VICAR Viewer")
        self.geometry("1100x760")
        self.minsize(760, 520)

        self.current_path: Path | None = None
        self.vicar_image: Any | None = None
        self.data: np.ndarray | None = None
        self.band_count = 1
        self.display_photo: ImageTk.PhotoImage | None = None
        self.display_pil: Image.Image | None = None

        self.low_percentile = tk.DoubleVar(value=1.0)
        self.high_percentile = tk.DoubleVar(value=99.0)
        self.band_index = tk.IntVar(value=0)
        self.colormap_name = tk.StringVar(value="gray")
        self.status_text = tk.StringVar(value="Open a VICAR image to begin.")
        self.metadata_text = tk.StringVar(value="No image loaded.")

        self._build_ui()

        if initial_file:
            self.load_file(Path(initial_file))

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(8, weight=1)

        ttk.Button(toolbar, text="Open VICAR…", command=self.open_file).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(toolbar, text="Save PNG…", command=self.save_png).grid(row=0, column=1, padx=(0, 16))

        ttk.Label(toolbar, text="Low %").grid(row=0, column=2)
        ttk.Spinbox(toolbar, from_=0, to=49, increment=0.5, textvariable=self.low_percentile, width=6, command=self.refresh_image).grid(row=0, column=3, padx=(4, 10))

        ttk.Label(toolbar, text="High %").grid(row=0, column=4)
        ttk.Spinbox(toolbar, from_=51, to=100, increment=0.5, textvariable=self.high_percentile, width=6, command=self.refresh_image).grid(row=0, column=5, padx=(4, 10))

        ttk.Label(toolbar, text="Colormap").grid(row=0, column=6)
        cmap_box = ttk.Combobox(toolbar, textvariable=self.colormap_name, values=DEFAULT_CMAPS, width=10, state="readonly")
        cmap_box.grid(row=0, column=7, padx=(4, 10))
        cmap_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_image())

        ttk.Button(toolbar, text="Reset stretch", command=self.reset_stretch).grid(row=0, column=9)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew")

        image_frame = ttk.Frame(body, padding=(8, 8))
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        body.add(image_frame, weight=4)

        self.canvas = tk.Canvas(image_frame, background="#222222", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self.refresh_image())

        info_frame = ttk.Frame(body, padding=(8, 8))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(3, weight=1)
        body.add(info_frame, weight=1)

        ttk.Label(info_frame, text="Image Info", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(info_frame, textvariable=self.metadata_text, justify="left", wraplength=330).grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Label(info_frame, text="VICAR Label", font=("TkDefaultFont", 10, "bold")).grid(row=2, column=0, sticky="nw")
        self.label_box = tk.Text(info_frame, height=20, wrap="word")
        self.label_box.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
        self.label_box.insert("1.0", "No label loaded.")
        self.label_box.configure(state="disabled")

        bottom = ttk.Frame(self, padding=(8, 4))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(4, weight=1)

        ttk.Label(bottom, text="Band").grid(row=0, column=0, padx=(0, 4))
        self.band_spin = ttk.Spinbox(bottom, from_=0, to=0, textvariable=self.band_index, width=6, command=self.refresh_image, state="disabled")
        self.band_spin.grid(row=0, column=1, padx=(0, 16))
        ttk.Label(bottom, textvariable=self.status_text).grid(row=0, column=2, sticky="w")

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Open VICAR image",
            filetypes=(("VICAR images", "*.img *.IMG *.vic *.VIC *.vicar *.VICAR"), ("All files", "*.*")),
        )
        if filename:
            self.load_file(Path(filename))

    def load_file(self, path: Path) -> None:
        try:
            vic = vicar.VicarImage(str(path))
            data = self._extract_array(vic)
        except Exception as exc:  # noqa: BLE001 - user-facing GUI error
            messagebox.showerror("Could not open VICAR image", f"{path}\n\n{exc}")
            return

        self.current_path = path
        self.vicar_image = vic
        self.data = data
        self.band_count = self._guess_band_count(data)
        self.band_index.set(0)

        if self.band_count > 1:
            self.band_spin.configure(state="normal", from_=0, to=self.band_count - 1)
        else:
            self.band_spin.configure(state="disabled", from_=0, to=0)

        self.title(f"Simple VICAR Viewer — {path.name}")
        self._update_metadata()
        self._update_label_box()
        self.refresh_image()

    def _extract_array(self, vic: Any) -> np.ndarray:
        """Return the most useful numpy array exposed by rms-vicar."""
        for attr in ("array2d", "array"):
            if hasattr(vic, attr):
                value = getattr(vic, attr)
                if value is not None:
                    arr = np.asarray(value)
                    if arr.size:
                        return arr
        raise ValueError("No image array found on VicarImage object.")

    def _guess_band_count(self, data: np.ndarray) -> int:
        if data.ndim < 3:
            return 1
        return int(data.shape[0])

    def _current_plane(self) -> np.ndarray:
        if self.data is None:
            raise ValueError("No image loaded.")

        arr = np.asarray(self.data)
        if arr.ndim == 2:
            return arr

        if arr.ndim == 3:
            idx = max(0, min(int(self.band_index.get()), arr.shape[0] - 1))
            return arr[idx, :, :]

        squeezed = np.squeeze(arr)
        if squeezed.ndim == 2:
            return squeezed
        if squeezed.ndim == 3:
            idx = max(0, min(int(self.band_index.get()), squeezed.shape[0] - 1))
            return squeezed[idx, :, :]
        raise ValueError(f"Unsupported image array shape: {arr.shape}")

    def reset_stretch(self) -> None:
        self.low_percentile.set(1.0)
        self.high_percentile.set(99.0)
        self.refresh_image()

    def refresh_image(self) -> None:
        if self.data is None:
            return

        try:
            plane = self._current_plane().astype(float)
            image = self._plane_to_pil(plane)
        except Exception as exc:  # noqa: BLE001 - user-facing status
            self.status_text.set(f"Display error: {exc}")
            return

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        image.thumbnail((width, height), Image.Resampling.LANCZOS)

        self.display_pil = image.copy()
        self.display_photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        self.canvas.create_image(x, y, anchor="nw", image=self.display_photo)

        band_note = f" band {self.band_index.get()}" if self.band_count > 1 else ""
        self.status_text.set(f"Showing {self.current_path.name if self.current_path else 'image'}{band_note}")

    def _plane_to_pil(self, plane: np.ndarray) -> Image.Image:
        finite = np.isfinite(plane)
        if not finite.any():
            normalized = np.zeros_like(plane, dtype=float)
        else:
            low = float(self.low_percentile.get())
            high = float(self.high_percentile.get())
            if low >= high:
                low, high = 1.0, 99.0
            vmin, vmax = np.nanpercentile(plane[finite], [low, high])
            if np.isclose(vmin, vmax):
                normalized = np.zeros_like(plane, dtype=float)
            else:
                normalized = (plane - vmin) / (vmax - vmin)
                normalized = np.clip(normalized, 0.0, 1.0)
                normalized[~finite] = 0.0

        cmap_name = self.colormap_name.get()
        if cmap_name == "gray":
            pixels = (normalized * 255).astype(np.uint8)
            return Image.fromarray(pixels, mode="L").convert("RGB")

        try:
            import matplotlib.colormaps as colormaps

            cmap = colormaps[cmap_name]
            rgba = (cmap(normalized) * 255).astype(np.uint8)
            return Image.fromarray(rgba, mode="RGBA").convert("RGB")
        except Exception:
            pixels = (normalized * 255).astype(np.uint8)
            return Image.fromarray(pixels, mode="L").convert("RGB")

    def _update_metadata(self) -> None:
        if self.data is None or self.current_path is None:
            return
        arr = np.asarray(self.data)
        dtype = arr.dtype
        shape = arr.shape
        try:
            size_mb = self.current_path.stat().st_size / (1024 * 1024)
            size_line = f"Size: {size_mb:.2f} MB"
        except OSError:
            size_line = "Size: unknown"

        lines = [
            f"File: {self.current_path.name}",
            f"Path: {self.current_path.parent}",
            f"Shape: {shape}",
            f"Dtype: {dtype}",
            f"Bands: {self.band_count}",
            size_line,
        ]
        self.metadata_text.set("\n".join(lines))

    def _update_label_box(self) -> None:
        label = self._label_text()
        self.label_box.configure(state="normal")
        self.label_box.delete("1.0", "end")
        self.label_box.insert("1.0", label)
        self.label_box.configure(state="disabled")

    def _label_text(self) -> str:
        if self.vicar_image is None:
            return "No label loaded."
        try:
            return str(self.vicar_image)
        except Exception:
            pass
        if hasattr(self.vicar_image, "label"):
            return str(getattr(self.vicar_image, "label"))
        return "No VICAR label text found on this image object."

    def save_png(self) -> None:
        if self.display_pil is None:
            messagebox.showinfo("Nothing to save", "Open an image first.")
            return

        default_name = "vicar_view.png"
        if self.current_path is not None:
            default_name = f"{self.current_path.stem}.png"

        filename = filedialog.asksaveasfilename(
            title="Save current view as PNG",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=(("PNG image", "*.png"), ("All files", "*.*")),
        )
        if filename:
            self.display_pil.save(filename)
            self.status_text.set(f"Saved {filename}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple VICAR image viewer.")
    parser.add_argument("file", nargs="?", help="Optional VICAR image file to open on launch.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    app = SimpleVicarViewer(args.file)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
