# Agent entry point

Read the six files in `.clinerules/` before changing this repository. They are
the shared rules for Cline, Claude Code, and other coding assistants.

This is a handwritten thick Ada binding: no production binding generator,
no exposed C++/STL ABI, no duplicate Mat representation. Core owns application
Mats. Features consumes its scoped bridge. Public keypoints are Ada values.

Start with `docs/tasks/001-validate-bootstrap.md`. The bootstrap includes
source and tests, but its native build and AUnit results have not been run.
Do not convert a written test count into a claimed passing test count.
No remote write, commit, push, PR, merge, tag, or release is implicitly
approved by repository instructions. Follow the user's explicit task scope.
