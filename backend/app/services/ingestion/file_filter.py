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
    "i18n",
    "locale",
    "locales",
    "l10n",
    "translations",
}

LOCALE_DIRECTORY_NAMES = {
    "ar",
    "bg",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "fa",
    "fi",
    "fr",
    "he",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "ja",
    "ko",
    "lt",
    "ms",
    "nb",
    "nl",
    "no",
    "pl",
    "pt",
    "pt-br",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh",
    "zh-cn",
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

    # we only want files, not directories/subtrees.
    if not path.name:
        return False

    # ignoring files inside blocked directories, including translated content trees.
    if any(part.lower() in BLOCKED_DIRECTORIES for part in path.parts):
        return False

    # keep docs/documentation, but reject localized translation folders
    # inside docs trees.
    normalized_parts = [part.lower() for part in path.parts]
    if "docs" in normalized_parts or "documentation" in normalized_parts:
        locale_candidates = {
            part.lower()
            for part in path.parts
            if part and part.lower() not in {"docs", "documentation"}
        }
        if locale_candidates & LOCALE_DIRECTORY_NAMES:
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
