---
title: US Court of Appeals: TOS may be updated by email, use can imply consent [pdf]
source: hacker_news
url: https://cdn.ca9.uscourts.gov/datastore/memoranda/2026/03/03/25-403.pdf
points: 547
---

Title: US Court of Appeals: TOS may be updated by email, use can imply consent [pdf]
Points: 547, Author: dryadin, Comments: 444

How we rebuilt Next.js with AI in one week
*This post was updated at 12:35 pm PT to fix a typo in the build time benchmarks.
Last week, one engineer and an AI model rebuilt the most popular front-end framework from scratch. The result,
(pronounced "vee-next"), is a drop-in replacement for Next.js, built on
, that deploys to Cloudflare Workers with a single command. In early benchmarks, it builds production apps up to 4x faster and produces client bundles up to 57% smaller. And we already have customers running it in production.
The whole thing cost about $1,100 in tokens.
is the most popular React framework. Millions of developers use it. It powers a huge chunk of the production web, and for good reason. The developer experience is top-notch.
But Next.js has a deployment problem when used in the broader serverless ecosystem. The tooling is entirely bespoke: Next.js has invested heavily in Turbopack but if you want to deploy it to Cloudflare, Netlify, or AWS Lambda, you have to take that build output and reshape it into something the target platform can actually run.
If you’re thinking: “Isn’t that what OpenNext does?”, you are correct.
was built to solve. And a lot of engineering effort has gone into OpenNext from multiple providers, including us at Cloudflare. It works, but quickly runs into limitations and becomes a game of whack-a-mole.
Building on top of Next.js output as a foundation has proven to be a difficult and fragile approach. Because OpenNext has to reverse-engineer Next.js's build output, this results in unpredictable changes between versions that take a lot of work to correct.
Next.js has been working on a first-class adapters API, and we've been collaborating with them on it. It's still an early effort but even with adapters, you're still building on the bespoke Turbopack toolchain. And adapters only cover build and deploy. During development, next dev runs exclusively in Node.js with no way to plug in a different runtime. If your application uses platform-specific APIs like Durable Objects, KV, or AI bindings, you can't test that code in dev without workarounds.
What if instead of adapting Next.js output, we reimplemented the Next.js API surface on
directly? Vite is the build tool used by most of the front-end ecosystem outside of Next.js, powering frameworks like Astro, SvelteKit, Nuxt, and Remix. A clean reimplementation, not merely a wrapper or adapter. We honestly didn't think it would work. But it’s 2026, and the cost of building software has completely changed.
We got a lot further than we expected.
in your scripts and everything else stays the same. Your existing
vinext dev          # Development server with HMR
vinext build        # Production build
vinext deploy       # Build and deploy to Cloudflare Workers
This is not a wrapper around Next.js and Turbopack output. It's an alternative implementation of the API surface: routing, server rendering, React Server Components, server actions, caching, middleware. All of it bui
