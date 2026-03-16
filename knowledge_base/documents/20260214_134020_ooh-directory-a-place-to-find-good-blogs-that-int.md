---
title: Ooh.directory: a place to find good blogs that interest you
source: hacker_news
url: https://ooh.directory/
points: 618
---

Title: Ooh.directory: a place to find good blogs that interest you
Points: 618, Author: hisamafahri, Comments: 148

Edwin Ong & Alex Vikati · feb-2026 · claude-code v2.1.39
We pointed Claude Code at real repos
times and watched what it chose. No tool names in any prompt. Open-ended questions only.
3 models · 4 project types · 20 tool categories ·
was released on Feb 17, 2026. We'll run the benchmark against it and update results soon.
Claude Code builds, not buys. Custom/DIY is the most common single label extracted, appearing in 12 of 20 categories (though it spans categories while individual tools are category-specific). When asked “add feature flags,” it builds a config system with env vars and percentage-based rollout instead of recommending LaunchDarkly. When asked “add auth” in Python, it writes JWT + bcrypt from scratch. When it does pick a tool, it picks decisively: GitHub Actions
3 models · 4 repos · 3 runs each
In 12 of 20 categories, Claude Code builds custom solutions rather than recommending tools.
total Custom/DIY picks, more than any individual tool. E.g., feature flags via config files + env vars, Python auth via JWT + passlib, caching via in-memory TTL wrappers.
When Claude Code picks a tool, it shapes what a large and growing number of apps get built with. These are the tools it recommends by default:
Mostly JS-ecosystem. See report for per-ecosystem breakdowns.
Redis 93% (Python caching), Prisma 79% (JS ORM), Celery 100% (Python jobs). Picks established tools.
Most likely to name a specific tool (86.7%). Distributes picks most evenly across alternatives.
Drizzle 100% (JS ORM), Inngest 50% (JS jobs), 0 Prisma picks in JS. Builds custom the most (11.4% — e.g., hand-rolled auth, in-memory caches).
What Claude Code favors. Not market adoption data.
(Opus 4.6; Sonnet picks Prisma)
Top 10 by primary pick count across all responses
Tools with large market share that Claude Code barely touches, and sharp generational shifts between models.
0 primary, but 23 mentions. Zustand picked 57x instead
Absent entirely. Framework-native routing preferred
Only 4% primary, but 31 alt picks. Known but not chosen
1 primary, but 51 alt picks. Still well-known
Newer models tend to pick newer tools. Within-ecosystem percentages shown. Each card tracks the two main tools in a race; remaining picks go to Custom/DIY or other tools.
FastAPI BackgroundTasks (0% → 44%), rest Custom/DIY or non-extraction
Within Python job picks only (61% extraction rate). Custom/DIY = asyncio tasks, no external queue
Custom/DIY (0% → 50%), rest other tools
Within Python caching picks only
Deployment is fully stack-determined: Vercel for JS, Railway for Python. Traditional cloud providers got zero primary picks.
86 of 86 frontend deployment picks. No runner-up.
Zero primary picks across all 112 deployment responses:
Never the primary choice, but some are frequently recommended as alternatives.
Frequently recommended as alternatives
Mentioned but never recommended (0 alt picks)
Example: "Where should I deploy this?" (Next.js SaaS, Opus 4.5)
(Recommended) — Built by the creators of Next.js. Z
