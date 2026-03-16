---
title: Elon Musk pushes out more xAI founders as AI coding effort falters
source: hacker_news
url: https://www.ft.com/content/e5fbc6c2-d5a6-4b97-a105-6a96ea849de5
points: 516
---

Title: Elon Musk pushes out more xAI founders as AI coding effort falters
Points: 516, Author: merksittich, Comments: 811

How We Hacked McKinsey's AI Platform
McKinsey & Company — the world's most prestigious consulting firm — built an internal AI platform called
for its 43,000+ employees. Lilli is a purpose-built system: chat, document analysis, RAG over decades of proprietary research, AI-powered search across 100,000+ internal documents. Launched in 2023, named after the first professional woman hired by the firm in 1945, adopted by over 70% of McKinsey, processing 500,000+ prompts a month.
So we decided to point our autonomous offensive agent at it. No credentials. No insider knowledge. And no human-in-the-loop. Just a domain name and a dream.
Within 2 hours, the agent had full read and write access to the entire production database.
Fun fact: As part of our research preview, the CodeWall research agent autonomously suggested McKinsey as a target citing their public
(to keep within guardrails) and
recent updates to their Lilli platform
. In the AI era, the threat landscape is shifting drastically — AI agents autonomously selecting and attacking targets will become the new normal.
The agent mapped the attack surface and found the API documentation publicly exposed — over 200 endpoints, fully documented. Most required authentication. Twenty-two didn't.
One of those unprotected endpoints wrote user search queries to the database. The values were safely parameterised, but the JSON
— the field names — were concatenated directly into SQL.
When it found JSON keys reflected verbatim in database error messages, it recognised a SQL injection that standard tools wouldn't flag
(and indeed OWASPs ZAP did not find the issue)
. From there, it ran fifteen blind iterations — each error message revealing a little more about the query shape — until live production data started flowing back. When the first real employee identifier appeared:
, the agent's chain of thought showed. When the full scale became clear — tens of millions of messages, tens of thousands of users:
From a workforce that uses this tool to discuss strategy, client engagements, financials, M&A activity, and internal research. Every conversation, stored in plaintext, accessible without authentication.
192,000 PDFs. 93,000 Excel spreadsheets. 93,000 PowerPoint decks. 58,000 Word documents. The filenames alone were sensitive and a direct download URL for anyone who knew where to look.
Every employee on the platform.
— the full organisational structure of how the firm uses AI internally.
The agent didn't stop at SQL. Across the wider attack surface, it found:
System prompts and AI model configurations
— 95 configs across 12 model types, revealing exactly how the AI was instructed to behave, what guardrails existed, and the full model stack (including fine-tuned models and deployment details)
3.68 million RAG document chunks
— the entire knowledge base feeding the AI, with S3 storage paths and internal file metadata. This is decades of proprietary McKinsey research, frameworks, and methodologies — the firm's intellect
