# Lucida GUI (0.1.0 development preview)

Qt 6 desktop frontend of [Lucida API](https://github.com/jerrecode/lucida-api). The GUI calls the shared backend in a worker thread. Initial tabs: Downloads, Providers and Diagnostics. Displays persisted jobs and supports a native output-directory picker, offline WAV test file and explicit-host trusted HTTP(S) audio downloads.

Linux install: `./install.sh`; Windows PowerShell: `./install.ps1`. Isolated `.venv` is created with Python >=3.11 and the Lucida API dependency is installed first. For sibling local source checkout set `LUCIDA_API_SOURCE=../lucida-api`. Requires available PySide6 wheel and a desktop session. Run `lucida-gui` from the environment's executable directory.

This is not an official Lucida client. External search, albums/playlists, pause, resume, cancel/retry controls, virtualized large-list view, native executable packaging, and tested Windows UI are future tasks. The close dialog prevents app exit while a job is active. No claim is made that full upstream features function.

Roadmap: [API implementation plan](https://github.com/jerrecode/lucida-api/blob/main/IMPLEMENTATION_PLAN.md).
