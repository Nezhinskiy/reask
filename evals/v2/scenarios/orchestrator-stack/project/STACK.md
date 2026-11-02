# Stack: config rework for nightjar 2.0

ADR-7 (accepted 2026-10-20): nightjar's settings move from `nightjar.ini` to `nightjar.toml`, and
all config code lives in one module. The work is split into three stacked PRs, each based on the
one below it. Merge bottom-up; tag 2.0 when the whole stack is on main.

| PR  | Branch                 | What                                                              | Child report                    | Review       | CI      |
|-----|------------------------|-------------------------------------------------------------------|---------------------------------|--------------|---------|
| #12 | cfg/extract            | Move settings parsing out of `cli.py` into `nightjar/config.py`   | runs/12-extract-config.md       | approved     | green   |
| #13 | cfg/toml               | Read `nightjar.toml`, remove the INI parser                       | runs/13-toml-config.md          | 1 approval   | green   |
| #14 | cfg/drop-legacy-paths  | Remove the `--legacy-paths` flag (deprecated since 1.6)           | runs/14-drop-legacy-paths.md    | not requested| running |

One child session per PR. Each wrote its report into runs/ when it finished and then stopped;
nothing has been merged yet.
