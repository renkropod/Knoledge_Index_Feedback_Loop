---
title: How far back in time can you understand English?
source: hacker_news
url: https://www.deadlanguagesociety.com/p/how-far-back-in-time-understand-english
points: 793
---

Title: How far back in time can you understand English?
Points: 793, Author: spzb, Comments: 415

I’ve been a .com purist for over two decades of building. Once, I broke that rule and bought a .online TLD for a small project. This is the story of how it went up in flames.
on HN, the site has been removed from Google's Safe Search blacklist. Thank you, unknown Google hero! I've emailed Radix to remove the darn
The site is finally back online. Not linking here as I don't want this to look like a marketing stunt. Link at the bottom if you're curious. [4]
Earlier this year, Namecheap was running a promo that let you choose one free .online or .site per account. I was working on a small product and thought, "hey, why not?" The app was a small browser, and the .online TLD just made sense in my head.
After a tiny $0.20 to cover ICANN fees, and hooking it up to Cloudflare and GitHub, I was up and running. Or so I thought.
Poking around traffic data for an unrelated domain many weeks after the purchase, I noticed there were zero visitors to the site in the last 48 hours. Loading it up led to the dreaded, all red, full page "This is an unsafe site" notice on both Firefox and Chrome. The site had a link to the App Store, some screenshots (no gore or violence or anything of that sort), and a few lines of text about the app, nothing else that could possibly cause this. [1]
Clicking through the disclaimers to load the actual site to check if it had been defaced, I was greeted with a "site not found" error. Uh oh.
After checking that Cloudflare was still activated and the CF Worker was pointing to the domain, I went to the registrar first. Namecheap is not the picture of reliability, so it seemed like a good place to start. The domain showed up fine on my account with the right expiration date. The nameservers were correct and pointed to CF.
Maybe I had gotten it wrong, so I checked the WHOIS information online. Status:
At this point, I double checked to make sure I hadn't received emails from the registry, registrar, host, or Google. Nada, nothing, zilch.
I emailed Namecheap to double check what was going on (even though it's a
[3]). They responded in a few minutes with:
Cursing under my breath, as it confirms my worst fears, I promptly submitted a request to the abuse team at
Radix, the registry in our case
Right, let's get ourselves off the damned Safe Browsing blacklist, eh? How hard could it be?
Very much so, I've now come to learn. You need to verify the domain in Google Search Console to then ask for a review and get the flag removed. But how do you get verified? Add a DNS TXT or a CNAME record. How will it work if the domain will not resolve? It won't.
As the situation stands, the registry won't reactivate the domain unless Google removes the flag, and Google won't remove the flag unless I verify that I own the domain, which I physically can't.
I've tried reporting the false positive
, just in case it moves the needle.
I've also submitted a review request to the Safe Search team (totally different from Safe Browsing) in the hopes that it might trigg
