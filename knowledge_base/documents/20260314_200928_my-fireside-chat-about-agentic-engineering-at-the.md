---
title: My fireside chat about agentic engineering at the Pragmatic Summit
source: hacker_news
url: https://simonwillison.net/2026/Mar/14/pragmatic-summit/
---

Title: My fireside chat about agentic engineering at the Pragmatic Summit
Score: 15 points by lumpa
Comments: 1

Article content:
My fireside chat about agentic engineering at the Pragmatic Summit
I was a speaker last month at the
in San Francisco, where I participated in a fireside chat session about
hosted by Eric Lui from Statsig.
. Here are my highlights from the conversation.
We started by talking about the different phases a software developer goes through in adopting AI coding tools.
I feel like there are different stages of AI adoption as a programmer. You start off with you’ve got ChatGPT and you ask it questions and occasionally it helps you out. And then the big step is when you move to the coding agents that are writing code for you—initially writing bits of code and then there’s that moment where the agent writes more code than you do, which is a big moment. And that for me happened only about maybe six months ago.
The new thing as of what, three weeks ago, is you don’t read the code. If anyone saw StrongDM—they had a big thing come out last week where they talked about their software factory and their two principles were nobody writes any code, nobody reads any code, which is clear insanity. That is wildly irresponsible. They’re a security company building security software, which is why it’s worth paying close attention—like how could this possibly be working?
I talked about StrongDM more in
How StrongDM’s AI team build serious software without even looking at the code
We discussed the challenge of knowing when to trust the AI’s output as opposed to reviewing every line with a fine tooth-comb.
The way I’ve become a little bit more comfortable with it is thinking about how when I worked at a big company, other teams would build services for us and we would read their documentation, use their service, and we wouldn’t go and look at their code. If it broke, we’d dive in and see what the bug was in the code. But you generally trust those teams of professionals to produce stuff that works. Trusting an AI in the same way feels very uncomfortable. I think Opus 4.5 was the first one that earned my trust—I’m very confident now that for classes of problems that I’ve seen it tackle before, it’s not going to do anything stupid. If I ask it to build a JSON API that hits this database and returns the data and paginates it, it’s just going to do it and I’m going to get the right thing back.
Test-driven development with agents
Every single coding session I start with an agent, I start by saying here’s how to run the test—it’s normally
is my current test framework. So I say run the test and then I say use red-green TDD and give it its instruction. So it’s “use red-green TDD”—it’s like five tokens, and that works. All of the good coding agents know what red-green TDD is and they will start churning through and the chances of you getting code that works go up so much if they’re writing the test first.
I wrote more about TDD for coding agents recently in
I have hated [test-first TDD] throughout my career. I’ve tried it in the past. It feels really tedious. It slows me down. I ju
