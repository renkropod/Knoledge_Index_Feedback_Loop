---
title: Meta acquires Moltbook
source: hacker_news
url: https://www.axios.com/2026/03/10/meta-facebook-moltbook-agent-social-network
points: 554
---

Title: Meta acquires Moltbook
Points: 554, Author: mmayberry, Comments: 381

We're thrilled to announce the stable release of Vite 8! When Vite first launched, we made a pragmatic bet on two bundlers: esbuild for speed during development, and Rollup for optimized production builds. That bet served us well for years. We're very grateful to the Rollup and esbuild maintainers. Vite wouldn't have succeeded without them. Today, it resolves into one: Vite 8 ships with
as its single, unified, Rust-based bundler, delivering up to 10-30x faster builds while maintaining full plugin compatibility. This is the most significant architectural change since Vite 2.
Vite is now being downloaded 65 million times a week, and the ecosystem continues to grow with every release. To help developers navigate the ever-expanding plugin landscape, we also launched
, a searchable directory of plugins for Vite, Rolldown, and Rollup that collects plugin data from npm daily.
or scaffold a Vite app locally with your preferred framework running
We invite you to help us improve Vite (joining the more than
), our dependencies, or plugins and projects in the ecosystem. Learn more at our
. A good way to get started is by
, sending tests PRs based on open issues, and supporting others in
. If you have questions, join our
Stay updated and connect with others building on top of Vite by following us on
Since its earliest versions, Vite relied on two separate bundlers to serve different needs.
handled fast compilation during development (dependency pre-bundling and TypeScript/JSX transforms) that made the dev experience feel instant.
handled production bundling, chunking, and optimization, with its rich plugin API powering the entire Vite plugin ecosystem.
This dual-bundler approach served Vite well for years. It allowed us to focus on developer experience and orchestration rather than reinventing parsing and bundling from scratch. But it came with trade-offs. Two separate transformation pipelines meant two separate plugin systems, and an increasing amount of glue code needed to keep the two pipelines in sync. Edge cases around inconsistent module handling accumulated over time, and every alignment fix in one pipeline risked introducing differences in the other.
is a Rust-based bundler built by the
team to address these challenges head-on. It was designed with three goals:
Written in Rust, Rolldown operates at native speed. In benchmarks, it is
matching esbuild's performance level.
Rolldown supports the same plugin API as Rollup and Vite. Most existing Vite plugins work out of the box with Vite 8.
A single unified bundler unlocks capabilities that were difficult or impossible with the dual-bundler setup, including full bundle mode, more flexible chunk splitting, module-level persistent caching, and Module Federation support.
The migration to Rolldown was deliberate and community-driven. First, a separate
package was released as a technical preview, allowing early adopters to test Rolldown's integration without affecting the stable version of Vite. The feedback fr
