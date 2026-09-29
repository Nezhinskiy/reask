# Security policy

reask is a set of instructions an AI agent loads and follows. That makes the text of
[`SKILL.md`](skills/reask/SKILL.md) the security-relevant artefact, more than the small installer
around it: anything that can change what an agent reads when it loads this skill can change what
the agent does in the user's session.

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting:**
<https://github.com/Nezhinskiy/reask/security/advisories/new>

That opens a private advisory only the maintainer can see. Please do **not** open a public issue
for anything listed under "What counts" below. If private reporting is unavailable to you, open a
public issue that says only "I have a security report and cannot use private reporting", without
details, and a private channel will be arranged.

This is a single-maintainer project: expect a first reply within a week. Reporters are credited
in the advisory and the changelog unless they ask otherwise.

## What counts

In scope:

- **Instruction integrity.** Any way the text an agent loads as this skill can differ from the
  reviewed `SKILL.md` at the tag or commit the user installed: a published package, Release asset
  or plugin source whose contents do not match the repository, or a build or release step that
  can be influenced from outside.
- **Skill-induced unsafe behaviour.** Wording in `SKILL.md` that leads an agent to take an action
  the user did not ask for: running commands, writing files beyond the scratch HTML file the skill
  describes, sending data anywhere, or acting on a choice the user has not made.
- **The installer.** Any way `reask install` or `reask uninstall` writes or deletes outside the
  skill folder it names, follows a link inside it, or removes a file it did not write.
- **The release channels.** Any way to publish to PyPI or create a GitHub Release without the
  maintainer's approval on the `pypi` environment, or to change `main` without a pull request.
  `main` is itself a release channel: the plugin marketplace and the Skills CLI install from it.

Out of scope:

- Prompt injection that reaches the agent through other content in the user's session. The skill
  asks the agent to restate a question the agent already asked; it does not change how the agent
  treats untrusted input.
- Anything that requires write access to the user's home directory or to this repository.

## Supported versions

reask is pre-1.0. Only the latest release is supported, and a security fix ships as a new patch
release. That release is what reaches every channel: Claude Code offers plugin users an update
only when `.claude-plugin/plugin.json`'s version changes, PyPI serves it to the next
`uvx reask install`, and Skills CLI users receive it with `npx skills update`.

## Verifying what you installed

Every Release asset and PyPI distribution carries a build provenance attestation. Check that a
file was built by this repository's release workflow from the tag you expect:

```bash
gh attestation verify reask-0.1.0-py3-none-any.whl --repo Nezhinskiy/reask \
  --signer-workflow Nezhinskiy/reask/.github/workflows/release.yml \
  --source-ref refs/tags/v0.1.0
```
