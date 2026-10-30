import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from changelog import collect_commits, last_tag, render


def git(repo: Path, *args: str, env=None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


class GitHistoryIntegrationTests(unittest.TestCase):
    def test_reads_only_commits_after_latest_tag(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Changelog Test")
            git(repo, "config", "user.email", "test@example.invalid")

            (repo / "file.txt").write_text("first\n", encoding="utf-8")
            git(repo, "add", "file.txt")
            git(repo, "commit", "-q", "-m", "feat: initial release")
            git(repo, "tag", "v1.0.0")

            (repo / "file.txt").write_text("second\n", encoding="utf-8")
            git(repo, "add", "file.txt")
            git(repo, "commit", "-q", "-m", "fix: update sample")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                self.assertEqual(last_tag(), "v1.0.0")
                commits = collect_commits("v1.0.0")
                self.assertEqual(len(commits), 1)
                self.assertEqual(commits[0][1], "fix: update sample")
                output = render(commits, "Unreleased", "2026-10-30")
                self.assertIn("### Fixed", output)
                self.assertNotIn("initial release", output)
            finally:
                os.chdir(previous_cwd)


if __name__ == "__main__":
    unittest.main()
