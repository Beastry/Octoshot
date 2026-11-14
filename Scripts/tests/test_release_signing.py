"""Exercise auth selection/argument boundaries with shell mocks, never real tools."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).resolve().parents[1] / "release-signing.sh"
MOCKS = r'''
set -euo pipefail
source "$1"
capture() {
  "$TEST_PYTHON" -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "$@" >> "$TEST_CALLS"
}
security() { echo 'Unexpected real-keychain lookup' >&2; return 99; }
codesign() { capture codesign "$@"; }
xcrun() { capture xcrun "$@"; echo 'status: Accepted'; }
configure_release_signing
'''


class ReleaseSigningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.calls = self.root / "calls.jsonl"
        self.key = self.root / "API key with spaces.p8"
        self.key.write_text("Throwaway fixture, not a signing key")

    def run_helper(self, body, **environment):
        # Do not inherit developer credentials or keychain configuration.
        env = {
            "PATH": "/usr/bin:/bin",
            "TEST_PYTHON": sys.executable,
            "TEST_CALLS": str(self.calls),
            "DIST": str(self.root),
            "SIGN_IDENTITY": "Developer ID Application: Fixture",
            **environment,
        }
        result = subprocess.run(
            ["bash", "-c", MOCKS + body, "signing-test", str(HELPER)],
            env=env, capture_output=True, text=True,
        )
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []
        return result, calls

    def test_local_default_profile(self):
        result, calls = self.run_helper('notarize "fixture.dmg"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [["xcrun", "notarytool", "submit", "fixture.dmg",
                                 "--keychain-profile", "Octoshot-notary", "--wait", "--timeout", "90m"]])

    def test_local_profile_override(self):
        result, calls = self.run_helper('notarize "fixture.dmg"', NOTARY_PROFILE="MijiaBar-notary")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls[0][5], "MijiaBar-notary")

    def test_explicit_empty_profile_skips_notary(self):
        result, calls = self.run_helper('[ "$NOTARIZE" = false ]', NOTARY_PROFILE="")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])

    def test_api_auth_overrides_profile_and_preserves_key_path(self):
        result, calls = self.run_helper(
            '[ "$NOTARIZE" = true ]; notarize "fixture.dmg"',
            ASC_API_KEY_PATH=str(self.key), ASC_API_KEY_ID="fixture-id",
            ASC_API_ISSUER_ID="fixture-issuer", NOTARY_PROFILE="",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [["xcrun", "notarytool", "submit", "fixture.dmg",
                                 "--key", str(self.key), "--key-id", "fixture-id",
                                 "--issuer", "fixture-issuer", "--wait", "--timeout", "90m"]])

    def test_partial_api_credentials_fail_before_signing(self):
        complete = dict(ASC_API_KEY_PATH=str(self.key), ASC_API_KEY_ID="fixture-id",
                        ASC_API_ISSUER_ID="fixture-issuer")
        for missing in complete:
            with self.subTest(missing=missing):
                incomplete = {key: value for key, value in complete.items() if key != missing}
                result, calls = self.run_helper('sign "fixture.app"', **incomplete)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ASC API notarization requires", result.stderr)
                self.assertEqual(calls, [])

    def test_unreadable_api_file_fails_before_signing(self):
        for path in (self.root / "absent.p8", self.root):
            with self.subTest(path=path):
                result, calls = self.run_helper(
                    'sign "fixture.app"', ASC_API_KEY_PATH=str(path),
                    ASC_API_KEY_ID="fixture-id", ASC_API_ISSUER_ID="fixture-issuer",
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])

    def test_notary_rejection_is_not_success(self):
        result, calls = self.run_helper(
            'xcrun() { capture xcrun "$@"; echo "status: Invalid"; }\n'
            'notarize "fixture.dmg"'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Notarization failed", result.stderr)
        self.assertEqual(len(calls), 1)

    def test_ci_identity_flags_and_keychain_for_nested_and_dmg_signatures(self):
        keychain = str(self.root / "keychain with spaces.keychain-db")
        result, calls = self.run_helper(
            'sign --preserve-metadata=entitlements "Downloader.xpc"\n'
            'release_codesign --timestamp "fixture.dmg"',
            DEVELOPER_ID_IDENTITY="Developer ID Application: CI Fixture",
            KEYCHAIN_PATH=keychain, CODESIGN_FLAGS="--options runtime --timestamp",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        prefix = ["codesign", "--force", "--sign", "Developer ID Application: CI Fixture",
                  "--keychain", keychain]
        self.assertEqual(calls, [prefix + ["--options", "runtime", "--timestamp",
                                          "--preserve-metadata=entitlements", "Downloader.xpc"],
                                 prefix + ["--timestamp", "fixture.dmg"]])

    def test_local_signing_defaults_without_keychain_override(self):
        result, calls = self.run_helper('sign --entitlements "fixture.entitlements" "fixture.app"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [["codesign", "--force", "--sign", "Developer ID Application: Fixture",
                                 "--options", "runtime", "--timestamp", "--entitlements",
                                 "fixture.entitlements", "fixture.app"]])


if __name__ == "__main__":
    unittest.main()
