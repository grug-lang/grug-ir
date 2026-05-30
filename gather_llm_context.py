import argparse
import os
from pathlib import Path

# Files and directories to ignore so we don't bloat the context window
IGNORE_DIRS = {
    ".git",
    ".github",  # Ignore CI/CD workflow files (unless you are debugging them)
    ".vscode",  # Ignore local IDE settings
    ".output"
}

IGNORE_FILES = {
    "generate_llm_prompt.py",
    ".coverage",  # Coverage data is large and irrelevant to code logic
    ".gitignore",  # Version control tooling
    ".pre-commit-config.yaml",  # Formatting tooling
    "LICENSE",
}

# Add binary or non-text extensions you want to explicitly skip
IGNORE_EXTS = {".exe", ".out"}


def generate_tree(dir_path: Path, prefix: str = "") -> str:
    """Generates a string representation of the directory tree."""
    tree_str = ""
    # Sort directories first, then files
    try:
        paths = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return tree_str

    # Filter out ignored directories and files
    paths = [
        p for p in paths if p.name not in IGNORE_DIRS and p.name not in IGNORE_FILES
    ]

    for i, path in enumerate(paths):
        is_last = i == (len(paths) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{path.name}\n"

        if path.is_dir():
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(path, prefix + extension)

    return tree_str


def is_text_file(filepath: Path) -> bool:
    """Attempts to determine if a file is plain text."""
    if filepath.suffix in IGNORE_EXTS:
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False


def generate_prompt(root_dir: Path, output_file: Path):
    """Generates the combined LLM prompt file using XML tags for safe boundaries."""
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(
            "Here is the context for my project. Please review the directory structure and file contents below.\n\n"
        )

        # Directory Structure
        out.write("<directory_structure>\n")
        out.write(f"{root_dir.name}/\n")
        out.write(generate_tree(root_dir))
        out.write("</directory_structure>\n\n")

        out.write("<project_files>\n")

        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in sorted(files):
                if file in IGNORE_FILES:
                    continue

                filepath = Path(root) / file

                if is_text_file(filepath):
                    rel_path = filepath.relative_to(root_dir)

                    # Use XML tags instead of markdown backticks to prevent collisions
                    out.write(f'<file path="{rel_path}">\n')

                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            out.write(content)
                            # Ensure the file block ends cleanly with a newline
                            if not content.endswith("\n"):
                                out.write("\n")
                    except Exception as e:
                        out.write(f"// Error reading file: {e}\n")

                    out.write("</file>\n\n")

        out.write("</project_files>\n")


def main():
    parser = argparse.ArgumentParser(
        description="Gather codebase context into a single prompt file for LLMs."
    )
    parser.add_argument(
        "-d",
        "--dir",
        default=".",
        help="Root directory of the project (default: current dir)",
    )
    parser.add_argument(
        "-o",
        "--out",
        default="llm_context.txt",
        help="Output file name (default: llm_context.txt)",
    )

    args = parser.parse_args()

    root_directory = Path(args.dir).resolve()
    output_filepath = Path(args.out).resolve()

    # Ignore the output file itself
    IGNORE_FILES.add(output_filepath.name)

    print(f"Gathering context from: {root_directory}")
    generate_prompt(root_directory, output_filepath)
    print(f"Done! Context saved to: {output_filepath}")


if __name__ == "__main__":
    main()
