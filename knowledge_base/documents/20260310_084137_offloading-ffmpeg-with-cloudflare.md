---
title: Offloading FFmpeg with Cloudflare
source: hacker_news
url: https://kentcdodds.com/blog/offloading-ffmpeg-with-cloudflare
---

Title: Offloading FFmpeg with Cloudflare
Score: 40 points by heftykoo
Comments: 18

Article content:
it with my response audio, and ran the whole thing through FFmpeg directly on
the same Fly.io machine that serves kentcdodds.com. It was a simple pipeline
and it worked fine. But in the back of my mind I knew I should probably give
this some proper treatment (queues etc).
The publish that finally broke things
Call Kent episode and hit publish. My app runs FFmpeg during the publish flow:
it stitches the caller's audio with my response, applies silence trimming,
normalizes loudness, adds intro and outro bumpers, and produces the final
episode MP3. That job used to block the HTTP request and run inline on the app
It wasn't a big deal because I'm the only person who kicks that off so I don't
But this one was kinda big relative to others I've done and that publish made
The Fly.io instance running kentcdodds.com hit extreme CPU saturation. The
metrics tell the story clearly:
and stayed there for the entire FFmpeg
run. The CPU quota balance graph showed the machine being throttled, having
consumed its allocated CPU budget so the scheduler was pulling it back. The
site was degraded until the job finished, and I had to emergency-upgrade the
machine from a shared CPU to a performance CPU to stabilize it.
That was the moment I decided to stop doing FFmpeg on the primary machine.
In defense of the original design
I want to be clear: running FFmpeg inline was not a foolish decision. It was a
reasonable simple-first choice that served 226 episodes with minimal incident.
Only I can trigger that code path. It runs exactly once per episode. When I
started building the Call Kent feature, I could have designed a proper job
queue with a dedicated worker pool. But that would have been solving a
scalability problem I did not yet have. "Start simple and iterate when reality
tells you to" is still how I think about this. Reality finally told me.
The old design also had a characteristic that made it deceptively safe for a
long time: it ran on the same machine that handled everything else, which meant
the machine was already sized for general web traffic. FFmpeg just piggybaacked
on that capacity. The problem only surfaced when the audio was long enough and
the shared CPU quota tight enough to cause a collision.
Another nice benefit of me waiting is that now we have Cloudflare Queues and
Containers to use (had I solved this earlier, I would have had to build my own
queues and containers or found another solution that I don't like as much).
Why the primary machine was the worst place for this
kentcdodds.com runs on Fly.io with a primary instance and read replicas. The
primary machine handles all write operations. The replicas handle reads. That
When FFmpeg ran on the primary machine, it competed with the one machine that
could not afford to be slow. If the primary stalls or throttles, writes stall.
Users trying to submit forms, save data, or do anything stateful hit that
bottleneck. The replicas were fine. The one machine that needed to be
responsive was the one eating all
