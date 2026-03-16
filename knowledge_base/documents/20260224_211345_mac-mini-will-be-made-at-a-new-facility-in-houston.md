---
title: Mac mini will be made at a new facility in Houston
source: hacker_news
url: https://www.apple.com/newsroom/2026/02/apple-accelerates-us-manufacturing-with-mac-mini-production/
points: 634
---

Title: Mac mini will be made at a new facility in Houston
Points: 634, Author: haunter, Comments: 682

Partnering with Mozilla to improve Firefox’s security
AI models can now independently identify high-severity vulnerabilities in complex software. As we recently documented, Claude found more than 500
(security flaws that are unknown to the software’s maintainers) in well-tested open-source software.
In this post, we share details of a collaboration with researchers at Mozilla in which Claude Opus 4.6 discovered 22 vulnerabilities over the course of two weeks. Of these, Mozilla assigned
14 as high-severity vulnerabilities
high-severity Firefox vulnerabilities that were remediated in 2025. In other words: AI is making it possible to detect severe security vulnerabilities at highly accelerated speeds.
Firefox security vulnerabilities reported from all sources, by month. Claude Opus 4.6 found 22 vulnerabilities in February 2026, more than were reported in any single month in 2025.
As part of this collaboration, Mozilla fielded a large number of reports from us, helped us understand what types of findings warranted submitting a bug report, and shipped fixes to hundreds of millions of users in
, and the technical lessons we learned, provides a model for how AI-enabled security researchers and maintainers can work together to meet this moment.
From model evaluations to a security partnership
In late 2025, we noticed that Opus 4.5 was close to solving all tasks in
, a benchmark that tests whether LLMs can reproduce known security vulnerabilities. We wanted to construct a harder and more realistic evaluation that contained a higher concentration of technically complex vulnerabilities, like those present in modern web browsers. So we built a dataset of prior Firefox common vulnerabilities and exposures (CVEs) to see if Claude could reproduce those.
We chose Firefox because it’s both a complex codebase and one of the most well-tested and secure open-source projects in the world. This makes it a harder test of AI’s ability to find novel security vulnerabilities than the open-source software we previously used to test our models. Hundreds of millions of users rely on it daily, and browser vulnerabilities are particularly dangerous because users routinely encounter untrusted content and depend on the browser to keep them safe.
Our first step was to use Claude to find previously identified CVEs in older versions of the Firefox codebase. We were surprised that Opus 4.6 could reproduce a high percentage of these historical CVEs, given that each of them took significant human effort to uncover. But it was still unclear how much we should trust this result because it was possible that at least some of those historical CVEs were already in Claude’s training data.
So we tasked Claude with finding novel vulnerabilities in the
version of Firefox—bugs that by definition can’t have been reported before. We focused first on Firefox’s JavaScript engine but then expanded to other areas of the browser. The JavaScript engine was a convenient first step: it’s an independent sl
