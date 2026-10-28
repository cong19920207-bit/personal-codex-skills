#!/usr/bin/env python3
"""Build a read-only, secret-safe inventory of a source repository."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


SCHEMA_VERSION = 1
DEFAULT_MAX_FILE_SIZE = 2 * 1024 * 1024

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "archive",
    "build",
    "coverage",
    "dist",
    "generated",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
}

BINARY_SUFFIXES = {
    ".7z",
    ".a",
    ".class",
    ".dll",
    ".dylib",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".o",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".tar",
    ".wasm",
    ".webp",
    ".zip",
}

SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "secrets.yml",
    "secrets.yaml",
}

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}

CONFIG_NAMES = {
    ".env.example",
    "application.properties",
    "application.yml",
    "application.yaml",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
    "Cargo.lock",
    "composer.json",
    "Gemfile",
    "Gemfile.lock",
    "go.mod",
    "go.sum",
    "gradle.properties",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "pom.xml",
    "Package.swift",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "settings.gradle",
    "settings.gradle.kts",
    "tsconfig.json",
    "uv.lock",
    "yarn.lock",
}

BUILD_DEPLOY_NAMES = {
    ".dockerignore",
    "Dockerfile",
    "Jenkinsfile",
    "Makefile",
    "Procfile",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "fly.toml",
    "netlify.toml",
    "render.yaml",
    "vercel.json",
}

SCHEMA_NAMES = {
    "asyncapi.json",
    "asyncapi.yaml",
    "asyncapi.yml",
    "openapi.json",
    "openapi.yaml",
    "openapi.yml",
    "schema.graphql",
    "schema.prisma",
}

FILE_CATEGORIES = (
    "entrypoints",
    "source",
    "schemas",
    "migrations",
    "tests",
    "config",
    "build_deploy",
    "existing_code_contracts",
)


def is_sensitive_name(name: str) -> bool:
    lower = name.lower()
    if lower in SENSITIVE_NAMES:
        return True
    return lower.startswith(".env.") and lower != ".env.example"


def is_code_contract_path(relative: Path) -> bool:
    parts = relative.parts
    return len(parts) >= 2 and parts[0].lower() == "docs" and parts[1].lower() == "code-contracts"


def is_allowed_docs_path(relative: Path) -> bool:
    parts = relative.parts
    if not parts or parts[0].lower() != "docs":
        return True
    return len(parts) == 1 or parts[1].lower() == "code-contracts"


def relative_text(root: Path, target: Path) -> str:
    return target.relative_to(root).as_posix()


def walk_repository(root: Path, max_file_size: int) -> tuple[list[Path], list[str], list[str]]:
    files: list[Path] = []
    excluded: set[str] = set()
    warnings: set[str] = set()
    pending = [root]

    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name.lower())
        except OSError:
            warnings.add(f"unreadable-directory:{relative_text(root, directory) or '.'}")
            continue

        for entry in entries:
            target = Path(entry.path)
            relative = target.relative_to(root)
            relative_name = relative.as_posix()

            if entry.is_symlink():
                warnings.add(f"skipped-symlink:{relative_name}")
                continue

            if entry.is_dir(follow_symlinks=False):
                if entry.name in EXCLUDED_DIRS:
                    excluded.add(f"directory:{relative_name}")
                    continue
                if not is_allowed_docs_path(relative):
                    excluded.add(f"documentation:{relative_name}")
                    continue
                pending.append(target)
                continue

            if not entry.is_file(follow_symlinks=False):
                warnings.add(f"skipped-non-file:{relative_name}")
                continue

            if is_sensitive_name(entry.name):
                excluded.add("sensitive-files")
                continue

            if not is_allowed_docs_path(relative):
                excluded.add("documentation-files")
                continue

            if target.suffix.lower() in BINARY_SUFFIXES:
                excluded.add("binary-files")
                continue

            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                warnings.add(f"unreadable-file:{relative_name}")
                continue

            if size > max_file_size:
                warnings.add(f"skipped-large-file:{relative_name}")
                continue

            files.append(target)

    return sorted(files, key=lambda item: relative_text(root, item)), sorted(excluded), sorted(warnings)


def is_test_path(relative: Path) -> bool:
    lower_parts = [part.lower() for part in relative.parts]
    name = relative.name.lower()
    return (
        any(part in {"test", "tests", "spec", "specs", "__tests__"} for part in lower_parts[:-1])
        or name.startswith("test_")
        or name.startswith("test-")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test.go")
    )


def is_migration_path(relative: Path) -> bool:
    lower_parts = [part.lower() for part in relative.parts]
    name = relative.name.lower()
    return (
        any(part in {"migration", "migrations", "migrate"} for part in lower_parts[:-1])
        or bool(re.match(r"^\d+[_-].*\.sql$", name))
    )


def is_schema_path(relative: Path) -> bool:
    name = relative.name
    lower = name.lower()
    return (
        name in SCHEMA_NAMES
        or lower.endswith(".schema.json")
        or lower.endswith(".schema.yaml")
        or lower.endswith(".schema.yml")
        or lower == "schema.sql"
    )


def is_entrypoint(relative: Path) -> bool:
    name = relative.name.lower()
    lower_parts = [part.lower() for part in relative.parts]
    return (
        name in {
            "app.py",
            "main.go",
            "main.py",
            "manage.py",
            "route.js",
            "route.ts",
            "server.js",
            "server.py",
            "server.ts",
            "wsgi.py",
            "asgi.py",
        }
        or name.endswith("application.java")
        or (name == "main.go" and "cmd" in lower_parts)
    )


def is_config_path(relative: Path) -> bool:
    name = relative.name
    lower = name.lower()
    return (
        name in CONFIG_NAMES
        or lower.endswith(".csproj")
        or lower.startswith("requirements") and lower.endswith(".txt")
        or lower.startswith("application-") and lower.endswith((".yml", ".yaml", ".properties"))
        or lower.endswith((".config.js", ".config.mjs", ".config.ts"))
        or "config" in [part.lower() for part in relative.parts[:-1]]
    )


def is_build_deploy_path(relative: Path) -> bool:
    name = relative.name
    parts = [part.lower() for part in relative.parts]
    return (
        name in BUILD_DEPLOY_NAMES
        or name.lower().startswith("dockerfile")
        or ".github" in parts and "workflows" in parts
        or "deploy" in parts
        or "deployment" in parts
        or "k8s" in parts
        or "kubernetes" in parts
    )


def classify_files(root: Path, files: Iterable[Path]) -> dict[str, list[str]]:
    categories = {name: [] for name in FILE_CATEGORIES}

    for target in files:
        relative = target.relative_to(root)
        relative_name = relative.as_posix()

        if is_code_contract_path(relative):
            categories["existing_code_contracts"].append(relative_name)
            continue

        if target.suffix.lower() in SOURCE_SUFFIXES:
            categories["source"].append(relative_name)
        if is_entrypoint(relative):
            categories["entrypoints"].append(relative_name)
        if is_schema_path(relative):
            categories["schemas"].append(relative_name)
        if is_migration_path(relative):
            categories["migrations"].append(relative_name)
        if is_test_path(relative):
            categories["tests"].append(relative_name)
        if is_config_path(relative):
            categories["config"].append(relative_name)
        if is_build_deploy_path(relative):
            categories["build_deploy"].append(relative_name)

    return {name: sorted(set(paths)) for name, paths in categories.items()}


def read_dependency_names(root: Path, files: Iterable[Path]) -> set[str]:
    dependencies: set[str] = set()

    for target in files:
        relative = target.relative_to(root)
        name = target.name.lower()

        try:
            if name == "package.json":
                payload = json.loads(target.read_text(encoding="utf-8"))
                for key in ("dependencies", "devDependencies"):
                    values = payload.get(key, {})
                    if isinstance(values, dict):
                        dependencies.update(str(item).lower() for item in values)
            elif name == "pyproject.toml" or name.startswith("requirements"):
                text = target.read_text(encoding="utf-8").lower()
                for package in ("django", "fastapi", "flask"):
                    if re.search(rf"(?<![\w-]){package}(?![\w-])", text):
                        dependencies.add(package)
            elif name in {"pom.xml", "build.gradle", "build.gradle.kts"}:
                text = target.read_text(encoding="utf-8").lower()
                if "spring" in text:
                    dependencies.add("spring")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue

    return dependencies


def detect_stack(root: Path, files: list[Path]) -> list[str]:
    stack: set[str] = set()
    dependencies = read_dependency_names(root, files)
    names = {target.name for target in files}
    suffixes = {target.suffix.lower() for target in files}

    if ".js" in suffixes or ".jsx" in suffixes or ".mjs" in suffixes or "package.json" in names:
        stack.add("JavaScript")
    if ".ts" in suffixes or ".tsx" in suffixes:
        stack.add("TypeScript")
    if "next" in dependencies:
        stack.add("Next.js")
    if "@nestjs/core" in dependencies:
        stack.add("NestJS")
    if "express" in dependencies:
        stack.add("Express")
    if "prisma" in dependencies or "@prisma/client" in dependencies or "schema.prisma" in names:
        stack.add("Prisma")

    if ".py" in suffixes or "pyproject.toml" in names or "requirements.txt" in names:
        stack.add("Python")
    if "fastapi" in dependencies:
        stack.add("FastAPI")
    if "django" in dependencies:
        stack.add("Django")
    if "flask" in dependencies:
        stack.add("Flask")
    if any(target.suffix.lower() in {".db", ".sqlite", ".sqlite3"} for target in files):
        stack.add("SQLite")

    if ".go" in suffixes or "go.mod" in names:
        stack.add("Go")
    if ".java" in suffixes or "pom.xml" in names or "build.gradle" in names or "build.gradle.kts" in names:
        stack.add("Java")
    if ".c" in suffixes or ".h" in suffixes:
        stack.add("C")
    if suffixes & {".cc", ".cpp", ".hpp"}:
        stack.add("C++")
    if ".cs" in suffixes or any(target.suffix.lower() == ".csproj" for target in files):
        stack.add("C#")
    if suffixes & {".kt", ".kts"}:
        stack.add("Kotlin")
    if ".php" in suffixes or "composer.json" in names:
        stack.add("PHP")
    if ".rb" in suffixes or "Gemfile" in names:
        stack.add("Ruby")
    if ".rs" in suffixes or "Cargo.toml" in names:
        stack.add("Rust")
    if ".scala" in suffixes:
        stack.add("Scala")
    if ".swift" in suffixes or "Package.swift" in names:
        stack.add("Swift")
    if "spring" in dependencies:
        stack.add("Spring")
    if any(target.name.startswith("Dockerfile") for target in files) or any(
        target.name in {"compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"}
        for target in files
    ):
        stack.add("Docker")

    return sorted(stack)


def detect_package_managers(files: list[Path]) -> list[str]:
    managers: set[str] = set()
    names = {target.name for target in files}

    has_pnpm_lock = "pnpm-lock.yaml" in names
    has_yarn_lock = "yarn.lock" in names
    has_poetry_lock = "poetry.lock" in names
    has_uv_lock = "uv.lock" in names

    if "package-lock.json" in names or (
        "package.json" in names and not has_pnpm_lock and not has_yarn_lock
    ):
        managers.add("npm")
    if has_pnpm_lock:
        managers.add("pnpm")
    if has_yarn_lock:
        managers.add("Yarn")
    if any(name.startswith("requirements") for name in names) or (
        "pyproject.toml" in names and not has_poetry_lock and not has_uv_lock
    ):
        managers.add("pip")
    if has_poetry_lock:
        managers.add("Poetry")
    if has_uv_lock:
        managers.add("uv")
    if "go.mod" in names:
        managers.add("Go Modules")
    if "pom.xml" in names:
        managers.add("Maven")
    if "build.gradle" in names or "build.gradle.kts" in names:
        managers.add("Gradle")
    if "Cargo.toml" in names:
        managers.add("Cargo")
    if "Gemfile" in names:
        managers.add("Bundler")
    if "composer.json" in names:
        managers.add("Composer")
    if any(target.suffix.lower() == ".csproj" for target in files):
        managers.add("NuGet")
    if "Package.swift" in names:
        managers.add("SwiftPM")

    return sorted(managers)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def safe_changed_path(raw: str) -> str | None:
    candidate = raw.split(" -> ")[-1].strip().strip('"')
    if not candidate:
        return None
    if is_sensitive_name(Path(candidate).name):
        return None
    return candidate


def git_inventory(root: Path) -> dict[str, object]:
    inside = run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "available": False,
            "commit": None,
            "branch": None,
            "dirty": None,
            "changed_files": [],
        }

    commit_result = run_git(root, "rev-parse", "HEAD")
    branch_result = run_git(root, "branch", "--show-current")
    status_result = run_git(root, "status", "--porcelain")
    changed_files: list[str] = []

    if status_result.returncode == 0:
        for line in status_result.stdout.splitlines():
            candidate = safe_changed_path(line[3:] if len(line) >= 4 else "")
            if candidate:
                changed_files.append(candidate)

    return {
        "available": True,
        "commit": commit_result.stdout.strip() if commit_result.returncode == 0 else None,
        "branch": branch_result.stdout.strip() if branch_result.returncode == 0 else None,
        "dirty": bool(status_result.stdout.strip()) if status_result.returncode == 0 else None,
        "changed_files": sorted(set(changed_files)),
    }


def build_inventory(root: Path, max_file_size: int = DEFAULT_MAX_FILE_SIZE) -> dict[str, object]:
    resolved = root.resolve()
    files, excluded, warnings = walk_repository(resolved, max_file_size)
    classified = classify_files(resolved, files)

    return {
        "schema_version": SCHEMA_VERSION,
        "repository": {
            "name": resolved.name,
            "git": git_inventory(resolved),
        },
        "detected_stack": detect_stack(resolved, files),
        "package_managers": detect_package_managers(files),
        "files": classified,
        "scan": {
            "max_file_size": max_file_size,
            "scanned_file_count": len(files),
            "excluded": excluded,
            "warnings": warnings,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Repository directory to inventory")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=DEFAULT_MAX_FILE_SIZE,
        help=f"Skip files larger than this many bytes (default: {DEFAULT_MAX_FILE_SIZE})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.repository)

    if not root.is_dir():
        print(f"Repository path is not a directory: {root}", file=sys.stderr)
        return 2
    if args.max_file_size <= 0:
        print("--max-file-size must be greater than zero", file=sys.stderr)
        return 2

    inventory = build_inventory(root, args.max_file_size)
    print(
        json.dumps(
            inventory,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
