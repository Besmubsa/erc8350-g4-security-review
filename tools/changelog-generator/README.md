# Git Changelog Generator

Generate a structured Markdown changelog from local Git history with Python 3.10+ and no third-party dependencies.

## Use it

1. Run `python tools/changelog-generator/changelog.py` from the repository root.
2. To choose the starting revision and release label, run `python tools/changelog-generator/changelog.py --since v1.0.0 --version v1.1.0 --date 2026-10-30`.
3. Run the unit tests with `python -m unittest discover -s tools/changelog-generator -p 'test_*.py'`.

By default, the generator uses commits after the most recently created Git tag; if no tags exist, it uses all commits. It skips merge commits and groups commit subjects into **Added**, **Fixed**, **Changed**, and **Removed**. Use `--output path/to/CHANGELOG.md` to choose another destination.

Commit messages are classified heuristically. Review the generated changelog before publishing a release.
