# project_tree.py
import os

EXCLUDE_DIRS = {".idea", ".venv", "__pycache__", ".git"}

def print_tree(startpath, prefix=""):
    try:
        items = sorted(
            name for name in os.listdir(startpath) if name not in EXCLUDE_DIRS
        )
    except FileNotFoundError:
        print(f"Path not found: {startpath}")
        return

    for i, name in enumerate(items):
        path = os.path.join(startpath, name)
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if i == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)


if __name__ == "__main__":
    root = "."   # шукаємо з поточної директорії
    print(os.path.basename(os.path.abspath(root)) + "/")
    print_tree(root)
