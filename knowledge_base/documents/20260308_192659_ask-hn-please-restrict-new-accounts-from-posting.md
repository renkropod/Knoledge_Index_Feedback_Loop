---
title: Ask HN: Please restrict new accounts from posting
source: hacker_news
url: 
points: 717
---

Title: Ask HN: Please restrict new accounts from posting
Points: 717, Author: Oras, Comments: 512

In 2017, WikiLeaks published Vault7 - a large cache of CIA hacking tools and internal documents. Buried among the exploits and surveillance tools was something far more mundane:
a page of internal developer documentation with git tips and tricks
Most of it is fairly standard stuff, amending commits, stashing changes, using bisect. But one tip has lived in my
Over time, a local git repo accumulates stale branches. Every feature branch, hotfix, and experiment you’ve ever merged sits there doing nothing.
starts to look like a graveyard.
You can list merged branches with:
But deleting them one by one is tedious. The CIA’s dev team has a cleaner solution:
git branch --merged | grep -v "\*\|master" | xargs -n 1 git branch -d
— lists all local branches that have already been merged into the current branch
— filters out the current branch (
— deletes each remaining branch one at a time, safely (lowercase
, you can update the command and exclude any other branches you frequently use:
git branch --merged origin/main | grep -vE "^\s*(\*|main|develop)" | xargs -n 1 git branch -d
after a deployment and your branch list goes from 40 entries back down to a handful.
I keep this as a git alias so I don’t have to remember the syntax:
alias ciaclean='git branch --merged origin/main | grep -vE "^\s*(\*|main|develop)" | xargs -n 1 git branch -d'
Small thing, but one of those commands that quietly saves a few minutes every week and keeps me organised.
