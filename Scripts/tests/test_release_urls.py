from pathlib import Path
import plistlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FEED_URL = "https://github.com/Beastry/Octoshot/releases/latest/download/appcast.xml"
DOWNLOAD_PREFIX = "https://github.com/Beastry/Octoshot/releases/download/v${VERSION}/"


class ReleaseURLTests(unittest.TestCase):
    def test_feed_url(self):
        with (ROOT / "Octoshot/Info.plist").open("rb") as source:
            info = plistlib.load(source)
        self.assertEqual(info["SUFeedURL"], FEED_URL)

    def test_default_download_url(self):
        script = (ROOT / "Scripts/generate-appcast.sh").read_text()
        self.assertIn(
            'DOWNLOAD_URL="${DOWNLOAD_URL:-'
            + DOWNLOAD_PREFIX
            + '${DMG_BASENAME}}"',
            script,
        )

    def test_appcast_generator_url_arguments(self):
        script = (ROOT / "Scripts/generate-appcast.sh").read_text()
        for option, expected in (
            ("--download-url-prefix", DOWNLOAD_PREFIX),
            ("--link", FEED_URL),
        ):
            with self.subTest(option=option):
                match = re.search(re.escape(option) + r'\s+"([^"]+)"', script)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), expected)

    def test_no_legacy_release_url_defaults(self):
        for name in ("Octoshot/Info.plist", "Scripts/generate-appcast.sh"):
            text = (ROOT / name).read_text()
            for legacy in (
                "github.com/neardws/Octoshot",
                "www.neardws.com/Octoshot",
                "https://beastry.github.io/Octoshot/appcast.xml",
            ):
                with self.subTest(path=name, legacy=legacy):
                    self.assertNotIn(legacy, text)

    def test_generator_keeps_feed_out_of_published_website(self):
        script = (ROOT / "Scripts/generate-appcast.sh").read_text()
        self.assertIn('APPCAST_PATH="${APPCAST_PATH:-dist/appcast.xml}"', script)
        self.assertNotIn("website/public/appcast.xml", script)
        self.assertIn('python3 Scripts/check-arm64-appcast.py "$STAGE/appcast.xml"', script)

    def test_website_repository_urls(self):
        config = (ROOT / "website/src/config/assets.ts").read_text()
        for key, expected in (
            ("repo", "Beastry/Octoshot"),
            ("releasesLatest", "https://github.com/Beastry/Octoshot/releases/latest"),
            ("apiLatest", "https://api.github.com/repos/Beastry/Octoshot/releases/latest"),
        ):
            with self.subTest(key=key):
                match = re.search(re.escape(key) + r":\s*'([^']+)'", config)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), expected)

    def test_settings_and_landing_repository_urls(self):
        settings = (ROOT / "Octoshot/Preferences/AppSettings.swift").read_text()
        self.assertIn(
            'static let repositoryURL = URL(string: "https://github.com/Beastry/Octoshot")!',
            settings,
        )
        landing = (ROOT / "website/src/i18n/ui.ts").read_text()
        for key, suffix in (
            ("RELEASE_URL", "/releases/latest"),
            ("REPO_URL", ""),
            ("ISSUES_URL", "/issues"),
        ):
            with self.subTest(key=key):
                self.assertIn(
                    f"export const {key} = 'https://github.com/Beastry/Octoshot{suffix}';",
                    landing,
                )


if __name__ == "__main__":
    unittest.main()
