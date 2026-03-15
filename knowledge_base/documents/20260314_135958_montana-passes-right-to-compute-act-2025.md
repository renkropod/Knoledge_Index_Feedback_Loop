---
title: Montana passes Right to Compute act (2025)
source: hacker_news
url: https://www.westernmt.news/2025/04/21/montana-leads-the-nation-with-groundbreaking-right-to-compute-act/
---

Title: Montana passes Right to Compute act (2025)
Score: 233 points by bilsbie
Comments: 201

Article content:
Dabao Evaluation Board for Baochip-1x
A powerful new RISC-V microcontroller with mostly open RTL
What It Is, Why I'm Doing It Now, and How It Came About
Thanks to all the backers who have contributed to the campaign so far, plus a special shout-out to those who have generously donated to support my work! As a subscriber to the “Dabao” campaign, you’re already aware of the Baochip-1x. This update fills in the backstory of what it is, why I’m doing it now, and how it came about.
Hardware Built to Run High-Assurance Software
In my mind, the Baochip-1x’s key differentiating feature is the inclusion of a Memory Management Unit (MMU). No other microcontroller in this performance/integration class has this feature, to the best of my knowledge. For those not versed in OS-nerd speak, the MMU is what sets the software that runs on your phone or desktop apart from the software that runs in your toaster oven. It facilitates secure, loadable apps by sticking every application in its own virtual memory space.
The MMU is a venerable piece of technology, dating back to the 1960’s. Its page-based memory protection scheme is well-understood and has passed the test of time; I’ve taught its principles to hundreds of undergraduates, and it continues to be a cornerstone of modern OSes.
Diagram illustrating an early virtual memory scheme from Kilburn, et al, 'One-level storage system', IRE Transactions, EC-11(2):223-235, 1962
When it comes to evaluating security-oriented features, older is not always worse; in fact, withstanding the test of time is a positive signal. For example, the AES cipher is about 26 years old. This seems ancient for computer technology, yet many cryptographers recommend it over newer ciphers explicitly because AES has withstood the test of hundreds of cryptographers trying to break it, with representation from every nation state, over years and years.
I’m aware of newer memory protection technologies, such as
, PMPs, MPUs… and as a nerd, I love thinking about these sorts of things. In fact,
, I even advocated for the use of CHERI-style hardware capabilities and tagged pointers in new CPU architectures.
However, as a pragmatic system architect, I see no reason to eschew the MMU in favor of any of these. In fact, the MMU is composable with all of these primitives – it’s valid to have both a PMP and an MMU in the same RISC-V CPU. And, even if you’re using a CHERI-like technology for hardware-enforced bounds checking on pointers, it still doesn’t allow for transparent address space relocation. Without page-based virtual memory, each program would need to be linked to a distinct, non-overlapping region of physical address space at compile time, and you couldn’t have swap memory.
This begs the question: if the MMU is such an obvious addition, why isn’t it more prevalent? If it’s such an obvious choice, wouldn’t more players include it in their chips?
“Small” CPUs such as those found in embedded SoCs have lacked this feature since their inception. I tr
