# this file is to filter out the noise- lockfiles, binaries, keep actual high-value code

"""blocklisting directories, only accepting: .py
.js
.ts
.tsx
.java
.cpp
.c
.h
.md
.mdx
.json
.yaml
.yml
.toml
.sql
.html
.css
"""

# skipping files over 500KB to avoid embedding giant auto-generated files.

# mimetypes:
# this is a module used to identify file types based on their extensions or URLs,
# looks at the end of the file name- the extension- maps a file name to its media type standard
from pathlib import PurePosixPath

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".md",
    ".mdx",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".sql",
}

BLOCKED_DIRECTORIES = {
    ".git",
    ".github",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
}

BLOCKED_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
}


def should_ingest_file(
    file_path: str,
    file_size: int | None = None,
    max_size_kb: int = 500,
) -> bool:
    path = PurePosixPath(file_path)

    # We only want files, not directories/subtrees.
    if not path.name:
        return False

    # ignoring files inside blocked directories.
    if any(part in BLOCKED_DIRECTORIES for part in path.parts):
        return False

    # ignoring explicitly blocked filenames.
    if path.name in BLOCKED_FILENAMES:
        return False

    # ignoring unsupported file types.
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False

    # gitHub already gives us the blob size in the tree response.
    if file_size is not None and file_size > max_size_kb * 1024:
        return False

    return True
