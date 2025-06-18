import os
from pathlib import Path

from DownloaderWorker import DownloaderWorker
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from RenamerWorker import RenamerWorker
from styleSheets import (
    blueStyleSheet,
    purpleStyleSheet,
    redStyleSheet,
)
from TemplateDatabase import TemplateDatabase


class MainWindow(QMainWindow):
    """Main window for the YT Music Downloader & Renamer GUI."""

    default_music_dir = Path.home() / "Documents" / "Downloaded Music"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Music Downloader & Renamer")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the template database
        self.db = TemplateDatabase()
        self.db.add_default_templates()

        # Worker thread references
        self.thread = None
        self.worker = None

        self.default_music_dir.mkdir(parents=True, exist_ok=True)

        # Build the UI
        self.setup_ui()

    # ---------------------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------------------
    def setup_ui(self):
        """Create and configure all UI elements."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.downloader_tab = QWidget()
        self.renamer_tab = QWidget()
        self.templates_tab = QWidget()

        self.tabs.addTab(self.downloader_tab, "💾 Downloader")
        self.tabs.addTab(self.renamer_tab, "✏️ Renamer")
        self.tabs.addTab(self.templates_tab, "⚙️ Templates")

        # Populate each tab
        self.create_downloader_tab()
        self.create_renamer_tab()
        self.create_templates_tab()

    # ------------------------------------------------------------------
    # Downloader tab
    # ------------------------------------------------------------------
    def create_downloader_tab(self):
        layout = QVBoxLayout(self.downloader_tab)

        # Playlist URL field
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Playlist URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://music.youtube.com/playlist?list=...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Output directory selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Save folder:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(False)
        self.output_dir_input.setText(str(object=self.default_music_dir))
        dir_layout.addWidget(self.output_dir_input)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(
            lambda: self.browse_output_directory(self.default_music_dir)
        )
        dir_layout.addWidget(self.browse_btn)
        layout.addLayout(dir_layout)

        # Start download button
        self.start_download_btn = QPushButton("Start Download")
        self.start_download_btn.setStyleSheet(purpleStyleSheet)
        self.start_download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.start_download_btn)

        # Counters
        counters_layout = QHBoxLayout()
        self.success_label = QLabel("Success: 0")
        self.fail_label = QLabel("Failed: 0")
        counters_layout.addStretch()
        counters_layout.addWidget(self.success_label)
        counters_layout.addStretch()
        counters_layout.addWidget(self.fail_label)
        counters_layout.addStretch()
        layout.addLayout(counters_layout)

        # Download log
        self.download_log = QTextEdit()
        self.download_log.setReadOnly(True)
        layout.addWidget(self.download_log)

    # ------------------------------------------------------------------
    # Renamer tab
    # ------------------------------------------------------------------
    def create_renamer_tab(self):
        layout = QVBoxLayout(self.renamer_tab)

        # Music folder selection
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Music folder:"))
        self.rename_dir_input = QLineEdit()
        self.rename_dir_input.setReadOnly(True)
        dir_layout.addWidget(self.rename_dir_input)
        self.rename_browse_btn = QPushButton("Browse…")
        self.rename_browse_btn.clicked.connect(
            lambda: self.browse_rename_directory(self.default_music_dir)
        )
        dir_layout.addWidget(self.rename_browse_btn)
        layout.addLayout(dir_layout)

        # Control buttons
        action_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Folder")
        self.scan_btn.setStyleSheet(blueStyleSheet)
        self.scan_btn.clicked.connect(self.scan_for_rename)
        self.rename_btn = QPushButton("Rename Selected")
        self.rename_btn.setStyleSheet(purpleStyleSheet)
        self.rename_btn.clicked.connect(self.start_rename)
        action_layout.addWidget(self.scan_btn)
        action_layout.addWidget(self.rename_btn)
        layout.addLayout(action_layout)

        # Rename table
        self.rename_table = QTableWidget()
        self.rename_table.setColumnCount(3)
        self.rename_table.setHorizontalHeaderLabels(["", "Current Name", "New Name"])
        self.rename_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.rename_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.rename_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        layout.addWidget(self.rename_table)

        # Rename message label
        self.rename_message_label = QLabel("")
        message_layout = QVBoxLayout()
        message_layout.addWidget(
            self.rename_message_label, alignment=Qt.AlignHCenter | Qt.AlignTop
        )
        layout.addLayout(message_layout)

    # ------------------------------------------------------------------
    # Templates tab
    # ------------------------------------------------------------------
    def create_templates_tab(self):
        layout = QVBoxLayout(self.templates_tab)

        # Header with menu button (ellipsis)
        header_layout = QHBoxLayout()
        header_label = QLabel(
            "Here you can manage rename templates (regular expressions are used)."
        )
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        menu_btn = QToolButton()
        menu_btn.setText("⚙️")  # three‑dot menu
        menu_btn.setFixedWidth(24)
        menu = QMenu(menu_btn)
        action_export = QAction("Export templates to file", self)
        action_import = QAction("Import templates from file", self)
        menu.addAction(action_export)
        menu.addAction(action_import)
        menu_btn.setMenu(menu)
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        header_layout.addWidget(menu_btn)
        layout.addLayout(header_layout)

        # Connect menu actions
        action_export.triggered.connect(self.export_templates_to_file)
        action_import.triggered.connect(self.import_templates_from_file)

        # Template table
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(3)
        self.templates_table.setHorizontalHeaderLabels(["ID", "Pattern", "Replacement"])
        self.templates_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.templates_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.templates_table.hideColumn(0)  # Hide ID column – only needed for deletion
        layout.addWidget(self.templates_table)

        # Add-form
        add_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Pattern (regex)")
        self.pattern_input.setFixedHeight(32)

        self.replacement_input = QLineEdit()
        self.replacement_input.setPlaceholderText("Replacement")
        self.replacement_input.setFixedHeight(32)

        self.add_template_btn = QPushButton("Add Template")
        self.add_template_btn.setStyleSheet(purpleStyleSheet)

        add_layout.addWidget(self.pattern_input)
        add_layout.addWidget(self.replacement_input)
        add_layout.addWidget(self.add_template_btn)
        layout.addLayout(add_layout)

        self.delete_template_btn = QPushButton("Delete Selected Template")
        self.delete_template_btn.setStyleSheet(redStyleSheet)
        layout.addWidget(self.delete_template_btn)

        # Connect signals
        self.add_template_btn.clicked.connect(self.add_template)
        self.delete_template_btn.clicked.connect(self.delete_template)

        # Initial load
        self.load_templates_to_table()

    # ------------------------------------------------------------------
    # Template‑tab helpers
    # ------------------------------------------------------------------
    def load_templates_to_table(self):
        """Refresh the template table from the database."""
        self.templates_table.setRowCount(0)
        for template in self.db.get_all_templates():
            row = self.templates_table.rowCount()
            self.templates_table.insertRow(row)
            self.templates_table.setItem(row, 0, QTableWidgetItem(str(template[0])))
            self.templates_table.setItem(row, 1, QTableWidgetItem(template[1]))
            self.templates_table.setItem(row, 2, QTableWidgetItem(template[2]))

    def export_templates_to_file(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export templates",
            str(self.default_music_dir / "templates.json"),
            "JSON (*.json)",
        )
        if not filepath:
            return
        data = [
            dict(id=t[0], pattern=t[1], replacement=t[2])
            for t in self.db.get_all_templates()
        ]
        try:
            import json

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.download_log.append(f"✔️ Templates exported to {filepath}")
        except Exception as e:
            self.download_log.append(f"⛔ Export failed: {e}")

    def import_templates_from_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import templates", str(self.default_music_dir), "JSON (*.json)"
        )
        if not filepath:
            return
        try:
            import json

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for item in data:
                pattern = item.get("pattern")
                replacement = item.get("replacement", "")
                if pattern:
                    try:
                        self.db.add_template(pattern, replacement)
                        count += 1
                    except Exception:
                        pass  # skip duplicates
            self.load_templates_to_table()
            self.download_log.append(f"✔️ Imported {count} templates from file")
        except Exception as e:
            self.download_log.append(f"⛔ Import failed: {e}")

    def add_template(self):
        pattern = self.pattern_input.text().strip()
        replacement = self.replacement_input.text().strip()
        if pattern:
            try:
                self.db.add_template(pattern, replacement)
                self.load_templates_to_table()
                self.pattern_input.clear()
                self.replacement_input.clear()
            except Exception as e:
                self.download_log.append(f"⛔ Failed to add template: {e}")

    def delete_template(self):
        row = self.templates_table.currentRow()
        if row >= 0:
            template_id = int(self.templates_table.item(row, 0).text())
            self.db.delete_template(template_id)
            self.load_templates_to_table()

    # ------------------------------------------------------------------
    # Downloader‑tab actions
    # ------------------------------------------------------------------
    def browse_output_directory(self, path=None):
        directory = QFileDialog.getExistingDirectory(
            self, "Select save folder", str(path)
        )
        if directory:
            self.output_dir_input.setText(directory)

    def start_download(self):
        url = self.url_input.text()
        output_dir = self.output_dir_input.text()

        if not url:
            self.download_log.append("⛔ Please enter a playlist URL.")
            return

        os.makedirs(output_dir, exist_ok=True)

        # Reset UI state and counters
        self.start_download_btn.setEnabled(False)
        self.download_log.clear()
        self.success_count = 0
        self.fail_count = 0
        self.success_label.setText("Success: 0")
        self.fail_label.setText("Failed: 0")

        # Configure worker thread
        self.thread = QThread()
        self.worker = DownloaderWorker(url, output_dir)
        self.worker.moveToThread(self.thread)

        # Signal wiring
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.start_download_btn.setEnabled(True))

        self.worker.progress.connect(self.update_download_log)
        self.worker.error.connect(self.update_download_log)
        self.worker.track_success.connect(self.increment_success)
        self.worker.track_fail.connect(self.increment_fail)

        self.thread.start()

    def update_download_log(self, message):
        self.download_log.append(message)

    def increment_success(self, _filename):
        self.success_count += 1
        self.success_label.setText(f"Success: {self.success_count}")

    def increment_fail(self, _filename):
        self.fail_count += 1
        self.fail_label.setText(f"Failed: {self.fail_count}")

    # ------------------------------------------------------------------
    # Renamer‑tab actions
    # ------------------------------------------------------------------
    def browse_rename_directory(self, path=None):
        directory = QFileDialog.getExistingDirectory(
            self, "Select music folder", str(path)
        )
        if directory:
            self.rename_dir_input.setText(directory)
            self.scan_for_rename()

    def scan_for_rename(self):
        directory = self.rename_dir_input.text()
        if not directory or not os.path.isdir(directory):
            # Could show an error message here
            return

        templates = [(t[1], t[2]) for t in self.db.get_all_templates()]

        self.thread = QThread()
        self.worker = RenamerWorker(templates)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(lambda: self.worker.scan_directory(directory))
        self.worker.scan_complete.connect(self.populate_rename_table)
        self.worker.error.connect(
            lambda err: self.download_log.append(f"Rename error: {err}")
        )
        self.worker.scan_complete.connect(self.thread.quit)
        self.worker.scan_complete.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def populate_rename_table(self, files):
        """Populate the table with (old_name, new_name) pairs returned from the scan."""

        if not files:
            self.rename_table.hide()
            self.rename_message_label.setText("⛔ No files found for renaming.")
            return
        else:
            self.rename_table.show()
            self.rename_message_label.setText("")
            self.rename_table.setRowCount(0)

        for old_name, new_name in files:
            row = self.rename_table.rowCount()
            self.rename_table.insertRow(row)

            # Checkbox cell
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.rename_table.setCellWidget(row, 0, cell_widget)

            self.rename_table.setItem(row, 1, QTableWidgetItem(old_name))
            self.rename_table.setItem(row, 2, QTableWidgetItem(new_name))

    def start_rename(self):
        directory = self.rename_dir_input.text()
        if not directory:
            return

        files_to_rename = []
        for row in range(self.rename_table.rowCount()):
            checkbox_widget = self.rename_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                old_name = self.rename_table.item(row, 1).text()
                new_name = self.rename_table.item(row, 2).text()
                files_to_rename.append((old_name, new_name))

        if not files_to_rename:
            return

        templates = [(t[1], t[2]) for t in self.db.get_all_templates()]

        self.thread = QThread()
        self.worker = RenamerWorker(templates)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            lambda: self.worker.rename_files(directory, files_to_rename)
        )
        self.worker.rename_progress.connect(
            self.update_download_log
        )  # Reuse the same log widget
        self.worker.rename_finished.connect(self.on_rename_finished)

        self.worker.rename_finished.connect(self.thread.quit)
        self.worker.rename_finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_rename_finished(self):
        self.update_download_log("✔️ Renaming finished.")
        # Refresh the table after renaming
        self.thread.quit()
        self.thread.wait()
        self.scan_for_rename()

    # ------------------------------------------------------------------
    # Shutdown handling
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Ensure worker threads shut down cleanly when the window closes."""
        if self.worker:
            self.worker.is_running = False

        # Wait up to 5 seconds for the thread to finish
        if self.thread and self.thread.isRunning():
            self.download_log.append("Finishing background tasks…")
            if not self.thread.wait(5000):
                self.download_log.append(
                    "⚠️ Thread did not respond in time. Possible issue on shutdown."
                )

        # Close DB connection
        self.db.close()
        event.accept()
