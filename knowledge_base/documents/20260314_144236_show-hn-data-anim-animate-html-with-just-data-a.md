---
title: Show HN: Data-anim – Animate HTML with just data attributes
source: hacker_news
url: https://github.com/ryo-manba/data-anim
---

Title: Show HN: Data-anim – Animate HTML with just data attributes
Score: 12 points by ryo-manba
Comments: 4

Hey HN, I built data-anim — an animation library where you never have to write JavaScript yourself.<p>You just write:<p><pre><code>  &lt;div data-anim=&quot;fadeInUp&quot;&gt;Hello&lt;&#x2F;div&gt;
</code></pre>
That&#x27;s it. Scroll-triggered fade-in animation, zero JS to write.<p>What it does:<p>- 30+ built-in animations (fade, slide, zoom, bounce, rotate, etc.)<p>- 4 triggers: scroll (default), load, click, hover<p>- 3-layer anti-FOUC protection (immediate style injection → noscript fallback → 5s timeout)<p>- Responsive controls: disable per device or swap animations on mobile<p>- TypeScript autocomplete for all attributes<p>- Under 3KB gzipped, zero dependencies<p>Why I built this:<p>I noticed that most animation needs on landing pages and marketing sites are simple — fade in on scroll, slide in from left, bounce on hover. But the existing options are either too heavy (Framer Motion ~30KB) or require JS boilerplate.<p>I also think declarative HTML attributes are the most AI-friendly animation format. When LLMs generate UI, HTML attributes are the output they hallucinate least on — no selector matching, no JS API to misremember, no script execution order to get wrong.<p>Docs: <a href="https:&#x2F;&#x2F;ryo-manba.github.io&#x2F;data-anim&#x2F;" rel="nofollow">https:&#x2F;&#x2F;ryo-manba.github.io&#x2F;data-anim&#x2F;</a><p>Playground: <a href="https:&#x2F;&#x2F;ryo-manba.github.io&#x2F;data-anim&#x2F;playground&#x2F;" rel="nofollow">https:&#x2F;&#x2F;ryo-manba.github.io&#x2F;data-anim&#x2F;playground&#x2F;</a><p>npm: <a href="https:&#x2F;&#x2F;www.npmjs.com&#x2F;package&#x2F;data-anim" rel="nofollow">https:&#x2F;&#x2F;www.npmjs.com&#x2F;package&#x2F;data-anim</a><p>Happy to answer any questions about the implementation or design decisions.
