# Security policy

reask is a set of instructions an AI agent loads and follows. That makes the text of
[`SKILL.md`](SKILL.md) the security-relevant artefact, more than the small installer around it:
anything that can change what an agent reads when it loads this skill can change what the agent
does in the user's session.

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting:**
<https://github.com/Nezhinskiy/reask/security/advisories/new>

That opens a private advisory only the maintainer can see. Please do **not** open a public issue
for anything listed under "What counts" below.

If private reporting is unavailable to you, open a public issue that says only "I have a
security report and cannot use private reporting", without details, and a private channel will
be arranged.

### What to include

The skill version (`metadata.version` in `SKILL.md`, or `reask --version`), how it was installed
(plugin, Skills CLI, Python package, zip, by hand), the agent and its version, and the smallest
reproduction you have: the prompt or file content, what the agent did, and what it should have
done.

### What to expect

This is a single-maintainer project, so read these as intentions rather than guarantees:

| | |
|---|---|
| First response | within 7 days |
| Assessment and a plan | within 14 days |
| Fix released | as soon as it is ready; you will be told the date |
| Credit | in the advisory and the changelog, unless you ask otherwise |

## What counts

In scope:

- **Instruction integrity.** Any way the text an agent loads as this skill can differ from the
  reviewed `SKILL.md` at the tag or commit the user installed: a published package, Release asset
  or plugin source whose contents do not match the repository, or a build or release step that
  can be influenced from outside.
- **Skill-induced unsafe behaviour.** Wording in `SKILL.md` that leads an agent to take an action
  the user did not ask for: running commands, writing files beyond the scratchpad file the skill
  describes, sending data anywhere, or acting on a choice the user has not made.
- **The installer.** Any way `reask install` or `reask uninstall` writes or deletes outside the
  skill directory it names, or follows a path the user did not give it.
- **The release pipeline.** Any way to publish to PyPI or create a GitHub Release without the
  maintainer's approval on the `pypi` environment.

Out of scope:

- Prompt injection that reaches the agent through other content in the user's session. The skill
  asks the agent to restate a question the agent already asked; it does not change how the agent
  treats untrusted input.
- Anything that requires write access to the user's home directory or to this repository.

## Supported versions

reask is pre-1.0. Only the latest release is supported; fixes land on `main` and in the next
release. Plugin and Skills CLI installs follow `main`, so they receive a fix as soon as it merges.

## Verifying what you installed

Every Release asset and PyPI distribution carries a build provenance attestation:

```bash
gh attestation verify reask-0.1.0-py3-none-any.whl --repo Nezhinskiy/reask
```
