import unittest

from changelog import classify, render


class ChangelogTests(unittest.TestCase):
    def test_conventional_commit_categories(self):
        cases = {
            "feat: add export endpoint": "Added",
            "fix: handle empty response": "Fixed",
            "remove: obsolete flag": "Removed",
            "docs: explain configuration": "Changed",
            "refactor(core): simplify parser": "Changed",
        }
        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(classify(subject), expected)

    def test_plain_language_categories(self):
        self.assertEqual(classify("Add CSV export"), "Added")
        self.assertEqual(classify("Fix crash on startup"), "Fixed")
        self.assertEqual(classify("Delete deprecated option"), "Removed")

    def test_render_groups_entries_and_escapes_hash(self):
        output = render(
            [("a1b2c3d", "feat: add export"), ("d4e5f6a", "fix: retry request")],
            "v1.2.0",
            "2026-10-30",
        )
        self.assertIn("## v1.2.0 — 2026-10-30", output)
        self.assertIn("### Added", output)
        self.assertIn("- feat: add export (`a1b2c3d`)", output)
        self.assertIn("### Fixed", output)

    def test_empty_history_is_explicit(self):
        self.assertIn("No commits found for this release.", render([], "Unreleased", "2026-10-30"))


if __name__ == "__main__":
    unittest.main()
