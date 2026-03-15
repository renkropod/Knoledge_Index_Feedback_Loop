---
title: Postgres with Builtin File Systems
source: hacker_news
url: https://db9.ai/
---

Title: Postgres with Builtin File Systems
Score: 64 points by ngaut
Comments: 20

Article content:
Create, manage, and query serverless PostgreSQL databases from your terminal. Branching, migrations, observability, type generation — all built in.
Full PostgreSQL and a cloud filesystem for AI agents. SQL when you need power. File ops when you need simplicity. One database, unified interfaces.
curl -fsSL https://db9.ai/install | sh
Your agent learns to install, auth, and use db9 autonomously
Personal assistants & customer copilots
Memory in tables. Context in files.
Structured state lives in Postgres. Raw context, transcripts, and session snapshots stay as files — all in one workspace.
topic = 'pricing' AND agent_id = 'a1'
Knowledge from files. Retrieval from SQL.
Source documents stay in the filesystem. Chunks, metadata, and vectors live in Postgres — agents retrieve grounded context from one backend.
Automation, reports & multi-agent runs
Outputs in files. History in Postgres.
Reports, traces, and artifacts persist as files. Run history, status, and metadata live in Postgres — one workspace per agent run.
Auto-embeddings, vector search, environment branching, file storage, cron — built in, not bolted on.
Auto-embeddings, vector search, and HTTP — all in SQL.
in a query and get vectors back — no external pipeline, no API keys in application code. Similarity search and outbound HTTP are native too.
-- similarity search with built-in embeddings
'https://api.example.com/health'
Clone your entire environment. Not just tables.
One command creates an isolated copy — data, files, cron jobs, and user permissions. Test against real conditions, then delete it.
db9 branch create myapp --name staging
Branch 'staging' created from database myapp.
Upload, download, and mount files alongside your data. No S3 buckets to configure.
db9 fs cp ./data.csv myapp:/imports/
Distributed job scheduling from SQL or CLI. No idle timeouts, no missed runs.
Zero setup, 600+ ORM tests passing. One command to generate TypeScript or Python types.
One command to install. One command to create a database. Zero config.
curl -fsSL https://db9.ai/install | sh
Serverless Postgres for AI agents. Create, query, branch, and manage databases from the terminal — zero config. Built-in JSONB, vector search, HTTP extension, filesystem queries, cron jobs, and full-text search.
Unlock deep insights and enterprise-grade observability. Stream OpenClaw events into db9 and secure runtime events as immutable JSONL audit logs.
https://db9.ai/plugins/my-claw-dash.md
and follow instructions to use my-claw-dash
