---
title: Show HN: OpenClaw-superpowers – Self-modifying skill library for OpenClaw agents
source: hacker_news
url: https://github.com/ArchieIndian/openclaw-superpowers
---

Title: Show HN: OpenClaw-superpowers – Self-modifying skill library for OpenClaw agents
Score: 8 points by Arkid
Comments: 0

I built a skill library for OpenClaw (always-on AI agent runtime, not session-based) where the agent can teach itself new behaviors during normal conversation.<p>The idea: you tell your agent &quot;every time I ask for a code review, always check for security issues first.&quot; It invokes a create-skill skill, writes a new SKILL.md, and that behavior is live immediately — no restart, no config change, no developer required.<p>What I think is actually useful (the safety cluster):<p>•    loop-circuit-breaker: OpenClaw retries ALL errors identically. This halts on the 2nd identical failure before it burns your context window.
•    spend-circuit-breaker: No built-in cap in OpenClaw. This tracks cumulative API cost and pauses non-essential crons at configurable thresholds.
•    workspace-integrity-guardian: Hashes SOUL.md, AGENTS.md, MEMORY.md. A corrupted SOUL.md = hijacked agent that survives restarts.
•    dangerous-action-guard: Explicit confirmation before rm -rf, git push --force, emails, financial actions. With audit log.
•    prompt-injection-guard: Scans external content (web scrapes, emails, docs) before acting on it.<p>Also: fact-check-before-trust (secondary verification for factual claims), project-onboarding (auto-generates PROJECT.md from a codebase), skill-vetting (security scanner — ~17% of community skills are malicious).
