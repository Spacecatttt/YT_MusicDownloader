# 🎵 YT Music Downloader

**YT Music Downloader** is a desktop application for downloading audio tracks from YouTube playlists and renaming them using customizable templates.

---

## 🔧 Main Features

- ✅ Download entire YouTube playlists in `.m4a` format
- ✂️ Clean up and format filenames automatically
- 🧠 Rename using regex-based templates
- 📤 Import/export templates to/from file

---

## 🖥️ User Interface Overview

- **Download Tab**
  Paste a playlist URL → choose an output directory → click "Download".
  Files will be saved in the format `Artist - Track Name.m4a`.

- **Rename Tab**
  Select a folder → click "Scan" → see a table with suggested new names.
  Confirm renaming for selected files.

- **Templates Tab**
  Manage regex rename templates (Pattern → Replacement).
  Import or export templates to file via dropdown menu.

---

## 🧩 Requirements

- Python 3.9+
- `PySide6`
- `yt-dlp`
- `ffmpeg` (must be in your system PATH)

Install dependencies:

```bash
pip install -r requirements.txt
```


## 📝 Sample Rename Templates

| Pattern         | Replacement | Description                        |
|-----------------|-------------|------------------------------------|
| `\s*\(.*?\)`    | `""`        | Removes text in parentheses        |
| `\s+`           | `" "`       | Normalizes whitespace              |