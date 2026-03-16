---
title: A new California law says all operating systems need to have age verification
source: hacker_news
url: https://www.pcgamer.com/software/operating-systems/a-new-california-law-says-all-operating-systems-including-linux-need-to-have-some-form-of-age-verification-at-account-setup/
points: 829
---

Title: A new California law says all operating systems need to have age verification
Points: 829, Author: WalterSobchak, Comments: 734

macOS-native sandboxing for local agents. Move fast, break nothing.
chance of disaster makes it a matter of
a fine-tuned MacBook Pro, crafted to perfection
chance — enforced by the kernel.
Safehouse denies write access outside your project directory. The kernel blocks the syscall before any file is touched.
rm: ~/: Operation not permitted
All agents work perfectly in their sandboxes, but can't impact anything outside it.
Agents inherit your full user permissions. Safehouse flips this — nothing is accessible unless explicitly granted.
Install with Homebrew or download the single shell script, then run your agent inside it. No build step, no dependencies beyond Bash and macOS.
eugene1g/safehouse/agent-safehouse
# Or download the single self-contained script
https://github.com/eugene1g/agent-safehouse/releases/latest/download/safehouse.sh
# 2. Run any agent inside Safehouse
Safehouse automatically grants read/write access to the selected workdir (git root by default) and read access to your installed toolchains. Most of your home directory — SSH keys, other repos, personal files — is denied by the kernel.
See it fail — proof the sandbox works
Try reading something sensitive inside safehouse. The kernel blocks it before the process ever sees the data.
# Try to read your SSH private key — denied by the kernel
# cat: /Users/you/.ssh/id_ed25519: Operation not permitted
# Try to list another repo — invisible
# ls: /Users/you/other-project: Operation not permitted
# But your current project works fine
# README.md  src/  package.json  ...
Safe by default with shell functions
Add these to your shell config and every agent runs inside Safehouse automatically — you don't have to remember. To run without the sandbox, use
# Sandboxed — the default. Just type the command name.
--dangerously-bypass-approvals-and-sandbox
# Unsandboxed — bypass the function with `command`
# command claude               — plain interactive session
# Sandboxed helpers without overriding the original binary names.
claude --dangerously-skip-permissions
codex --dangerously-bypass-approvals-and-sandbox
Generate your own profile with an LLM
Use a ready-made prompt that tells Claude, Codex, Gemini, or another model to inspect the real Safehouse profile templates, ask about your home directory and toolchain, and generate a least-privilege `sandbox-exec` profile for your setup.
The guide also tells the LLM to ask about global dotfiles, suggest a durable profile path like
, offer a wrapper that grants the current working directory, and add shell shortcuts for your preferred agents.
