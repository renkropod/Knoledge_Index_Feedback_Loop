---
title: I built Timeframe, our family e-paper dashboard
source: hacker_news
url: https://hawksley.org/2026/02/17/timeframe.html
points: 1616
---

Title: I built Timeframe, our family e-paper dashboard
Points: 1616, Author: saeedesmaili, Comments: 369

How I built Timeframe, our family e-paper dashboard
Over the past decade, I’ve worked to build the perfect family dashboard system for our home, called
. Combining calendar, weather, and smart home data, it’s become an important part of our daily lives.
https://news.ycombinator.com/item?id=47113728
for a lively discussion of this post.
When Caitlin and I got married a decade ago, we set an intention to have a healthy relationship with technology in our home. We kept our bedroom free of any screens, charging our devices elsewhere overnight. But we missed our calendar and weather apps.
So I set out to build a solution to our problem. First, I constructed a
using an off-the-shelf medicine cabinet and LCD display with its frame removed. It showed the calendar and weather data we needed:
But it was hard to read the text, especially during the day as we get significant natural light in Colorado. At night, it glowed like any backlit display, sticking out sorely in our living space.
I then spent about a year experimenting with various jailbroken Kindle devices, eventually landing on design with calendar and weather data on a pair of screens. The Kindles took a few seconds to refresh and flash the screen to reset the ink pixels, so they only updated every half hour. I designed wood enclosures and laser-cut them at the
Software-wise, I built a Ruby on Rails app for fetching the necessary data from Google Calendar and Dark Sky. The Kindles woke up on a schedule, loading a URL in the app that rendered a PNG using
. The prototype proved e-paper was the right solution: it was unobtrusive regardless of lighting:
The Kindles were a hack, requiring constant tinkering to keep them working. It was time for a more reliable solution. I tried an OLED screen to see if the lack of a global backlight would be less distracting, but it wasn’t much better than the Magic Mirror:
So it was back to e-paper. I found a system of displays from
, which came in 6”/10”/13”/32” sizes and could update every ten minutes for 2-3
The 32” screen used an outdated lower-contrast panel and its resolution was too low to render text smoothly. The smaller sizes used a contrasty, high-PPI panel. I ended up using a combination of them around the house: a 6” in the mudroom for the weather, a 13” (with its built-in magnetic backing) in the kitchen attached to the side of the fridge, and a 10” in the bedroom.
The Visionect displays required running custom closed-source software, either as a SaaS or locally with Docker. I opted for a local installation on the Raspberry Pi already running the Rails backend. I had my best results
images to the Visionect displays every five minutes in a recurring background job. It used IMGKit to generate a PNG and send it to the Visionect API, logic I extracted into
. This setup proved to be incredibly reliable, without a single failure for months at a time.
Visiting friends often asked how they could have a similar system in their home. Three years after the initial p
