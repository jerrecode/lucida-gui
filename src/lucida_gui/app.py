"""Small but functional Qt 6 desktop interface. API calls run on a worker thread."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from lucida_api import Config, LucidaClient, Job


def main() -> None:
    from PySide6.QtCore import QThread, Signal, Qt, QTimer
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
        QLabel, QMessageBox, QTabWidget, QTextEdit, QFileDialog)

    class TransferWorker(QThread):
        changed = Signal(dict)
        finished_job = Signal(dict)
        error = Signal(str)
        def __init__(self, config: Config, source: str, filename: str | None = None):
            super().__init__()
            self.config, self.source, self.filename = config, source, filename
        def run(self):
            try:
                def report(job: Job):
                    self.changed.emit(job.to_dict())
                job = asyncio.run(LucidaClient(self.config).acquire(self.source, self.filename, report))
                self.finished_job.emit(job.to_dict())
            except Exception as exc:
                self.error.emit(str(exc))

    class SearchWorker(QThread):
        results = Signal(list)
        error = Signal(str)
        def __init__(self, config: Config, query: str):
            super().__init__()
            self.config, self.query = config, query
        def run(self):
            try:
                matches = asyncio.run(LucidaClient(self.config).search(self.query))
                self.results.emit([match.to_dict() for match in matches])
            except Exception as exc:
                self.error.emit(str(exc))

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.config = Config()
            self.api = LucidaClient(self.config)
            self.workers: list[QThread] = []
            self.setWindowTitle("Lucida Desktop 0.1.0")
            self.resize(860, 560)
            tabs = QTabWidget()
            self.setCentralWidget(tabs)

            downloads = QWidget()
            layout = QVBoxLayout(downloads)
            layout.addWidget(QLabel("Authorized audio URL (explicit host approval required for network downloads)"))
            line = QHBoxLayout()
            self.url = QLineEdit()
            self.url.setPlaceholderText("https://approved.example/media.wav")
            self.url.setAccessibleName("Media URL")
            line.addWidget(self.url)
            self.host = QLineEdit()
            self.host.setPlaceholderText("Allowed host")
            self.host.setAccessibleName("Trusted download host")
            self.host.setMaximumWidth(180)
            line.addWidget(self.host)
            layout.addLayout(line)
            row = QHBoxLayout()
            sample = QPushButton("Generate test tone")
            sample.clicked.connect(lambda: self.start("sample://tone"))
            row.addWidget(sample)
            start = QPushButton("Download authorized URL")
            start.clicked.connect(self.start_url)
            row.addWidget(start)
            choose = QPushButton("Choose output folder")
            choose.clicked.connect(self.choose_output)
            row.addWidget(choose)
            layout.addLayout(row)
            self.location = QLabel(str(self.config.output_dir))
            layout.addWidget(self.location)
            self.status = QLabel("Ready. All transfers are processed by Lucida API.")
            layout.addWidget(self.status)
            self.jobs = QTableWidget(0, 4)
            self.jobs.setHorizontalHeaderLabels(["State", "Source", "Bytes", "Output"])
            self.jobs.horizontalHeader().setStretchLastSection(True)
            self.jobs.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            layout.addWidget(self.jobs)
            refresh = QPushButton("Refresh job history")
            refresh.clicked.connect(self.refresh)
            layout.addWidget(refresh)
            tabs.addTab(downloads, "Downloads")

            search_page = QWidget()
            sl = QVBoxLayout(search_page)
            sl.addWidget(QLabel("Search MusicBrainz recording metadata. Results do not provide audio files."))
            search_row = QHBoxLayout()
            self.query = QLineEdit()
            self.query.setPlaceholderText("Track, artist, album ...")
            self.query.setAccessibleName("Recording search query")
            self.query.returnPressed.connect(self.start_search)
            search_row.addWidget(self.query)
            sb = QPushButton("Search")
            sb.clicked.connect(self.start_search)
            search_row.addWidget(sb)
            sl.addLayout(search_row)
            self.search_results = QTextEdit()
            self.search_results.setReadOnly(True)
            self.search_results.setPlainText("Enter search terms to retrieve recording metadata.")
            sl.addWidget(self.search_results)
            tabs.addTab(search_page, "Search")

            info = QWidget()
            il = QVBoxLayout(info)
            desc = QTextEdit()
            desc.setReadOnly(True)
            desc.setPlainText("\n\n".join(
                f"{p['name']}: acquisition={p['acquisition']}; search={p['search']}\n{p['notes']}"
                for p in self.api.providers()))
            il.addWidget(desc)
            tabs.addTab(info, "Providers")
            diagnostics = QWidget()
            dl = QVBoxLayout(diagnostics)
            dl.addWidget(QLabel(f"API {self.api.version()['api']}  •  SQLite journal: {self.config.state_dir}"))
            dl.addWidget(QLabel("Remote Lucida service integration: unverified, not advertised as available."))
            dl.addStretch()
            tabs.addTab(diagnostics, "Diagnostics")
            self.setStyleSheet('''QMainWindow, QWidget { background: #161b26; color: #e7edf9; font-size: 13px; }
                QLineEdit, QTableWidget, QTextEdit { background: #222b39; color: #f5f7fc;
                border: 1px solid #40516b; border-radius: 5px; padding: 7px; }
                QPushButton { background: #304c78; color: white; border: none;
                padding: 10px; border-radius: 6px; } QPushButton:hover { background: #42669c; }
                QTabBar::tab { padding: 12px; } QTabBar::tab:selected { background: #304c78; }''')
            self.refresh()

        def start_search(self):
            query = self.query.text().strip()
            if not query:
                return
            self.search_results.setPlainText("Searching metadata provider...")
            worker = SearchWorker(self.config, query)
            self.workers.append(worker)
            worker.results.connect(lambda results: self.search_results.setPlainText(
                "\n\n".join(f"{r['title']}  |  {r['artist']}\nMusicBrainz ID: {r['id']}  •  score: {r['score']}"
                            for r in results) or "No recordings found"))
            worker.error.connect(lambda reason: self.search_results.setPlainText(f"Metadata search unavailable: {reason}"))
            worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
            worker.start()

        def choose_output(self):
            folder = QFileDialog.getExistingDirectory(self, "Choose download location", str(self.config.output_dir))
            if folder:
                self.config = Config(state_dir=self.config.state_dir, output_dir=Path(folder))
                self.api = LucidaClient(self.config)
                self.location.setText(folder)

        def start_url(self):
            if not self.url.text().strip() or not self.host.text().strip():
                QMessageBox.warning(self, "Source required", "Supply a URL and its trusted hostname.")
                return
            self.start(self.url.text().strip(), self.host.text().strip())

        def start(self, source: str, host: str | None = None):
            cfg = Config(state_dir=self.config.state_dir, output_dir=self.config.output_dir,
                         allowed_hosts=(host,) if host else ())
            worker = TransferWorker(cfg, source)
            self.workers.append(worker)
            worker.changed.connect(lambda job: self.status.setText(
                f"{job['state']}: {job['transferred']} bytes"))
            worker.finished_job.connect(lambda job: (self.status.setText(f"Completed: {job['destination']}"), self.refresh()))
            worker.error.connect(lambda msg: (self.status.setText(f"Error: {msg}"), self.refresh(),
                                              QMessageBox.warning(self, "Transfer failed", msg)))
            worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
            worker.start()

        def refresh(self):
            jobs = self.api.jobs(200)
            self.jobs.setRowCount(len(jobs))
            for i, job in enumerate(jobs):
                for col, val in enumerate((job.state, job.source, job.transferred, job.destination)):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.jobs.setItem(i, col, item)

        def closeEvent(self, event):
            if any(w.isRunning() for w in self.workers):
                QMessageBox.information(self, "Transfers running", "Finish active transfers before closing.")
                event.ignore()
            else:
                event.accept()

    app = QApplication(sys.argv)
    app.setApplicationName("Lucida Desktop")
    window = Window()
    window.show()
    if "--smoke" in sys.argv:
        # Preserve the event loop long enough to process QObject.deleteLater().
        app.setQuitOnLastWindowClosed(False)
        def shutdown_smoke():
            window.close()
            window.deleteLater()
            QTimer.singleShot(200, app.quit)
        QTimer.singleShot(200, shutdown_smoke)
    code = app.exec()
    del window
    del app
    sys.exit(code)

if __name__ == "__main__":
    main()
