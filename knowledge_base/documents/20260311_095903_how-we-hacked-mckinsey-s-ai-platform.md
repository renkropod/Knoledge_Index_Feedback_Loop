---
title: How we hacked McKinsey's AI platform
source: hacker_news
url: https://codewall.ai/blog/how-we-hacked-mckinseys-ai-platform
points: 505
---

Title: How we hacked McKinsey's AI platform
Points: 505, Author: mycroft_4221, Comments: 195

Terminals should generate the 256-color palette from the user's
If you've spent much time in the terminal, you've probably set a
custom base16 theme. They work well. You define a handful of colors
in one place and all your programs use them.
The drawback is that 16 colors is limiting. Complex and color-heavy
programs struggle with such a small palette.
The mainstream solution is to use truecolor and gain access to 16
million colors. But there are drawbacks:
Each truecolor program needs its own theme configuration.
Changing your color scheme means editing multiple config files.
Light/dark switching requires explicit support from program maintainers.
Truecolor escape codes are longer and slower to parse.
Fewer terminals support truecolor.
The 256-color palette sits in the middle with more range than base16
and less overhead than truecolor. But it has its own issues:
The default theme clashes with most base16 themes.
The default theme has poor readability and inconsistent contrast.
Nobody wants to manually define 240 additional colors.
The solution is to generate the extended palette from your existing
base16 colors. You keep the simplicity of theming in one place while
gaining access to many more colors.
If terminals did this automatically, then terminal program maintainers
would consider the 256-color palette a viable choice, allowing them
to use a more expressive color range without requiring added
complexity or configuration files.
Understanding the 256-Color Palette
The 256-color palette has a specific layout.  If you are already
familiar with it, you can skip to the next section.
The first 16 colors form the base16 palette. It contains black,
white, and all primary and secondary colors, each with normal and
The next 216 colors form a 6x6x6 color cube. It works like 24-bit
RGB but with 6 shades per channel instead of 256.
You can calculate a specific index using this formula, where R, G,
The final 24 colors form a grayscale ramp between black and white.
Pure black and white themselves are excluded since they can be found
in the color cube at (0, 0, 0) and (5, 5, 5).
You can calculate specific index using this formula, where S is the
Problems with the 256-Color Palette
The most obvious problem with the 256-color palette is the inconsistency
Using a custom 256-color palette gives a more pleasing result:
The default 216-color cube interpolates between black and each color
incorrectly. It is shifted towards lighter shades (37% intensity
for the first non-black shade as opposed to the expected 20%), causing
readability issues when attempting to use dark shades as background:
If the color cube is instead interpolated correctly, readability
The default 256-color palette uses fully saturated colors, leading
to inconsistent brightness against the black background. Notice
that blue always appears darker than green, despite having the same
If a less saturated blue is used instead then the consistent
These problems can be solved by generating the 256-color
