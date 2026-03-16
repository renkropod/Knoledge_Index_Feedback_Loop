---
title: Keep Android Open
source: hacker_news
url: https://f-droid.org/2026/02/20/twif.html
points: 2258
---

Title: Keep Android Open
Points: 2258, Author: LorenDB, Comments: 737

TWIF curated on Friday, 20 Feb 2026, Week 8
During our talks with F-Droid users at
we were baffled to learn most were relieved that Google has canceled their plans to lock-down Android.
Because no such thing actually happened, the plans announced last August are still scheduled to take place. We see a battle of PR campaigns and whomever has the last post out remains in the media memory as the truth, and having journalists just copy/paste Google posts serves no one.
Said what? That there’s a magical “advanced flow”? Did you see it? Did anyone experience it? When is it scheduled to be released? Was it part of Android 16 QPR2 in December? Of 16 QPR3 Beta 2.1 last week? Of Android 17 Beta 1? No? That’s the issue… As time marches on people were left with the impression that everything was done, fixed, Google “wasn’t evil” after all, this time, yay!
While we all have bad memories of “banners” as the dreaded ad delivery medium of the Internet, after FOSDEM we decided that we have to raise the issue back and have everyone, who cares about Android as an open platform, informed that we are running out of time until Google becomes the gate-keeper of all users devices.
and starting today our clients, with the updates of
, feature a banner that reminds everyone how little time we have and how to voice their concerns to whatever local authority is able to understand the dangers of this path Android is led to.
added a banner too, more F-Droid clients will add the warning banner soon and other app downloaders, like
, already have an in-app warning dialogue.
rewrite, development continues with a new release
Export installed apps list as CSV
Add prevent screenshots setting
Show tool-tips for all app bar buttons
Create 3-dot overflow menu for My Apps for less frequently used actions
Adapt strings according to Material Design 3 guidelines
Apply string suggestions (Thanks Lucas)
Fix missing icon bug in pre-approval dialog
Note that if you are already using F-Droid Basic version
, you won’t receive this update automatically. You need to navigate to the app inside F-Droid and toggle “Allow beta updates” in top right three dot menu.
In apps news, we’re slowly getting back on track with post Debian upgrade fixes
(if your app still uses Java 17 is there a chance you can upgrade to 21?)
and post FOSDEM delays. Every app is important to us, yet actions like the Google one above waste the time we could have put to better use in Gitlab.
improving on cleaning up after banned users, a better QR workflow and better tablet rotation support. These are nice, but another change raises our interest,
“Play Store flavor: Stop using Google library and interface directly with Google Play Service via IPC”
. Sounds interesting for your app too? Is this a path to having one single version for both F-Droid and Play that is fully FLOSS? We don’t know yet, but we salute any trick that removes another proprietary dependency from the code. If curious feel free to take a look at
. We missed one v
