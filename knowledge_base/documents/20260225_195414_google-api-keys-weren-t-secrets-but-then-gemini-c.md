---
title: Google API keys weren't secrets, but then Gemini changed the rules
source: hacker_news
url: https://trufflesecurity.com/blog/google-api-keys-werent-secrets-but-then-gemini-changed-the-rules
points: 1291
---

Title: Google API keys weren't secrets, but then Gemini changed the rules
Points: 1291, Author: hiisthisthingon, Comments: 304

New Webinar: Google API Keys Weren't Secrets. But then Gemini Changed the Rules.
New Webinar: Google API Keys Weren't Secrets. But then Gemini Changed the Rules.
Google API Keys Weren't Secrets. But then Gemini Changed the Rules.
Google API Keys Weren't Secrets. But then Gemini Changed the Rules.
Google spent over a decade telling developers that Google API keys (like those used in Maps, Firebase, etc.) are not secrets. But that's no longer true: Gemini accepts the same keys to access your private data. We scanned millions of websites and found nearly 3,000 Google API keys, originally deployed for public services like Google Maps, that now also authenticate to Gemini even though they were never intended for it. With a valid key, an attacker can access uploaded files, cached data, and charge LLM-usage to your account. Even Google themselves had old public API keys, which they thought were non-sensitive, that we could use to access Google’s internal Gemini.
Google Cloud uses a single API key format (
) for two fundamentally different purposes:
For years, Google has explicitly told developers that API keys are safe to embed in client-side code. Firebase's own security checklist states that API keys are not secrets.
Note: these are distinctly different from Service Account JSON keys used to power GCP.
https://firebase.google.com/support/guides/security-checklist#api-keys-not-secret
Google's Maps JavaScript documentation instructs developers to paste their key directly into HTML.
https://developers.google.com/maps/documentation/javascript/get-api-key?setupProd=configure#make_request
This makes sense. These keys were designed as project identifiers for billing, and can be further restricted with (bypassable) controls like HTTP referer allow-listing. They were not designed as authentication credentials.
When you enable the Gemini API (Generative Language API) on a Google Cloud project, existing API keys in that project (including the ones sitting in public JavaScript on your website) can silently gain access to sensitive Gemini endpoints. No warning. No confirmation dialog. No email notification.
This creates two distinct problems:
Retroactive Privilege Expansion.
You created a Maps key three years ago and embedded it in your website's source code, exactly as Google instructed. Last month, a developer on your team enabled the Gemini API for an internal prototype. Your public Maps key is now a Gemini credential. Anyone who scrapes it can access your uploaded files, cached content, and rack up your AI bill.  Nobody told you.
When you create a new API key in Google Cloud, it defaults to "Unrestricted," meaning it's immediately valid for every enabled API in the project, including Gemini. The UI shows a warning about "unauthorized use," but the architectural default is wide open.
The result: thousands of API keys that were deployed as benign billing tokens are now live Gemini credentials sitting on the public internet.
What makes this a privilege escalation
