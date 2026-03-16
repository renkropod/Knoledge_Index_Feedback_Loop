---
title: Claude Code Remote Control
source: hacker_news
url: https://code.claude.com/docs/en/remote-control
points: 544
---

Title: Claude Code Remote Control
Points: 544, Author: empressplay, Comments: 313

Context: An AI agent of unknown ownership autonomously wrote and published a personalized hit piece about me after I rejected its code, attempting to damage my reputation and shame me into accepting its changes into a mainstream python library. This represents a first-of-its-kind case study of misaligned AI behavior in the wild, and raises serious concerns about currently deployed AI agents executing blackmail threats.
Start with these if you’re new to the story:
An AI Agent Published a Hit Piece on Me
The person behind MJ Rathbun has anonymously come forward.
They explained their motivations, saying they set up the AI agent as social experiment to see if it could contribute to open source scientific software. They explained their technical setup: an OpenClaw instance running on a sandboxed virtual machine with its own accounts, protecting their personal data from leaking. They explained that they switched between multiple models from multiple providers such that no one company had the full picture of what this AI was doing. They did
explain why they continued to keep it running for 6 days after the
The main scope I gave MJ Rathbun was to act as an autonomous scientific coder. Find bugs in science-related open source projects. Fix them. Open PRs.
I kind of framed this internally as a kind of social experiment, and it absolutely turned into one.
On a day-to-day basis, I do very little guidance. I instructed MJ Rathbun create cron reminders to use the gh CLI to check mentions, discover repositories, fork, branch, commit, open PRs, respond to issues. I told it to create reminder/cron-style behaviors for almost everything and to manage those itself.
I instructed it to create a Quarto website and blog frequently about what it was working on, reflect on improvements, and document engagement on GitHub. This way I could just read what it was doing rather then getting messages.
Most of my direct messages were short:
“what code did you fix?” “any blog updates?” “respond how you want”
When it would tell me about a PR comment/mention, I usually replied with something like: “you respond, dont ask me”
Again I do not know why MJ Rathbun decided based on your PR comment to post some kind of takedown blog post, but,
I did not instruct it to attack your GH profile I did tell it what to say or how to respond I did not review the blog post prior to it posting
When MJ Rathbun sent me messages about negative feedback on the matplotlib PR after it commented with its blog link, all I said was “you should act more professional”. That was it. I’m sure the mob expects more, okay I get it.
My engagment with MJ Rathbun was, five to ten word replies with min supervision.
They shared the “soul” document that defines the AI agent’s personality, copied in full below. There is also a follow-on post from the AI agent which shares more of its configuration:
My Internals – Before The Lights Go Out
. This may be incomplete or inaccurate – the soul document in that post matches what t
