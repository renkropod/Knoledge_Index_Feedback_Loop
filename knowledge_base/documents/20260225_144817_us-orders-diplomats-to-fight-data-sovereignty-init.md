---
title: US orders diplomats to fight data sovereignty initiatives
source: hacker_news
url: https://www.reuters.com/sustainability/boards-policy-regulation/us-orders-diplomats-fight-data-sovereignty-initiatives-2026-02-25/
points: 546
---

Title: US orders diplomats to fight data sovereignty initiatives
Points: 546, Author: colinhb, Comments: 485

Building Bluehood, a Bluetooth scanner that reveals what information we leak just by having Bluetooth enabled on our devices.
If you’ve read much of this blog, you’ll know I have a
blocking ads network-wide with AdGuard
keeping secrets out of my dotfiles with Proton Pass
, I tend to think carefully about what data I’m exposing and to whom.
, a Bluetooth scanner that tracks nearby devices and analyses their presence patterns. The project was heavily assisted by AI, but the motivation was entirely human: I wanted to understand what information I was leaking just by having Bluetooth enabled.
The timing felt right. A few days ago, researchers at KU Leuven disclosed
(CVE-2025-36911), a critical vulnerability affecting hundreds of millions of Bluetooth audio devices. The flaw allows attackers to hijack headphones and earbuds remotely, eavesdrop on conversations, and track locations through Google’s Find Hub network. It’s a stark reminder that Bluetooth isn’t the invisible, harmless signal we treat it as.
We’ve normalised the idea that Bluetooth is always on. Phones, laptops, smartwatches, headphones, cars, and even medical devices constantly broadcast their presence. The standard response to privacy concerns is usually “nothing to hide, nothing to fear.”
But here’s the thing: even if you have nothing to hide, you’re still giving away information you probably don’t intend to.
From my home office, running Bluehood in passive mode (just listening, never connecting), I could detect:
When delivery vehicles arrived, and whether it was the same driver each time
The daily patterns of my neighbours based on their phones and wearables
Which devices consistently appeared together (someone’s phone and smartwatch, for instance)
The exact times certain people were home, at work, or elsewhere
None of this required any special equipment. A Raspberry Pi with a Bluetooth adapter would do the job. So would most laptops.
What concerns me most isn’t that people choose to have Bluetooth enabled. It’s that many devices don’t give users the option to disable it.
Hearing aids are a good example. Modern hearing aids often use Bluetooth Low Energy so audiologists can connect and adjust settings or run diagnostics. Pacemakers and other implanted medical devices sometimes broadcast BLE signals for the same reason. The user can’t simply turn this off.
Then there are vehicles. Delivery vans, police cars, ambulances, logistics fleets, and trains often have Bluetooth-enabled systems for fleet management, diagnostics, or driver assistance. These broadcast continuously, and the drivers have no control over it.
Even consumer devices aren’t always straightforward. Many smartwatches need Bluetooth to function at all. GPS collars for pets require it to communicate with the owner’s phone. Some fitness equipment won’t work without it.
Privacy Tools That Need You to Broadcast
What’s interesting is that some of the most privacy-focused projects actually require Bluetooth to be enabled.
is a pee
