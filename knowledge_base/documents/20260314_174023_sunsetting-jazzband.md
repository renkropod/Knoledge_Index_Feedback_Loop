---
title: Sunsetting Jazzband
source: hacker_news
url: https://jazzband.co/news/2026/03/14/sunsetting-jazzband
---

Title: Sunsetting Jazzband
Score: 140 points by mooreds
Comments: 52

Article content:
Jazzband is sunsetting. New signups are disabled. Project leads will
be contacted before PyCon US 2026 to coordinate transfers. The
as a cooperative experiment to reduce the stress of maintaining Open Source
software projects. The idea was simple – everyone who joins gets access to
push code, triage issues, merge pull requests.
It had a good run. More than 10 years, actually.
But it’s time to wind things down.
the flood of AI-generated spam PRs and issues – has made Jazzband’s model
of open membership and shared push access untenable.
Jazzband was designed for a world where the worst case was someone
accidentally merging the wrong PR. In a world where
only 1 in 10 AI-generated PRs meets project standards
because confirmation rates dropped below 5%, and where GitHub’s own
kill switch to disable pull requests entirely
an organization that gives push access to everyone who joins simply
But honestly, the cracks have been showing for much longer than that.
Jazzband was always a one-roadie operation. People
over the years, and I tried a number of times to make it work – but it
never stuck. I dropped the ball on organizing it properly, and when
volunteers did step up they’d quietly step back after a while. That’s
not a criticism of them, it’s just how volunteer work goes when there’s
The result was the same though: every project transfer, every lead
assignment, every PyPI permission change, every infrastructure
decision – it all went through me.
was raised as early as 2017. I gave a
keynote at DjangoCon Europe 2021
about it – five years in. In that talk I said out loud that the “social
coding” experiment had failed to create an equitable community, and that
a sustainable solution didn’t exist without serious financial support.
The roadmap I presented – revamp infrastructure, grow the management
team, formalize guidelines, reach out for funding – none of that
In the years since, I’ve been on the PSF board – which faced its own
crises – and now serve as PSF chair. That work matters and I don’t
regret prioritizing it, but it meant Jazzband got even less of my time.
Meanwhile, GitHub moved in the opposite direction. Copilot launched in
2022, trained on open source code that maintainers were burning out
60% of maintainers are still unpaid
in 2024 showed what happens when a lone maintainer burns out and someone
malicious fills the gap. And Jazzband’s own infrastructure started
the projects it was supposed to help – the release pipeline couldn’t
projects that needed admin access were stuck.
So projects started leaving. And that’s OK – that was always supposed
and Tim Schilling for picking up where Jazzband fell short. They have
5 admins, 15 active projects (including django-debug-toolbar,
django-simple-history, and django-cookie-consent from Jazzband), and
They solved the governance problem from day one. If you’re a Jazzband
project lead looking for a new home for your Django project, start there.
For non-Django projects like pip-tools, contextlib2, geojson, o
