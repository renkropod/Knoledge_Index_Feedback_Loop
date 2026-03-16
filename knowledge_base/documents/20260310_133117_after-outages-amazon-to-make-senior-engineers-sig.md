---
title: After outages, Amazon to make senior engineers sign off on AI-assisted changes
source: hacker_news
url: https://arstechnica.com/ai/2026/03/after-outages-amazon-to-make-senior-engineers-sign-off-on-ai-assisted-changes/
points: 657
---

Title: After outages, Amazon to make senior engineers sign off on AI-assisted changes
Points: 657, Author: ndr42, Comments: 484

Dependabot is a noise machine. It makes you feel like you’re doing work, but you’re actually discouraging more useful work. This is
true for security alerts in the Go ecosystem.
I recommend turning it off and replacing it with a pair of scheduled GitHub Actions, one running govulncheck, and the other running your test suite against the latest version of your dependencies.
method would produce invalid results if the receiver was not the identity point.
A lot of the Go ecosystem depends on filippo.io/edwards25519, mostly through
(228k dependents only on GitHub).
against unaffected repositories to update filippo.io/edwards25519. These PRs were accompanied by a security alert with
a nonsensical, made up CVSS v4 score
, allegedly based on the breakage the update is causing in the ecosystem. Note that the diff between v1.1.0 and v1.1.1 is
one line in the method no one uses
for the Wycheproof repository, which
does not import the affected filippo.io/edwards25519 package at all
. Instead, it only imports the unaffected filippo.io/edwards25519/field package.
$ go mod why -m filippo.io/edwards25519
github.com/c2sp/wycheproof/tools/twistcheck
Use a serious vulnerability scanner instead
But isn’t this toil unavoidable, to prevent attackers from exploiting old vulnerabilities in your dependencies? Absolutely not!
Computers are perfectly capable of doing the work of filtering out these irrelevant alerts for you. The
metadata for all Go vulnerabilities.
the entry for the filippo.io/edwards25519 vulnerability
- module: filippo.io/edwards25519
- package: filippo.io/edwards25519
summary: Invalid result or undefined behavior in filippo.io/edwards25519
Previously, if MultiScalarMult was invoked on an
initialized point who was not the identity point, MultiScalarMult
produced an incorrect result. If called on an
uninitialized point, MultiScalarMult exhibited undefined behavior.
- advisory: https://github.com/FiloSottile/edwards25519/security/advisories/GHSA-fw7p-63qq-7hpr
- fix: https://github.com/FiloSottile/edwards25519/commit/d1c650afb95fad0742b98d95f2eb2cf031393abb
created: 2026-02-17T14:45:04.271552-05:00
Any decent vulnerability scanner will
filter based on the package, which requires a simple
. This already silences a lot of noise, because it’s common and good practice for modules to separate functionality relevant to different dependents into different sub-packages.
For example, it would have avoided the false alert against the Wycheproof repository.
If you use a third-party vulnerability scanner, you should demand at least package-level filtering.
vulnerability scanners will go further, though, and filter based on the reachability of the vulnerable
using static analysis. That’s what
$ go mod why -m filippo.io/edwards25519
filippo.io/sunlight/internal/ctlog
github.com/google/certificate-transparency-go/trillian/ctfe
Your code is affected by 0 vulnerabilities.
This scan also found 1 vulnerability in packages you import and 2
vulnerabilities in modules you requi
