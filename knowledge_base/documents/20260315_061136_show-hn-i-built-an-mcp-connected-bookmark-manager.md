---
title: Show HN: I built an MCP-connected bookmark manager because X's are useless
source: hacker_news
url: https://www.bookmarksos.com/
---

Title: Show HN: I built an MCP-connected bookmark manager because X's are useless
Score: 3 points by enzovarela
Comments: 0

I made BookmarkSOS because I had a dumb problem. I bookmark around 20-30 tweets a day on X, being threads, tools, launch posts, and design references. The problem? I would never go back, and if I did, I would never find what I needed again. X gives you a reverse-chronological list with no search, no folders, no tags. Basically a write-only database. Very disorganized and useless.<p>So I built a web app + extension that adds a save button to every tweet. One click captures everything that you need, text, images, videos, author, timestamps. All into a dashboard with folders, color-coded tags, and full-text search.<p>And the best part: it ships with an MCP server. You install it with command line, connect it to Claude Code, and now your AI can search and reference every tweet you&#x27;ve ever saved. &quot;Find that thread about programmatic SEO I bookmarked last week&quot; just works. Your bookmarks become part of your dev workflow instead of sitting in a graveyard.<p>Stack used: Next.js, Convex for the reactive backend, Better Auth with Google OAuth, and a Manifest V3 Chrome extension.<p>Would love to hear what you think.
