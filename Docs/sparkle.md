# Sparkle in-app updates

Octoshot uses [Sparkle 2](https://sparkle-project.org/) for signed, notarized update delivery.

## Feed URL

New builds from this checkout read:

`https://github.com/Beastry/Octoshot/releases/latest/download/appcast.xml`

The official feed is an asset of the latest published stable GitHub Release. The reusable workflow uploads the signed DMG, its SHA-256 checksum, and `appcast.xml` to a **draft** only. Draft assets do not serve the public latest-download feed. Human publication as **stable/latest**, after the run completes and the artifacts are reviewed, is the ship switch. Until a stable/latest release carries this asset, the new URL may return 404; changing this checkout does not publish a feed.

The post-#128 Pages URL, `https://beastry.github.io/Octoshot/appcast.xml`, is no longer the official feed for new builds. GitHub Releases do not update Pages automatically. This PR leaves the existing `website/public/appcast.xml` release artifact untouched and does not deploy or change the website.

### Already-installed clients are not migrated

Already-installed v0.3.2 (and earlier) builds still request `https://www.neardws.com/Octoshot/appcast.xml`, which currently returns HTTP 404 (verified November 14, 2026). Changing `SUFeedURL` in this repository only affects newly built releases: it does **not** make those old clients compatible or migrate their update URL.

Compatibility remains unsolved for both the old domain and any builds using the post-#128 Pages feed. A future, separately authorized plan is a minimal HTTPS 301 for the www/apex `/Octoshot/appcast.xml` path to the chosen official feed, or to the same Pages path with a separately maintained compatibility feed. Other `/Octoshot` paths would need explicit path-preserving redirects. Clients that already use Pages would need a separately maintained feed or redirect there too. Validate legacy Sparkle compatibility before enabling any redirect. No DNS, Cloudflare, personal-site, or Pages compatibility changes are made here.

## Checking for updates

- Menu bar **Octoshot → Check for Updates…** (简体：**检查更新…**)
- **Settings → About → Check for Updates…**

Automatic checks run once per day (`SUScheduledCheckInterval` = 86400). Downloads are **not** installed without user confirmation (`SUAutomaticallyUpdate` = false).

Debug builds and non-`.app` runs do not start Sparkle (no error dialogs when `SUFeedURL` is absent from the running bundle).

## Signing keys (maintainers)

Sparkle uses an Ed25519 key pair:

1. On a Mac, run:

   ```bash
   bash Scripts/generate-sparkle-keys.sh
   ```

   This uses Sparkle’s `generate_keys`, stores the private key in your login Keychain, and exports:

   `~/octoshot-private/sparkle/eddsa_priv.key`

2. Copy the printed **public** key into `Octoshot/Info.plist` as `SUPublicEDKey` (only the public key belongs in git).

3. **Never commit** `eddsa_priv.key` or any Keychain export. The repo `.gitignore` lists common private-key paths.

If you regenerate keys, every future appcast must be signed with the matching private key. Without the private key that corresponds to `SUPublicEDKey`, you must generate a new pair and ship a release that updates the public key in the app.

For the reusable workflow, the matching exported base64 Ed25519 private key is supplied as `SPARKLE_ED_PRIVATE_KEY`; it is passed to Sparkle tooling on stdin. No private key belongs in git or a release asset.

## Preparing a draft with GitHub Actions

`.github/workflows/release.yml` is a thin caller of `Beastry/macos-release/.github/workflows/release.yml`, with both `uses` and `toolkit-ref` pinned to `017a72f883a47b375ac5e653e78bfd0befdc3212`. The toolkit's separate GPL license PR [#2](https://github.com/Beastry/macos-release/pull/2) is unmerged and changes only license/docs files, so this caller uses the reviewed published main SHA. An optional follow-up pin bump can follow that merge. Octoshot's GPL-3.0-only first-party grant from #129 is preserved.

The release caller has only a `workflow_dispatch` trigger; existing `build.yml` runs app/URL tests on pull requests without release credentials. Real preparation requires a separately authorized dispatch **from main**, after review/merge and credential setup. A PR-branch dispatch cannot start real notarization: both the caller and toolkit enforce the default-branch boundary, and the toolkit requires source reachability from the default branch. The tag input defaults to `v0.3.3`; this integration leaves the app at **0.3.3 / build 6**. The workflow does not create or push tags.

The real job inherits the toolkit defaults: `runs-on: xcode-27`, `XCODE_APP=/Applications/Xcode_27.app`, and a 120-minute timeout. It installs XcodeGen if needed and runs this repository's `bash Scripts/package.sh`, using the full `project.yml` with MLX, arm64-only Release builds, embedded CLI/llama helpers, and existing inside-out signing of Sparkle XPC services, `Autoupdate`, `Updater.app`, frameworks, and the app. It does not use the MLX stub project.

The caller has `contents: read` by default. Only its dispatch job grants the `contents: write` ceiling required by the reusable workflow's final draft upload; the toolkit keeps guard/package jobs at read and gives the draft job no signing secrets. There is no `secrets: inherit`. Exactly these nine Actions secret names are required for a real run:

- `DEVELOPER_ID_P12_BASE64`
- `DEVELOPER_ID_P12_PASSWORD`
- `DEVELOPER_ID_IDENTITY`
- `APPLE_TEAM_ID`
- `KEYCHAIN_PASSWORD`
- `ASC_API_KEY_ID`
- `ASC_API_ISSUER_ID`
- `ASC_API_KEY_P8_BASE64`
- `SPARKLE_ED_PRIVATE_KEY`

Repository Actions secret-name enumeration on November 14, 2026 returned **no configured names**. Organization/environment secret availability is not assumed. No secret values were inspected or configured by this PR.

The toolkit imports an ephemeral keychain and ASC API key file. `Scripts/package.sh` accepts `DEVELOPER_ID_IDENTITY`, `KEYCHAIN_PATH`, `CODESIGN_FLAGS` (default `--options runtime --timestamp`), `APPLE_TEAM_ID`, and `ASC_API_KEY_PATH` / `ASC_API_KEY_ID` / `ASC_API_ISSUER_ID`. Every signing invocation receives the selected keychain as a separate quoted argument. Intermediate Xcode builds disable automatic signing; the existing final Developer ID signing pass owns nested signatures. A partially configured API authentication fails before building rather than falling back to a local profile.

Packaging notarizes and staples **both the app and DMG**, so the caller sets `already-notarized: true`. The toolkit still validates the DMG staple and Gatekeeper, independently checks the packaged app's signature/team/runtime/plist, verifies the Sparkle signature against its public key, and generates the feed/checksum from the final stapled DMG. Only `dist/Octoshot-v*-macOS.dmg` is selected (exactly one file); local ZIP/log outputs are not uploaded. API credentials take precedence over local profiles. Local maintainers can continue using the `Octoshot-notary` default, or `NOTARY_PROFILE=MijiaBar-notary bash Scripts/package.sh`; explicitly empty `NOTARY_PROFILE` skips notarization only when no API credentials are supplied.

The pinned toolkit source was inspected for its guard, runner, five composites, signing/feed/build-order validation, tests, cleanup, and draft-only API behavior. It checks that a build is strictly higher than the latest published appcast, refuses to modify any published release (including prereleases), and checks draft state before each upload. It sets `draft: true`, `prerelease: false`, and `make_latest: "false"`. Wait for the run to finish before any human publication; later explicitly select stable/latest. Its no-secret tests cannot establish real signing/notarization success.

No real release workflow, package build, notarization, tag, or release is started as part of this integration PR. The local Mac mini has Command Line Tools only, and the installed 0.3.2 app is not replaced.

## Local appcast generation (no upload)

Official CI generates the appcast through the toolkit. For a separately authorized local packaging session, `Scripts/generate-appcast.sh` can generate a local `dist/appcast.xml` from a notarized DMG:

```bash
export VERSION=0.3.3
export DMG_PATH=dist/Octoshot-v0.3.3-macOS.dmg
# SPARKLE_KEY defaults to ~/octoshot-private/sparkle/eddsa_priv.key
bash Scripts/generate-appcast.sh
```

`APPCAST_PATH` optionally selects another local output. This script neither uploads assets nor rewrites `website/public/appcast.xml`. Its default enclosure and `--download-url-prefix` use `https://github.com/Beastry/Octoshot/releases/download/v${VERSION}/`; `--link` uses the official latest-download feed. Any manual artifact upload/publication requires separate authorization and review.

## Apple Silicon-only releases

Release builds now set `ARCHS=arm64` for the app, CLI, and embedded MLX framework. The app hard-links MLX, so retaining an Intel app slice without redesigning that boundary is not supported. Intel Macs cannot launch these releases; keep their last compatible universal release available. `LSArchitecturePriority` and `LSMinimumSystemVersion` are unchanged.

The caller passes `hardware-requirements: arm64` to the toolkit's appcast generator. Local Sparkle 2.10's `generate_appcast` detects an arm64-only executable and emits `<sparkle:hardwareRequirements>arm64</sparkle:hardwareRequirements>`; `Scripts/generate-appcast.sh` checks this before writing its local output. The app's Sparkle runtime remains 2.10 or later; the toolkit separately pins 2.8.1 signing tools. Older Sparkle clients may not honor this field: verify the updater version in every supported Intel release before publishing, or keep those clients on a separate legacy feed. An Info.plist change in the new app cannot protect already-installed clients.

The historical Pages appcast remains a separate release artifact, not a placeholder for or mirror of future GitHub Release assets.
