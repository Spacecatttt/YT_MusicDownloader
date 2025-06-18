import logging
import os
from shutil import which

from PySide6.QtCore import QObject, Signal


class DownloaderWorker(QObject):
    """
    Worker class for downloading music in a separate thread.
    """

    progress = Signal(str)
    track_success = Signal(str)
    track_fail = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, url, output_dir):
        super().__init__()
        self.playlist_url = url
        self.output_dir = output_dir
        self.is_running = True

    def get_ffmpeg_path(self):
        path = which("ffmpeg")
        if path:
            return path
        logging.fatal("FFmpeg not found in PATH")
        raise FileNotFoundError("FFmpeg not found in PATH")

    def progress_hook(self, d):
        """Hook to track download status from yt-dlp."""
        if not self.is_running:
            raise Exception("Download stopped by user.")

        if d["status"] == "finished":
            file_path = d.get("filename") or d.get("info_dict", {}).get("_filename")
            if file_path:
                self.progress.emit(f"✔️ Finished: {os.path.basename(file_path)}")
                self.track_success.emit(file_path)
        elif d["status"] == "error":
            error_message = d.get("error", "Unknown download error")
            filename = d.get("filename", "Unknown file")
            self.progress.emit(f"⛔ Download error '{os.path.basename(filename)}'.")
            logging.error(f"Download error for {filename}: {error_message}")
            self.track_fail.emit(filename)

    def run(self):
        """Main method that starts the download process."""
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(
                    self.output_dir, "%(artist,uploader)s - %(track,title)s.%(ext)s"
                ),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "m4a",
                        "preferredquality": "best",
                    }
                ],
                "ffmpeg_location": self.get_ffmpeg_path(),
                "ignoreerrors": True,  # Very important to not stop on errors
                "progress_hooks": [self.progress_hook],
                "logger": logging.getLogger(),
                "quiet": True,
                "noprogress": True,  # Use custom progress
                "cookies_from_browser": ("chrome",),
                #  If True - replace spaces and special characters (e.g. ., (, )) with underscores (_).
                "restrictfilenames": False,
                "trim_filenames": 40,
                "sleep_interval": 3,
                "max_sleep_interval": 10,
            }

            self.progress.emit(f"Starting playlist download: {self.playlist_url}")
            self.progress.emit(f"📂 Saving to: {self.output_dir}")

            import yt_dlp

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.playlist_url])

            self.progress.emit("✔️ All downloads completed.")

        except Exception as e:
            self.error.emit(f"Critical error: {e}")
            logging.fatal(f"An unexpected error occurred in downloader thread: {e}")
        finally:
            self.finished.emit()
