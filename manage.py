#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    # Ensure the submodule root is on sys.path so dev_project.settings is importable
    # regardless of whether this script is called from here or from the parent repo.
    sys.path.insert(0, str(Path(__file__).parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dev_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure the virtual environment is active."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
