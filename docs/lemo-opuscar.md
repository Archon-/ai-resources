# Lemo-Opuscar

External toolbox. Recorded here so it stays findable, and so it is not copied into `skills/`.

- Repo: [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)
- Gallery: [lemomo-ai.github.io/lemo-opuscar](https://lemomo-ai.github.io/lemo-opuscar/)
- Author: Lemomo ([@lemomo_ai](https://github.com/lemomo-ai))

`scripts/fetch-sources.sh` does not touch it. `scripts/install.sh` does not link it.

## What it is

A library of 99 film styles for a coding agent, plus the guides and tools that turn a sentence into a short film. You pick a style and bring a story. The agent writes the film in code: canvas and WebGL frames, a score from free sample libraries, and text-to-speech narration. There is no video-generation model and no stock footage in the pipeline.

Each style is a `STYLE.md` (how it looks and sounds) and a short demo film made the same way. The agent also reads two guides from the upstream repo:

| File | Role |
| --- | --- |
| `DIRECTOR.md` | Story, sound, rhythm, camera, performance, self-checks |
| `TECHNIQUE.md` | Frame-by-frame rendering, voice, music, mixing |
| `styles/<style>/STYLE.md` | The look. The story stays yours. |

The styles are grouped by picture, not by topic: edit and documentary, painting, sketch, crafts, print, type, diagrams, cartoons, games, film and tape, screens, light, 3D, instruments, data and maps. The gallery has a page per style, with the demo, stills, and the sentence to paste.

Claude Fable, Opus, and Sonnet are the models the styles were tuned on. In Claude Code, set effort to high (`/effort high`). Other models may not reproduce the styles.

A film takes the agent about 30–60 minutes and a lot of tokens. The machine needs Node 20+, ffmpeg 7+, and Python 3.11+ (or uv). The agent installs the rest. Ubuntu 24.04’s ffmpeg 6.1 is too old; use a static ffmpeg 7 build. Default picture is 1920×1080 at 24 fps. Some styles set their own frame rate. Other sizes are a request, not a setting in this repo.

Three styles draw characters with an image generator you supply: Manga Panels, Text Flash Cuts, and Comic History Cartoon. They are marked in the upstream style list. Without that generator those three cannot start. Every other style runs without one.

You can also change a library style, or start from a blank description, and keep the result in `~/lemo-my-styles/<name>/`. Later films name it the same way as a library style. Updates and uninstall leave that folder alone.

## How to use it

Claude Code, from any folder:

```bash
claude plugin marketplace add lemomo-ai/lemo-opuscar
claude plugin install lemo-opuscar@lemolab
```

The first film downloads the guides, tools, and style prompts to `~/lemo-opuscar`, shared across films. The film’s own project, from source to the finished video, is written in the folder you started from.

Then, in Claude Code:

```text
Make a 45-second film in the watercolor style about the coffee farm my family runs. Warm female narrator.
```

Name the style in English, in Chinese, or by its folder. Length, narrator, your own photos, and your own music are optional additions to that sentence.

`/lemo-opuscar:lemo-opuscar` with no other text asks which language to use, then whether you want a library style, a style of your own, or a film in a style you already saved. It also asks about voice, music, or other material, and whether to stop once at a storyboard.

Update, then restart Claude Code. The copy in `~/lemo-opuscar` refreshes on the next film:

```bash
claude plugin marketplace update lemolab && claude plugin update lemo-opuscar@lemolab
```

Third-party marketplaces such as lemolab stay on manual update until you turn auto-update on. In Claude Code: `/plugin`, Marketplaces, lemolab, Enable auto-update.

Uninstall, then delete `~/lemo-opuscar` if you want the downloaded library gone:

```bash
claude plugin uninstall lemo-opuscar@lemolab
```

`~/lemo-my-styles/` stays. Delete that folder yourself when you want those styles gone.

Another agent can use the same skill by copying `plugin/skills/lemo-opuscar/` into that agent’s skills folder. `scripts/setup.sh` clones the library into `~/lemo-opuscar` on first run. This hub does not copy that skill.

A clone is the other path. Films then go in `films/<name>/` inside the clone:

```bash
git clone https://github.com/lemomo-ai/lemo-opuscar.git
cd lemo-opuscar
claude
```

After `git pull` in that clone, run `sh plugin/skills/lemo-opuscar/scripts/setup.sh deps` once. If you installed the voice or music packages, run `sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice music` instead.

## Why it stays upstream

`plugin/skills/lemo-opuscar/` is `SKILL.md` plus `scripts/setup.sh`. With no arguments, `setup.sh` picks a library path: `$LEMO_OPUSCAR_HOME` if set, otherwise the git checkout you are standing in when it already has `AGENTS.md` and `core/render`, otherwise `~/lemo-opuscar`. When that path is not a library, the script clones `main` (`git clone --depth 1 --sparse`). The sparse checkout keeps the guides, `core/`, `tools/`, and each `STYLE.md`. A clone the script created is marked `lemo.managed`. The next run of that clone fetches `origin main` and hard-resets to that tip.

A linked copy can make a film, because that script downloads the library. It stays out of `skills/` because the download follows upstream `main`. This hub pins vendored trees to commits in `docs/sources.lock.json`, and `scripts/check_updates.py` compares those pins. A copy here would not be the tree the next film runs.

Upstream also splits the licence. Code (`core/`, `tools/`, `styleboard/`, plugin scripts, demo code) is MIT. Markdown, including each `STYLE.md` and the guides, is CC BY-NC 4.0, with an extra permission to read and adapt those docs while making a film, including a commercial or client film, and to ship the adapted docs inside that film’s project files. Selling the docs, or putting them into another product, needs a commercial licence from the author. Demo films and stills are CC BY 4.0, with exclusions called out in the upstream `LICENSE` (Clawd, some third-party interfaces, and six narration tracks). Films you make with the library are yours.

This file is a pointer. It does not copy those prompts, guides, or films. Read the upstream `LICENSE` and `REUSE.toml` before reusing anything from that repo.
