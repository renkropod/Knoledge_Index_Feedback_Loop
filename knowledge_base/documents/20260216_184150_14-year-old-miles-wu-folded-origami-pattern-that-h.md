---
title: 14-year-old Miles Wu folded origami pattern that holds 10k times its own weight
source: hacker_news
url: https://www.smithsonianmag.com/innovation/this-14-year-old-is-using-origami-to-design-emergency-shelters-that-are-sturdy-cost-efficient-and-easy-to-deploy-180988179/
points: 928
---

Title: 14-year-old Miles Wu folded origami pattern that holds 10k times its own weight
Points: 928, Author: bookofjoe, Comments: 202

I'm a diving instructor. I'm also a platform engineer who spends lots of his time thinking about and implementing infrastructure security. Sometimes those two worlds collide in unexpected ways.
A Sula sula (Frigatebird) and a dive flag on the actual boat where I found the vulnerability - somewhere off Cocos Island.
While on a 14 day-long dive trip around Cocos Island in Costa Rica, I stumbled across a vulnerability in the portal of an (not publicly named) sports insurer - one that I'm personally insured through. What I found was so trivial, so fundamentally broken, that I genuinely couldn't believe it hadn't been exploited already.
I disclosed this vulnerability on
with a standard 30-day embargo period. That embargo expired on May 28, 2025 - over
. I waited this long to publish because I wanted to give the organization every reasonable opportunity to fully remediate the issue and notify affected users. The vulnerability has since been addressed, but to my knowledge, I have not received confirmation that affected users were notified. I have reached out to the organization to ask for clarification on this matter.
This is the story of what happened when I tried to do the right thing.
To understand why this is so bad, you need to know how the registration process works. As a diving instructor, I register my students (to get them insured) through my account on the portal. I enter their personal information with their consent - name, date of birth, address, phone number, email - and the system creates an account for them. The student then receives an email with their new account credentials: a numeric user ID and a default password. They
log in to complete additional information, or they might never touch the portal again.
When I registered three students in quick succession, they were sitting right next to me and checked their welcome emails. The user IDs were nearly identical - sequential numbers, one after the other. That's when it clicked that something really bad was going on.
Now here's the problem: the portal used
for login. User XXXXXX0, XXXXXX1, XXXXXX2, and so on. That alone is a red flag, but it gets worse: every account was provisioned with a
that was never enforced to be changed on first login. And many users - especially students who had their accounts created
them by their instructors - never changed it.
So the "authentication" to access a user's full profile - name, address, phone number, email, date of birth - was:
Type the same default password that every account shares on account creation.
There's a good chance you get in.
That's it. No rate limiting. No account lockout. No MFA. Just an incrementing integer and a password that might as well have been
I verified the issue with the minimum access necessary to confirm the scope - and stopped immediately after.
I did everything by the book. I contacted
(MaltaCIP) first - since the organization is registered in Malta, this is the competent national authority. The Maltese
National Coordina
