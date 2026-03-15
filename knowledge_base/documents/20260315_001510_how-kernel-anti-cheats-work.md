---
title: How kernel anti-cheats work
source: hacker_news
url: https://s4dbrd.github.io/posts/how-kernel-anti-cheats-work/
---

Title: How kernel anti-cheats work
Score: 166 points by davikr
Comments: 129

Article content:
How Kernel Anti-Cheats Work: A Deep Dive into Modern Game Protection
How Kernel Anti-Cheats Work: A Deep Dive into Modern Game Protection
Modern kernel anti-cheat systems are, without exaggeration, among the most sophisticated pieces of software running on consumer Windows machines. They operate at the highest privilege level available to software, they intercept kernel callbacks that were designed for legitimate security products, they scan memory structures that most programmers never touch in their entire careers, and they do all of this transparently while a game is running. If you have ever wondered how BattlEye actually catches a cheat, or why Vanguard insists on loading before Windows boots, or what it means for a PCIe DMA device to bypass every single one of these protections, this post is for you.
This is not a comprehensive or authoritative reference. It is just me documenting what I found and trying to explain it clearly. Some of it comes from public research and papers I have linked at the bottom, some from reading kernel source and reversing drivers myself. If something is wrong, feel free to reach out. The post assumes some familiarity with Windows internals and low-level programming, but I have tried to explain each concept before using it.
Why Usermode Protections Are Not Enough
The fundamental problem with usermode-only anti-cheat is the trust model. A usermode process runs at ring 3, subject to the full authority of the kernel. Any protection implemented entirely in usermode can be bypassed by anything running at a higher privilege level, and in Windows that means ring 0 (kernel drivers) or below (hypervisors, firmware). A usermode anti-cheat that calls
to check game memory integrity can be defeated by a kernel driver that hooks
and returns falsified data. A usermode anti-cheat that enumerates loaded modules via
can be defeated by a driver that patches the PEB module list. The usermode process is completely blind to what happens above it.
Cheat developers understood this years before most anti-cheat engineers were willing to act on it. The kernel was, for a long time, the exclusive domain of cheats. Kernel-mode cheats could directly manipulate game memory without going through any API that a usermode anti-cheat could intercept. They could hide their presence from usermode enumeration APIs trivially. They could intercept and forge the results of any check a usermode anti-cheat might perform.
The response was inevitable: move the anti-cheat into the kernel.
The escalation has been relentless. Usermode cheats gave way to kernel cheats. Kernel anti-cheats appeared in response. Cheat developers began exploiting legitimate, signed drivers with vulnerabilities to achieve kernel execution without loading an unsigned driver (the BYOVD attack). Anti-cheats responded with blocklists and stricter driver enumeration. Cheat developers moved to hypervisors, running below the kernel and virtualizing the entire OS. Anti-cheats added hypervisor d
