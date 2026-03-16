---
title: Cognitive Debt: When Velocity Exceeds Comprehension
source: hacker_news
url: https://www.rockoder.com/beyondthecode/cognitive-debt-when-velocity-exceeds-comprehension/
points: 507
---

Title: Cognitive Debt: When Velocity Exceeds Comprehension
Points: 507, Author: pagade, Comments: 223

New updates and improvements at Cloudflare.
Crawl entire websites with a single API call using Browser Rendering
Edit: this post has been edited to clarify crawling behavior with respect to site guidance.
You can now crawl an entire website with a single API call using
, available in open beta. Submit a starting URL, and pages are automatically discovered, rendered in a headless browser, and returned in multiple formats, including HTML, Markdown, and structured JSON. The endpoint is a
by default, making it easy for developers to comply with website rules, and making it less likely for crawlers to ignore web-owner guidance. This is great for training models, building RAG pipelines, and researching or monitoring content across a site.
Crawl jobs run asynchronously. You submit a URL, receive a job ID, and check back for results as pages are processed.
'https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl'
'Authorization: Bearer <apiToken>'
'Content-Type: application/json'
"url": "https://blog.cloudflare.com/"
'https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl/{job_id}'
'Authorization: Bearer <apiToken>'
- Return crawled content as HTML, Markdown, and structured JSON (powered by
- Configure crawl depth, page limits, and wildcard patterns to include or exclude specific URL paths
- Discovers URLs from sitemaps, page links, or both
to skip pages that haven't changed or were recently fetched, saving time and cost on repeated crawls
to fetch static HTML without spinning up a browser, for faster crawling of static sites
Available on both the Workers Free and Paid plans.
: the /crawl endpoint cannot bypass Cloudflare bot detection or captchas, and self-identifies as a bot.
If you are setting up your own site to be crawled, review the
robots.txt and sitemaps best practices
