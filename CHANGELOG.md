# Changelog

Newest first. Every entry is written for users: a release's section becomes its GitHub Release
notes.

## 0.4.0 (2026-11-06)

- The re-ask is written in the language of your own words, not of text you pasted or a command
  you ran.
- It covers every decision still waiting on you, including ones asked before the agent's last
  message, and with several questions it ends on all of them together.
- When the decision changes what your product's users see, the live example shows it from their
  side.
- When a longer check would settle a close call, the agent offers that check as one of the
  answers instead of guessing.
- The skill no longer loads when the agent is about to ask a new question of its own, or when you
  have already answered.
- The plugin has an icon and listing details for the Anthropic plugin directory: a display name
  and links to the documentation, support and privacy sections.
- The README opens with a one-line install for Claude Code, Codex, Cursor and Gemini CLI, shows
  how to use reask on a single question in a form, and replaces the hand-written example with real
  output. It has a Privacy section: reask collects and sends nothing.
- CI checks the plugin with the plugin directory's own validation profile.

## 0.3.0 (2026-09-29)

- Every re-ask now starts from the context, whatever the question: what is being built, why the
  decision matters now, and every task number, document code or name from the session explained.
  0.2.0 cut this for questions with few options, which left short re-asks that could not be
  answered without scrolling back.
- Depth now follows the question's difficulty and the agent's confidence rather than the number of
  options: the less sure it is, the more evidence it gives, up to the facts on each side and what
  would tip a close call.
- A reference by number or code (a task, a ticket, a rule, a section, a pull request) now comes
  with what it says, so you never have to open it to follow the question.
- Every option again comes with pros and cons, however short.
- Asked several questions at once, you can bounce only the ones you cannot answer; each gets the
  same depth, and the answers you gave are kept.

## 0.2.0 (2026-09-29)

- A re-ask is now sized to what you are missing: a yes/no question or two familiar options comes
  back in a few lines, several options in a short briefing, and only a decision you have lost the
  thread of gets the full five-part briefing.
- Before recommending, the agent argues against its own first lean and checks the fact it rests
  on with a quick read-only look at your project. If that changes the recommendation, or surfaces
  a better option, the re-ask says so in one line and offers the new option as an answer.

## 0.1.0 (2026-09-29)

First release.

- The `/reask` skill: re-asks a pending question as a five-part briefing (where we are, a live
  example, options with pros and cons, a recommendation, one question) in under 500 words and in
  the user's language, or as a short form when the question is a simple yes or no.
- Install it with the Skills CLI (`npx skills add Nezhinskiy/reask`), as a Claude Code plugin,
  with the `reask` Python package, as a zip for claude.ai, or by copying `SKILL.md`.
- `reask install`, `reask uninstall` and `reask print`. Neither `install` nor `uninstall`
  replaces or deletes a copy you have edited without `--force`, and neither follows a symbolic
  link inside the skills directory.
- Every release is built in CI from its tag and carries build provenance attestations.
