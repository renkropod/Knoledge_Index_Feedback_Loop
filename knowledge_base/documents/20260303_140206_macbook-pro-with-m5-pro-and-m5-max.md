---
title: MacBook Pro with M5 Pro and M5 Max
source: hacker_news
url: https://www.apple.com/newsroom/2026/03/apple-introduces-macbook-pro-with-all-new-m5-pro-and-m5-max/
points: 862
---

Title: MacBook Pro with M5 Pro and M5 Max
Points: 862, Author: scrlk, Comments: 979

Many believe AI is the real deal. In narrow domains, it already surpasses human performance. Used well, it is an unprecedented amplifier of human ingenuity and productivity. Its widespread adoption is hindered by two key barriers: high latency and astronomical cost. Interactions with language models lag far behind the pace of human cognition. Coding assistants can ponder for minutes, disrupting the programmer’s state of flow, and limiting effective human-AI collaboration. Meanwhile, automated agentic AI applications demand millisecond latencies, not leisurely human-paced responses.
On the cost front, deploying modern models demands massive engineering and capital: room-sized supercomputers consuming hundreds of kilowatts, with liquid cooling, advanced packaging, stacked memory, complex I/O, and miles of cables. This scales to city-sized data center campuses and satellite networks, driving extreme operational expenses.
Though society seems poised to build a dystopian future defined by data centers and adjacent power plants, history hints at a different direction. Past technological revolutions often started with grotesque prototypes, only to be eclipsed by breakthroughs yielding more practical outcomes.
Consider ENIAC, a room-filling beast of vacuum tubes and cables. ENIAC introduced humanity to the magic of computing, but was slow, costly, and unscalable. The transistor sparked swift evolution, through workstations and PCs, to smartphones and ubiquitous computing, sparing the world from ENIAC sprawl.
General-purpose computing entered the mainstream by becoming easy to build, fast, and cheap.
Founded 2.5 years ago, Taalas developed a platform for transforming any AI model into custom silicon. From the moment a previously unseen model is received, it can be realized in hardware in only two months.
The resulting Hardcore Models are an order of magnitude faster, cheaper, and lower power than software-based implementations.
Taalas’ work is guided by the following core principles:
Throughout the history of computation, deep specialization has been the surest path to extreme efficiency in critical workloads.
AI inference is the most critical computational workload that humanity has ever faced, and the one that stands to gain the most from specialization.
Its computational demands motivate total specialization: the production of optimal silicon for each individual model.
2. Merging storage and computation
Modern inference hardware is constrained by an artificial divide: memory on one side, compute on the other, operating at fundamentally different speeds.
This separation arises from a longstanding paradox. DRAM is far denser, and therefore cheaper, than the types of memory compatible with standard chip processes. However, accessing off-chip DRAM is thousands of times slower than on-chip memory. Conversely, compute chips cannot be built using DRAM processes.
This divide underpins much of the complexity in modern inference hardware, creating the need for a
