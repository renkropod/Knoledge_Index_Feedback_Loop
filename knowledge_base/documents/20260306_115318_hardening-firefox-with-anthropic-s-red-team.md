---
title: Hardening Firefox with Anthropic's Red Team
source: hacker_news
url: https://www.anthropic.com/news/mozilla-firefox-security
points: 628
---

Title: Hardening Firefox with Anthropic's Red Team
Points: 628, Author: todsacerdoti, Comments: 173

The English-language edition of Wikipedia is blacklisting Archive.today after the controversial archive site was used to direct a distributed denial of service (DDoS) attack against a blog.
In the course of discussing whether Archive.today should be deprecated because of the DDoS, Wikipedia editors discovered that the archive site altered snapshots of webpages to insert the name of the blogger who was targeted by the DDoS. The alterations were apparently fueled by a grudge against the blogger over a post that described how the Archive.today maintainer hid their identity behind several aliases.
“There is consensus to immediately deprecate
, and, as soon as practicable, add it to the spam blacklist (or create an edit filter that blocks adding new links), and remove all links to it,” stated an
today on Wikipedia’s Archive.today discussion. “There is a strong consensus that Wikipedia should not direct its readers towards a website that hijacks users’ computers to run a DDoS attack (see
). Additionally, evidence has been presented that archive.today’s operators have altered the content of archived pages, rendering it unreliable.”
More than 695,000 links to Archive.today are distributed across 400,000 or so Wikipedia pages. The archive site is commonly used to bypass news paywalls, and t
on the site operator’s identity with a subpoena to domain registrar Tucows.
“Those in favor of maintaining the status quo rested their arguments primarily on the utility of archive.today for
,” said today’s Wikipedia update. “However, an analysis of existing links has shown that most of its uses can be replaced. Several editors started to work out implementation details during this RfC [request for comment] and the community should figure out how to efficiently remove links to archive.today.”
published as a result of the decision asked editors to help remove and replace links to the following domain names used by the archive site: archive.today, archive.is, archive.ph, archive.fo, archive.li, archive.md, and archive.vn. The guidance says editors can remove Archive.today links when the original source is still online and has identical content; replace the archive link so it points to a different archive site, like the Internet Archive, Ghostarchive, or Megalodon; or “change the original source to something that doesn’t need an archive (e.g., a source that was printed on paper), or for which a link to an archive is only a matter of
The Wikipedia guidance points out that the Internet Archive and its website, Archive.org, are “uninvolved with and entirely separate from archive.today.” The
is a nonprofit based in the US.
, malicious code in Archive.today’s CAPTCHA page was used to direct a DDoS against the
written by a man named Jani Patokallio. The Archive.today maintainer demanded that Patokallio take down a
that discussed the archive site founder’s possible identity. Patokallio wasn’t able to determine who runs Archive.today but mentioned apparent aliases such as “Denis 
