---
title: Show HN: GitAgent – An open standard that turns any Git repo into an AI agent
source: hacker_news
url: https://www.gitagent.sh/
---

Title: Show HN: GitAgent – An open standard that turns any Git repo into an AI agent
Score: 87 points by sivasurend
Comments: 12

We built GitAgent because we kept seeing the same problem: every agent framework defines agents differently, and switching frameworks means rewriting everything.<p>GitAgent is a spec that defines an AI agent as files in a git repo.<p>Three core files — agent.yaml (config), SOUL.md (personality&#x2F;instructions), and SKILL.md (capabilities) — and you get a portable agent definition that exports to Claude Code, OpenAI Agents SDK, CrewAI, Google ADK, LangChain, and others.<p>What you get for free by being git-native:<p>1. Version control for agent behavior (roll back a bad prompt like you&#x27;d revert a bad commit)
2. Branching for environment promotion (dev → staging → main)
3. Human-in-the-loop via PRs (agent learns a skill → opens a branch → human reviews before merge)
4. Audit trail via git blame and git diff
5. Agent forking and remixing (fork a public agent, customize it, PR improvements back)
6. CI&#x2F;CD with GitAgent validate in GitHub Actions<p>The CLI lets you run any agent repo directly:<p>npx @open-gitagent&#x2F;gitagent run -r <a href="https:&#x2F;&#x2F;github.com&#x2F;user&#x2F;agent" rel="nofollow">https:&#x2F;&#x2F;github.com&#x2F;user&#x2F;agent</a> -a claude<p>The compliance layer is optional, but there if you need it — risk tiers, regulatory mappings (FINRA, SEC, SR 11-7), and audit reports via GitAgent audit.<p>Spec is at <a href="https:&#x2F;&#x2F;gitagent.sh" rel="nofollow">https:&#x2F;&#x2F;gitagent.sh</a>, code is on GitHub.<p>Would love feedback on the schema design and what adapters people would want next.
