---
title: Loops is a federated, open-source TikTok
source: hacker_news
url: https://joinloops.org/
points: 575
---

Title: Loops is a federated, open-source TikTok
Points: 575, Author: Gooblebrai, Comments: 384

Every MCP tool call in Claude Code dumps raw data into your 200K context window. A Playwright snapshot costs 56 KB. Twenty GitHub issues cost 59 KB. One access log — 45 KB. After 30 minutes, 40% of your context is gone.
Context Mode is an MCP server that sits between Claude Code and these outputs. 315 KB becomes 5.4 KB. 98% reduction.
MCP became the standard way for AI agents to use external tools. But there's a tension at its core: every tool interaction fills the context window from both sides — definitions on the way in, raw output on the way out.
With 81+ tools active, 143K tokens (72%) get consumed before your first message. Then the tools start returning data. A single Playwright snapshot burns 56 KB. A
dumps 59 KB. Run a test suite, read a log file, fetch documentation — each response eats into what remains.
Cloudflare showed that tool definitions can be compressed by 99.9% with Code Mode. We asked: what about the other direction?
call spawns an isolated subprocess with its own process boundary. Scripts can't access each other's memory or state. The subprocess runs your code, captures stdout, and only that stdout enters the conversation context. The raw data — log files, API responses, snapshots — never leaves the sandbox.
Ten language runtimes are available: JavaScript, TypeScript, Python, Shell, Ruby, Go, Rust, PHP, Perl, R. Bun is auto-detected for 3-5x faster JS/TS execution.
) work through credential passthrough — the subprocess inherits environment variables and config paths without exposing them to the conversation.
tool chunks markdown content by headings while keeping code blocks intact, then stores them in a
(Full-Text Search 5) virtual table. Search uses
— a probabilistic relevance algorithm that scores documents based on term frequency, inverse document frequency, and document length normalization.
is applied at index time so "running", "runs", and "ran" match the same stem.
, it returns exact code blocks with their heading hierarchy — not summaries, not approximations, the actual indexed content.
extends this to URLs: fetch, convert HTML to markdown, chunk, index. The raw page never enters context.
Validated across 11 real-world scenarios — test triage, TypeScript error diagnosis, git diff review, dependency audit, API response processing, CSV analytics. All under 1 KB output each.
Over a full session: 315 KB of raw output becomes 5.4 KB. Session time before slowdown goes from ~30 minutes to ~3 hours. Context remaining after 45 minutes: 99% instead of 60%.
Two ways. Plugin Marketplace gives you auto-routing hooks and slash commands:
context-mode@claude-context-mode
Or MCP-only if you just want the tools:
You don't change how you work. Context Mode includes a PreToolUse hook that automatically routes tool outputs through the sandbox. Subagents learn to use
as their primary tool. Bash subagents get upgraded to
The practical difference: your context window stops filling up. Sessions that used to hit the wall at 30 minutes now run
