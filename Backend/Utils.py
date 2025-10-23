import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and dev mode."""
    try:
        base_path = sys._MEIPASS  # Used when running as bundled EXE
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
