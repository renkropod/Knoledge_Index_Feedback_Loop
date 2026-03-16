---
title: Oat – Ultra-lightweight, zero dependency, semantic HTML, CSS, JS UI library
source: hacker_news
url: https://oat.ink/
points: 539
---

Title: Oat – Ultra-lightweight, zero dependency, semantic HTML, CSS, JS UI library
Points: 539, Author: twapi, Comments: 139

for the past 4 years that has had
to scale quickly. From the beginning I made some core decisions that the
company has had to stick to, for better or worse, these past four years. This post
will list some of the major decisions made and if I endorse them for your
startup, or if I regret them and advise you to pick something else.
Early on, we were using both GCP and AWS. During that time, I had
no idea who my “account manager” was for Google Cloud, while at the same
time I had regular cadence meetings with our AWS account manager. There is a feel
that Google lives on robots and automation, while Amazon lives with a customer focus.
This support has helped us when evaluating new AWS services. Besides support, AWS has done a great job around stability
and minimizing backwards incompatible API changes.
There was a time when Google Cloud was the choice for Kubernetes clusters, especially
when there was ambiguity around if AWS would invest in EKS over
all the extra Kubernetes integrations around AWS services (external-dns, external-secrets, etc),
this is not much of any issue anymore.
Unless you’re penny-pinching (and your time is free), there’s no reason to run your own
control plane rather than use EKS. The main advantage of using an alternative in AWS, like ECS,
is the deep integration into AWS services. Luckily, Kubernetes has caught up in many ways: for example,
using external-dns to integrate with Route53.
We started with EKS managed addons because I thought it was the “right” way to use EKS. Unfortunately, we always
ran into a situation where we needed to customize the installation itself. Maybe the CPU requests, the image tag,
or some configmap. We’ve since switched to using helm charts for what were add-ons and things are running much better
with promotions that fit similar to our existing GitOps pipelines.
Data is the most critical part of your infrastructure. You lose your network: that’s downtime. You
lose your data: that’s a company ending event. The markup cost of using RDS (or any managed database)
Redis has worked very well as a cache and general use product. It’s fast, the API is simple and
well documented, and the implementation is battle tested. Unlike other cache options, like
Memcached, Redis has a lot of features that make it useful for more than just caching. It’s a
great swiss army knife of “do fast data thing”.
Part of me is unsure what the state of Redis is for Cloud Providers, but I feel it’s so widely used by AWS customers
that AWS will continue to support it well.
. It was a hot mess of stability problems. Since moving to ECR,
things have been much more stable. The deeper permission integrations with EKS nodes or dev servers has also been a
There are Zero Trust VPN alternatives from companies like CloudFlare. I’m sure these products work
well, but a VPN is just so dead simple to setup and understand (“simplicity is preferable” is my mantra). We use
Okta to manage our VPN access and it’s been a great experience.
It’s super e
