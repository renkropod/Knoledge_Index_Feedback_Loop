---
title: The L in "LLM" Stands for Lying
source: hacker_news
url: https://acko.net/blog/the-l-in-llm-stands-for-lying/
points: 666
---

Title: The L in "LLM" Stands for Lying
Points: 666, Author: LorenDB, Comments: 477

Your house is quietly plotting to break while you sleep—and
you’re dreaming about redoing the kitchen.
tracks maintenance, projects, incidents, appliances, vendors, quotes, and documents—all from your terminal.
When did I last change the furnace filter?
Maintenance schedules, auto-computed due dates, full service history.
What if we finally did the backyard?
Projects from napkin sketch to completion—or graceful abandonment.
How much would it actually cost to…
Quotes side by side, vendor history, and the math you need to actually decide — in your local currency.
Is the dishwasher still under warranty?
Appliance tracking with purchase dates, warranty status, and maintenance history tied to each one.
Log incidents with severity and location, link them to appliances and vendors, and resolve them when fixed.
A vendor directory with contact info, quote history, and every job they've done for you.
Attach files—manuals, invoices, photos—directly to projects and appliances. Stored in the same SQLite file. Full-text search finds any document by title, notes, or extracted text. PDFs and scanned documents are automatically OCR’d so their text is searchable, and when an LLM is configured, that text can also be analyzed for richer summaries and structure.
How much have I spent on plumbing?
Chat with a local LLM about your data. It writes the SQL, runs the query, and summarizes the results—all on your machine.
go install github.com/cpcloud/micasa/cmd/micasa@latest
Linux, macOS, and Windows binaries are available for amd64 and arm64.
micasa --demo         # poke around with sample data
micasa                # start fresh with your own house
micasa --print-path   # show where the database lives
Linux, macOS, Windows. One SQLite file, your machine. Back it up with
I built this because my home maintenance system was a shoebox of receipts and the vague feeling I was supposed to call someone about the roof.
replaces the shoebox, the binder you never open, and the sticky note on the fridge with one SQLite file and a terminal you already have open. Its modal, keyboard-driven interface is inspired by
