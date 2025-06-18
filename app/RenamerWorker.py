import os
import re

from PySide6.QtCore import QObject, Signal


class RenamerWorker(QObject):
    """
    Worker class for scanning directories and renaming files after downloading.
    """

    scan_complete = Signal(list)
    rename_progress = Signal(str)
    rename_finished = Signal()
    error = Signal(str)

    def __init__(self, templates):
        super().__init__()
        self.templates = templates

    def scan_directory(self, directory):
        """Scans the directory and builds a list of files that need renaming."""
        results = []
        try:
            for filename in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, filename)):
                    name_without_ext, file_ext = os.path.splitext(filename)
                    cleaned_name = self.clean_filename(name_without_ext)

                    if cleaned_name != name_without_ext:
                        new_filename = f"{cleaned_name}{file_ext}"
                        results.append((filename, new_filename))

            self.scan_complete.emit(results)
        except Exception as e:
            self.error.emit(f"Scan error: {e}")

    def clean_filename(self, name):
        """Applies regex templates to clean up a file name."""
        cleaned_name = name
        for pattern, replacement in self.templates:
            cleaned_name = re.sub(
                pattern, replacement, cleaned_name, flags=re.IGNORECASE
            )

        # Remove trailing spaces, dashes or underscores
        cleaned_name = cleaned_name.strip(" -_")
        return cleaned_name

    def rename_files(self, directory, files_to_rename):
        """Renames the selected files."""
        try:
            for old_name, new_name in files_to_rename:
                old_path = os.path.join(directory, old_name)
                new_path = os.path.join(directory, new_name)
                try:
                    os.rename(old_path, new_path)
                    self.rename_progress.emit(f"✔️ {old_name} -> {new_name}")
                except OSError as e:
                    self.rename_progress.emit(f"⛔ Failed to rename {old_name}: {e}")
            self.rename_finished.emit()
        except Exception as e:
            self.error.emit(f"Critical error during renaming: {e}")
