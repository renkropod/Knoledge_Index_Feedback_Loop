---
title: AI adoption and Solow's productivity paradox
source: hacker_news
url: https://fortune.com/2026/02/17/ai-productivity-paradox-ceo-study-robert-solow-information-technology-age/
points: 792
---

Title: AI adoption and Solow's productivity paradox
Points: 792, Author: virgildotcodes, Comments: 752

Temporal: The 9-Year Journey to Fix Time in JavaScript
Welcome to our blog! I'm Jason Williams, a senior software engineer on Bloomberg's JavaScript Infrastructure and Terminal Experience team. Today the Bloomberg Terminal runs
to engineers across the company.
Bloomberg may not be the first company you think of when discussing JavaScript. It certainly wasn't for me in 2018 before I worked here. Back then, I attended my first
meeting in London, only to meet some Bloomberg engineers who were there discussing Realms, WebAssembly, Class Fields, and
. The company has now been involved with JavaScript standardization for numerous years, including partnering with Igalia. Some of the proposals we have assisted include
, Async Await, BigInt, Class Fields, Promise.allSettled, Promise.withResolvers, WeakRefs,
The first proposal I worked on was
, which was fulfilling. After that finished, I decided to help out on a proposal around dates and times, called Temporal.
JavaScript is unique in that it runs in all browsers. There is no single "owner," so you can't just make a change in isolation and expect it to apply everywhere. You need buy-in from all parties. Evolution happens through
, the Technical Committee responsible for ECMAScript.
Proposals move through a series of
Stage 1 - Problem space accepted
Stage 2 - Draft design chosen, but work to continue
Stage 2.7 - Proposal approved in principle; awaiting testing and feedback
Stage 3 - Implementation and feedback
In 2018, when I first looked at Temporal, it was at Stage 1. The TC39 Committee was convinced the problem was real. It was a radical proposal to bring a whole new library for Dates and Times into JavaScript. It was:
Providing different DateTime Types (instead of a single API)
Adding first-class time zone and calendar support
But how did we get here? Why was Date such a pain point? For that, we need to take a step back.
In 1995, Brendan Eich was tasked with a 10-day sprint to create Mocha (which would later become JavaScript). Under intense time pressure, many design decisions were pragmatic. One of them was to port Java's Date implementation directly. As Brendan later explained:
It was a straight port by Ken Smith (the only code in "Mocha" I didn't write) of Java's Date code from Java to C.
At the time, this made sense. Java was ascendant and JavaScript was being framed as its lightweight companion. Internally, the philosophy was even referred to as
that changing the API would have been politically difficult:
Changing it when everyone expected Java to be the "big brother" language would make confusion and bugs; Sun would have objected too.
In that moment, consistency with Java was more important than fundamentally rethinking the time model. It was a pragmatic trade-off. The Web was young, and most applications making use of JavaScript would be simple, at least, to begin with.
By the 2010s, JavaScript was powering banking systems, trading terminals, collaboration tools, and other complex systems runni
