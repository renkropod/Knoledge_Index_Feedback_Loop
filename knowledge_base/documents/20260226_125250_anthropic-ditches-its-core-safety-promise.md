---
title: Anthropic ditches its core safety promise
source: hacker_news
url: https://www.cnn.com/2026/02/25/tech/anthropic-safety-policy-change
points: 552
---

Title: Anthropic ditches its core safety promise
Points: 552, Author: motbus3, Comments: 3

Continue local sessions from any device with Remote Control
Store instructions and memories
Enable Remote Control for all sessions
Remote Control vs Claude Code on the web
Remote Control is available on all plans. Team and Enterprise admins must first enable Claude Code in
to a Claude Code session running on your machine. Start a task at your desk, then pick it up from your phone on the couch or a browser on another computer.
When you start a Remote Control session on your machine, Claude keeps running locally the entire time, so nothing moves to the cloud. With Remote Control you can:
Use your full local environment remotely
, tools, and project configuration all stay available
Work from both surfaces at once
: the conversation stays in sync across all connected devices, so you can send messages from your terminal, browser, and phone interchangeably
: if your laptop sleeps or your network drops, the session reconnects automatically when your machine comes back online
, which runs on cloud infrastructure, Remote Control sessions run directly on your machine and interact with your local filesystem. The web and mobile interfaces are just a window into that local session.
Remote Control requires Claude Code v2.1.51 or later. Check your version with
This page covers setup, how to start and connect to sessions, and how Remote Control compares to Claude Code on the web.
Before using Remote Control, confirm that your environment meets these conditions:
: available on Pro, Max, Team, and Enterprise plans. Team and Enterprise admins must first enable Claude Code in
to sign in through claude.ai if you haven’t already.
in your project directory at least once to accept the workspace trust dialog.
You can start a dedicated Remote Control server, start an interactive session with Remote Control enabled, or connect a session that’s already running.
Navigate to your project directory and run:
The process stays running in your terminal in server mode, waiting for remote connections. It displays a session URL you can use to
, and you can press spacebar to show a QR code for quick access from your phone. While a remote session is active, the terminal shows connection status and tool activity.
Set a custom session title visible in the session list at claude.ai/code.
How concurrent sessions are created. Press
(default): all sessions share the current working directory, so they can conflict if editing the same files.
: each on-demand session gets its own
Maximum number of concurrent sessions. Default is 32.
Show detailed connection and session logs.
for filesystem and network isolation. Off by default.
To start a normal interactive Claude Code session with Remote Control enabled, use the
Optionally pass a name for the session:
This gives you a full interactive session in your terminal that you can also control from claude.ai or the Claude app. Unlike
(server mode), you can type messages locally while the session is also available remotely.
If you’re already in a Claud
