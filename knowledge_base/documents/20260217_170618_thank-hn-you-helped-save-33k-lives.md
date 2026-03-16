---
title: Thank HN: You helped save 33k lives
source: hacker_news
url: 
points: 1148
---

Title: Thank HN: You helped save 33k lives
Points: 1148, Author: chaseadam17, Comments: 112

For the past few weeks I’ve been teaching my 9-pound cavapoo Momo (cavalier king charles spaniel and toy poodle) to vibe code games. The key to making this work is telling Claude Code that a genius game designer who only speaks in cryptic riddles is giving it instructions, add strong guardrails, and build plenty of tools for automated feedback. The results have surpassed my expectations. Below I walk through all the pieces and how they came together.
If you’d rather skip ahead, all the
are at the bottom, including a full game she made and a video of her making it.
Back in December I was working on a small game prototype in Godot. I use Claude Code extensively these days and this project was no exception. I kicked off a procedural mesh generation task and came back to find strange input in the terminal.
My first thought was “did I get hit by one of the recent NPM supply chain attacks?” Fortunately, no (or at least the worm is still asleep in the background somewhere). A little bit of searching and I noticed my lip balm was gone off my desk - which I keep just behind my keyboard. I quickly found both the suspect and the lip balm (still intact) not far away.
At the time, I thought this was funny, took a screenshot, and moved on. Fast forward a few weeks, and I found myself with a lot of time on my hands. On January 13th, I woke up to the news that Meta had
and my role specifically as a research engineer had been eliminated.
Since the layoff, I’ve had plenty of time with friends and family. In recounting the anecdote of Momo typing away on my keyboard, I began to wonder “what would happen if she actually submitted that input to Claude? Could I make it do something meaningful?”. I decided to find out. Here’s what that looked like.
Momo types on a Bluetooth keyboard proxied through a Raspberry Pi 5. Keystrokes travel across the network to
, a small Rust app that filters out special keys and forwards the rest to Claude Code. When Momo has typed enough, DogKeyboard triggers a smart pet feeder to dispense treats. A chime tells her when Claude is ready for more input.
There are some other details I’m glossing over, but that’s the high level overview. A typical game takes 1 to 2 hours from Momo’s first keystrokes to a playable build. All the games are made in
4.6, with 100% of the game logic in C#.
It’s easy to submit random text to Claude Code, but it doesn’t do much.
● It looks like that might have been an accidental keyboard input. Let me know if there's something I can help you with!
Of course this can be worked around by telling Claude that there
meaning here. After a lot of iteration, I found this opening to work well:
(a very creative one) who communicates in an unusual way. Sometimes I’ll mash the keyboard or type nonsense like “skfjhsd#$%” – but
full of genius game ideas (even if it’s hard to see).
who can understand my cryptic language. No matter what odd or nonsensical input I provide, you will
interpret it as a meaningful instruction or idea for
