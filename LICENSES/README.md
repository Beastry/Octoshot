# First-party license scope

First-party Octoshot material in this repository is released under the
**GNU General Public License, version 3 only**.

| | |
| --- | --- |
| SPDX identifier | `GPL-3.0-only` |
| License text | [`LICENSE`](../LICENSE) (the unmodified GNU GPL v3 from the Free Software Foundation) |
| Copyright | Copyright (c) 2026 neardws |
| Version grant | Version 3 only. This project does not grant the option to choose a later version of the GNU GPL. |

The `LICENSE` file is the license text itself and is left unmodified, including
the Free Software Foundation’s “How to Apply These Terms” appendix. That
appendix is guidance. The version that applies to this project is the
`GPL-3.0-only` grant in this file and in the README license sections.

## What “first-party” covers

First-party material is the source, documentation, scripts, website copy, and
original artwork written for Octoshot by the copyright holder named above.
That includes the original cartoon octopus mascot and the brand images in this
repository. The mascot is an original character and is not based on an existing
copyrighted character.

Per-file SPDX headers were not added to source files. The grant for the current
tree is this repository-level notice.

## MIT rights from before this change

Until this change, the repository was distributed under the MIT License,
Copyright (c) 2026 neardws. The MIT grant is irrevocable. Anyone who already
received a copy under that license keeps the MIT rights for **that copy**.
That includes tagged releases and any historical commit whose tree still
contains the MIT `LICENSE`.

The original copyright line and permission notice are preserved byte for byte
in [`MIT-legacy.txt`](MIT-legacy.txt), after a short preface. `MIT-legacy.txt`
records the earlier grant. It is not the license for the current first-party
tree.

Git history also contains commits contributed while the project license was
MIT, including commits by skywalker (`lovestarsni@gmail.com`). This change does
not name a new copyright owner and does not revoke the MIT permission under
which those contributions were received. MIT is compatible with GPL-3.0-only,
so the project can distribute the current tree under GPL-3.0-only while that
preserved MIT notice remains in place for the pre-migration grant.

## Third-party components

Third-party code, model weights, and their notices stay under their own
licenses. This change does not relicense them and does not add owners or
restrictions.

Existing project attribution, kept as already documented:

- **Sparkle 2.** Not vendored in this repository. `project.yml` and
  `project.ci.yml` depend on `https://github.com/sparkle-project/Sparkle` from
  2.10.0. Upstream stays under the Sparkle project’s license (MIT, plus the
  additional notices shipped in that project’s `LICENSE`).
- **mlx-swift-lm** 2.29.3 (`ml-explore/mlx-swift-lm`): Apache-2.0, as recorded
  in `Docs/EMBEDDED_AI.md` and Settings → About.
- **SmolVLM2 weights** (`mlx-community/SmolVLM2-500M-Video-Instruct-mlx-4bit`):
  Apache-2.0 (Hugging FaceTB / mlx-community). Downloaded on demand into
  Application Support. Not stored in git.
- **pix2tex-mfr GGUF** (`cstr/pix2tex-mfr-gguf`): MIT (cstr). Downloaded on
  demand. Not stored in git.
- **llama.cpp binaries** (pinned release `b11514`, `llama-mtmd-cli` and its
  runtime libraries): MIT, as recorded in `Docs/EMBEDDED_AI.md`. Fetched by
  `Scripts/fetch-llama-mtmd.sh`. Not stored in git.
- **MiniCPM-V-4.6 MLX catalog entry** (`mlx-community/MiniCPM-V-4.6-4bit`):
  Apache-2.0 (MiniCPM / mlx-community), as stated by
  `EmbeddedModelID.licenseNote`. Not bundled. The optional diary model
  `openbmb/minicpm-v4.7:1b` is installed by the user through Ollama and is not
  part of this relicensing. This repository does not add a license line for
  that weight beyond the existing catalog note for the MLX entry.
- **Website npm dependencies** keep the licenses already recorded on each
  package in `website/package-lock.json`.

Settings → About keeps the existing embedded-weight attribution sentence.
