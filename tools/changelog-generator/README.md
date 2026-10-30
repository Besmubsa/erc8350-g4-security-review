# Git Changelog Generator

Generate a structured Markdown changelog from local Git history with Python 3.10+ and no third-party dependencies.

## Use it (3 steps)

1. From the project root, run `bash tools/changelog-generator/changelog.sh` (or `python3 tools/changelog-generator/changelog.py`).
2. To choose the starting revision and release label, run `bash tools/changelog-generator/changelog.sh --since v1.0.0 --version v1.1.0 --date 2026-10-30`.
3. Run the tests with `python3 -m unittest discover -s tools/changelog-generator -p 'test_*.py'`.

By default, the generator uses commits after the most recently created Git tag; if no tags exist, it uses all commits. It skips merge commits and groups commit subjects into **Added**, **Fixed**, **Changed**, and **Removed**. Use `--output path/to/CHANGELOG.md` to choose another destination.

The integration test creates a temporary Git repository, tags a release, adds a subsequent commit, and checks that only the post-tag commit appears in the changelog. No network access or real project modification is needed to run tests.

Commit messages are classified heuristically. Review the generated changelog before publishing a release.
