---
title: Fedora 44 on the Raspberry Pi 5
source: hacker_news
url: https://nullr0ute.com/2026/03/fedora-44-on-the-raspberry-pi-5/
---

Title: Fedora 44 on the Raspberry Pi 5
Score: 97 points by jandeboevrie
Comments: 27

Article content:
? I was planning on getting images done for
but I was unwell and busy and ran out of time. So what better time to get them out than
So compared to the last image what do we have now? Quite a lot more and I have more in the pipeline which should be in place in before freeze, plus a possible secret 😉, I just wanted to get something out sooner rather than later for people to play with. So the things that are working and tested are now:
All Raspberry Pi 5B: both revC and revD SoC 1/2/4/8/16GB variants
The micro SD slot – the only supported OS disk ATM
HDMI including accelerated graphics
Desktops including images for KDE and GNOME
Overall the devices are quire usable, but I will be working to improve it even more in the coming days.
The things that don’t work, but I’m hoping will be working RSN (pre 44) in no particular order:
One thing you do need to currently do manually once you’ve created an image is to add the following to the kernel command line (use the –args option to arm-image-installer):
and without that accelerated graphics and some other things just won’t work, once you’re booted add it to
so new kernels will get it too. I’ll hopefully have that issue fixed shortly, I know the problem, just still haven’t got the best solution!
You’ll also want to disable auto-suspend on the Desktop images.
So where can I get these images? Right here:
Fedora 44 GNOME Workstation Image
