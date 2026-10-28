from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("inventory_repository.py")


class InventoryRepositoryTests(unittest.TestCase):
    def load_module(self):
        specification = importlib.util.spec_from_file_location("inventory_repository_under_test", SCRIPT)
        if specification is None or specification.loader is None:
            self.fail("unable to load inventory_repository.py")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module

    def write(self, root: Path, relative: str, content: str | bytes = "") -> Path:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def run_inventory(self, root: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout) if result.returncode == 0 else {}
        return result, payload

    def init_git(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)

    def snapshot(self, root: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in sorted(root.rglob("*")):
            if not item.is_file() or ".git" in item.parts:
                continue
            relative = item.relative_to(root).as_posix()
            result[relative] = hashlib.sha256(item.read_bytes()).hexdigest()
        return result

    def test_detects_typescript_next_prisma_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(
                root,
                "package.json",
                json.dumps(
                    {
                        "dependencies": {"next": "16.0.0", "@prisma/client": "7.0.0"},
                        "devDependencies": {"typescript": "5.0.0"},
                        "scripts": {"private-token": "must-not-be-emitted"},
                    }
                ),
            )
            self.write(root, "src/app/api/projects/route.ts", "export async function GET() {}")
            self.write(root, "prisma/schema.prisma", "model Project { id String @id }")
            self.write(root, "prisma/migrations/001_init/migration.sql", "CREATE TABLE Project(id text);")
            self.write(root, "scripts/test-e2e.mjs", "export const passed = true;")
            self.write(root, "Dockerfile", "FROM node:22")
            self.write(root, "docs/code-contracts/INDEX.md", "# Existing")

            result, payload = self.run_inventory(root, "--pretty")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["schema_version"], 1)
            self.assertTrue({"TypeScript", "Next.js", "Prisma", "Docker"} <= set(payload["detected_stack"]))
            self.assertIn("src/app/api/projects/route.ts", payload["files"]["entrypoints"])
            self.assertIn("prisma/schema.prisma", payload["files"]["schemas"])
            self.assertIn("prisma/migrations/001_init/migration.sql", payload["files"]["migrations"])
            self.assertIn("scripts/test-e2e.mjs", payload["files"]["tests"])
            self.assertIn("docs/code-contracts/INDEX.md", payload["files"]["existing_code_contracts"])
            self.assertNotIn("must-not-be-emitted", result.stdout)

    def test_detects_python_sqlite_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(
                root,
                "pyproject.toml",
                '[project]\nname = "sample"\ndependencies = ["fastapi>=0.100"]\n',
            )
            self.write(root, "src/main.py", "import sqlite3\n\ndef main():\n    return sqlite3.connect('db.sqlite3')\n")
            self.write(root, "migrations/001_init.sql", "CREATE TABLE item(id integer primary key);")
            self.write(root, "db.sqlite3", b"SQLite format 3\x00")
            self.write(root, "tests/test_main.py", "def test_main():\n    assert True\n")

            result, payload = self.run_inventory(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue({"Python", "FastAPI", "SQLite"} <= set(payload["detected_stack"]))
            self.assertIn("src/main.py", payload["files"]["entrypoints"])
            self.assertIn("migrations/001_init.sql", payload["files"]["migrations"])
            self.assertIn("tests/test_main.py", payload["files"]["tests"])

    def test_excludes_dependencies_build_output_docs_and_sensitive_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/main.ts", "export const value = 1;")
            self.write(root, "node_modules/pkg/index.js", "dependency")
            self.write(root, "dist/app.js", "compiled")
            self.write(root, "generated/client.py", "GENERATED = True")
            self.write(root, "assets/module.wasm", b"\x00asm\x01\x00\x00\x00")
            self.write(root, "docs/PRD.md", "stale requirement")
            self.write(root, ".env", "PRIVATE_TOKEN=secret-value-must-not-appear")

            result, payload = self.run_inventory(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            serialized = json.dumps(payload, ensure_ascii=False)
            all_paths = [
                item
                for category in payload["files"].values()
                for item in category
            ]

            self.assertNotIn("node_modules/pkg/index.js", all_paths)
            self.assertNotIn("dist/app.js", all_paths)
            self.assertNotIn("generated/client.py", all_paths)
            self.assertNotIn("assets/module.wasm", all_paths)
            self.assertNotIn("docs/PRD.md", all_paths)
            self.assertNotIn(".env", all_paths)
            self.assertNotIn("secret-value-must-not-appear", serialized)
            self.assertIn("binary-files", payload["scan"]["excluded"])

    def test_does_not_follow_external_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as external_dir:
            root = Path(repo_dir)
            external = Path(external_dir)
            self.write(root, "src/main.py", "print('safe')")
            self.write(external, "secret.py", "EXTERNAL_SECRET = 'do-not-read'")
            link = root / "external-link"
            try:
                link.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")

            result, payload = self.run_inventory(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("do-not-read", json.dumps(payload))
            self.assertTrue(any("external-link" in warning for warning in payload["scan"]["warnings"]))

    def test_reports_git_revision_and_dirty_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.init_git(root)
            source = self.write(root, "src/main.py", "print('clean')\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True)
            source.write_text("print('dirty')\n", encoding="utf-8")

            result, payload = self.run_inventory(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            git_data = payload["repository"]["git"]

            self.assertTrue(git_data["available"])
            self.assertEqual(len(git_data["commit"]), 40)
            self.assertTrue(git_data["dirty"])
            self.assertIn("src/main.py", git_data["changed_files"])

    def test_git_commands_disable_optional_locks(self) -> None:
        module = self.load_module()
        completed = subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout="",
            stderr="",
        )

        with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
            module.run_git(Path("/repository"), "status", "--porcelain")

        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")

    def test_detects_additional_languages_and_package_managers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/main.rs", "fn main() {}")
            self.write(root, "src/tool.rb", "puts 'ok'")
            self.write(root, "src/index.php", "<?php echo 'ok';")
            self.write(root, "src/App.cs", "class App {}")
            self.write(root, "src/main.swift", "print(\"ok\")")
            self.write(root, "src/App.kt", "fun main() {}")
            self.write(root, "src/Main.scala", "object Main")
            self.write(root, "src/native.c", "int main(void) { return 0; }")
            self.write(root, "src/native.cpp", "int main() { return 0; }")
            self.write(root, "Cargo.toml", "[package]\nname = \"sample\"\nversion = \"0.1.0\"\n")
            self.write(root, "Gemfile", "source 'https://example.invalid'\n")
            self.write(root, "composer.json", "{}")
            self.write(root, "sample.csproj", "<Project />")
            self.write(root, "Package.swift", "// swift-tools-version: 5.9")

            result, payload = self.run_inventory(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                {
                    "C",
                    "C++",
                    "C#",
                    "Kotlin",
                    "PHP",
                    "Ruby",
                    "Rust",
                    "Scala",
                    "Swift",
                }
                <= set(payload["detected_stack"])
            )
            self.assertTrue(
                {"Bundler", "Cargo", "Composer", "NuGet", "SwiftPM"}
                <= set(payload["package_managers"])
            )

    def test_lockfiles_take_precedence_over_fallback_package_managers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "package.json", "{}")
            self.write(root, "pnpm-lock.yaml", "lockfileVersion: '9.0'")
            self.write(root, "pyproject.toml", "[project]\nname = 'sample'\n")
            self.write(root, "uv.lock", "version = 1\n")

            result, payload = self.run_inventory(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pnpm", payload["package_managers"])
            self.assertIn("uv", payload["package_managers"])
            self.assertNotIn("npm", payload["package_managers"])
            self.assertNotIn("pip", payload["package_managers"])

    def test_excludes_archives_and_large_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/main.py", "x")
            self.write(root, "archive/old.py", "x")
            self.write(root, "notes.txt", "content larger than limit")

            result, payload = self.run_inventory(root, "--max-file-size", "8")
            all_paths = [
                item
                for category in payload["files"].values()
                for item in category
            ]

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("archive/old.py", all_paths)
            self.assertNotIn("notes.txt", all_paths)
            self.assertTrue(
                any(warning == "skipped-large-file:notes.txt" for warning in payload["scan"]["warnings"])
            )

    def test_emits_relative_sorted_paths_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/z.py", "Z = 1")
            self.write(root, "src/a.py", "A = 1")
            self.write(root, ".env.production", "TOKEN=another-secret")

            result, payload = self.run_inventory(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            for paths in payload["files"].values():
                self.assertEqual(paths, sorted(paths))
                self.assertTrue(all(not Path(item).is_absolute() for item in paths))
            self.assertNotIn("another-secret", result.stdout)

    def test_does_not_modify_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/main.py", "print('unchanged')\n")
            before = self.snapshot(root)

            result, _ = self.run_inventory(root)
            after = self.snapshot(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, after)

    def test_rejects_non_directory_repository_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.write(Path(temp_dir), "not-a-directory.txt", "content")

            result, _ = self.run_inventory(target)

            self.assertEqual(result.returncode, 2)
            self.assertIn("not a directory", result.stderr.lower())
            self.assertEqual(result.stdout, "")

    def test_interruption_leaves_repository_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for index in range(500):
                self.write(root, f"src/module_{index:04d}.py", f"VALUE = {index}\n")
            before = self.snapshot(root)

            process = subprocess.Popen(
                [sys.executable, str(SCRIPT), str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            process.terminate()
            process.communicate(timeout=10)

            self.assertEqual(before, self.snapshot(root))
            self.assertFalse(any(item.name.startswith("contract-from-code") for item in root.iterdir()))

    def test_invalid_max_file_size_leaves_repository_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write(root, "src/main.py", "print('unchanged')\n")
            before = self.snapshot(root)

            result, _ = self.run_inventory(root, "--max-file-size", "0")

            self.assertEqual(result.returncode, 2)
            self.assertEqual(before, self.snapshot(root))


if __name__ == "__main__":
    unittest.main()
