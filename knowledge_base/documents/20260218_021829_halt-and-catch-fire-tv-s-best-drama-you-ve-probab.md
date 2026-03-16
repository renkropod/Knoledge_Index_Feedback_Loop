---
title: Halt and Catch Fire: TV’s best drama you’ve probably never heard of (2021)
source: hacker_news
url: https://www.sceneandheardnu.com/content/halt-and-catch-fire
points: 763
---

Title: Halt and Catch Fire: TV’s best drama you’ve probably never heard of (2021)
Points: 763, Author: walterbell, Comments: 395

When I decided to build my startup on European infrastructure, I thought it would be a straightforward swap. Ditch AWS, pick some EU providers, done. How hard could it be?
Turns out: harder than expected. Not impossible, I did it, but nobody talks about the weird friction points you hit along the way. This is that post.
Data sovereignty, GDPR simplicity, not having your entire business dependent on three American hyperscalers, and honestly, a bit of stubbornness. I wanted to prove it could be done. The EU has real infrastructure companies building serious products. They deserve the traffic.
Here's what I landed on after a lot of trial, error, and migration headaches.
handles the core compute. Load balancers, VMs, and S3-compatible object storage. The pricing is almost absurdly good compared to AWS, and the performance is solid. If you've never spun up a Hetzner box, you're overpaying for cloud compute.
fills the gaps Hetzner doesn't cover. I use their Transactional Email (TEM) service, Container Registry, a second S3 bucket for specific workloads, their observability stack, and even their domain registrar. One provider, multiple services, it simplifies billing if nothing else.
is the unsung hero of this stack. CDN with distributed storage, DNS, image optimization, WAF, and DDoS protection, all from a company headquartered in Slovenia. Their edge network is genuinely impressive and their dashboard is a joy to use. Coming from Cloudflare, I felt at home rather quickly.
powers our AI inference. If you need GPU compute in Europe without sending requests to
, they're one of the few real options.
handles authentication and identity. A German provider that gives you passkeys, social logins, and user management without reaching for Auth0 or Clerk. More on this in the "can't avoid" section — it doesn't eliminate American dependencies entirely, but it keeps the auth layer European.
Self-hosting: Rancher, my beloved
This is where things get fun... and time-consuming. I self-host a surprising amount:
All running on Kubernetes, with Rancher as the glue keeping the whole cluster sane.
Is self-hosting more work than SaaS? Obviously. But it means my data stays exactly where I put it, and I'm not at the mercy of a provider's pricing changes or acquisition drama.
keeps things encrypted and European.
watches the monitors so I can sleep.
Transactional email with competitive pricing.
This one surprised me. Sendgrid, Postmark, Mailgun, they all make it trivially easy and reasonably cheap.
The EU options exist, but finding one that matches on deliverability, pricing, and developer experience took real effort. Scaleway's TEM works, but the ecosystem is thinner. Fewer templates, fewer integrations, less community knowledge to lean on when something goes wrong.
If you live in GitHub's ecosystem Actions, Issues, code review workflows, the social graph... walking away feels like leaving a city you've lived in for a decade. You know where everything is. Gitea is actually exc
