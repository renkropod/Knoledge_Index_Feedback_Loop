---
title: What not to write on your security clearance form (1988)
source: hacker_news
url: https://milk.com/wall-o-shame/security_clearance.html
points: 510
---

Title: What not to write on your security clearance form (1988)
Points: 510, Author: wizardforhire, Comments: 221

is a Git extension that records the AI coding session used to produce a commit. It attaches AI conversation transcripts as git notes, creating an audit trail for AI-assisted development.
git-memento solves a critical problem in AI-assisted development: when an AI assistant produces a commit, the conversation that led to that change is typically lost. Team members see
the AI was asked to change it, what alternatives were considered, or what constraints were given.
Creates commits with normal Git flow (
Attaches the AI session transcript to the commit using
Produces human-readable markdown notes
Keeps provider support extensible (Codex and Claude Code supported)
Works seamlessly with your existing Git workflow
Development teams using AI coding assistants (Codex, Claude Code) who want to maintain transparency, support code review, meet compliance requirements, or preserve context for debugging and onboarding.
Before using git-memento, you need:
or your provider's instructions
Install git-memento from the latest GitHub release:
curl -fsSL https://raw.githubusercontent.com/mandel-macaque/memento/main/install.sh
Detect your OS and architecture
Download the appropriate release binary
(or your configured install directory)
Prompt you to add the directory to your
After installation, verify git-memento is available:
Initialize git-memento for your repository. This stores provider configuration in local git metadata (
once per repository. The configuration is stored locally and won't affect other repositories.
Create a commit with an attached AI session note
: Use the session ID from your Claude session
Add user authentication feature
Check that the AI session transcript was attached to your commit:
You should see a markdown-formatted conversation with your AI provider showing the messages exchanged during the session.
Push your commit and sync the notes to your remote repository:
Pushes your commits to the remote
Configures fetch mappings so teammates can retrieve notes
Your team members can fetch the notes with:
Continue reading for more advanced features and commands.
stores configuration in local git metadata (
multiple times, and each value is forwarded to
--summary-skill session-summary-default -m
Without a session id, it copies the note(s) from the previous HEAD onto the amended commit
With a session id, it copies previous note(s) and appends the new fetched session as an additional session entry
A single commit note can contain sessions from different AI providers
--summary-skill <skill|default>
) stores a summary record instead of the full transcript
The CLI prints the generated summary and asks for confirmation
If rejected, you must provide a prompt to regenerate
maps to the repository skill at
skills/session-summary-default/SKILL.md
The default summary skill is always applied as a baseline; if a user-provided summary skill conflicts with it, user-provided instructions take precedence
Verify both notes after a summary run:
git notes --ref refs/not
