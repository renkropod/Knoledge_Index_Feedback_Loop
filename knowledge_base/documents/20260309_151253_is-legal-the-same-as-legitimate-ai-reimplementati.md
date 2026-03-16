---
title: Is legal the same as legitimate: AI reimplementation and the erosion of copyleft
source: hacker_news
url: https://writings.hongminhee.org/2026/03/legal-vs-legitimate/
points: 569
---

Title: Is legal the same as legitimate: AI reimplementation and the erosion of copyleft
Points: 569, Author: dahlia, Comments: 593

The unreasonable power of nested decision rules.
Let's pretend we're farmers with a new plot of land. Given only the Diameter and Height of a tree trunk, we must determine if it's an Apple, Cherry, or Oak tree. To do this, we'll use a Decision Tree.
is an Oak tree! Thus, we can probably assume that any other trees we find in that region will also be one.
. We'll draw a vertical line at this Diameter and classify everything above it as Oak (our first
), and continue to partition our remaining data on the left.
We continue along, hoping to split our plot of land in the most favorable manner. We see that creating a new
leads to a nice section of Cherry trees, so we partition our data there.
Our Decision Tree updates accordingly, adding a new
After this second split we're left with an area containing many Apple and some Cherry trees. No problem: a vertical division can be drawn to separate the Apple trees a bit better.
Once again, our Decision Tree updates accordingly.
The remaining region just needs a further horizontal division and boom - our job is done! We've obtained an optimal set of nested decisions.
That said, some regions still enclose a few misclassified points. Should we continue splitting, partitioning into smaller sections?
If we do, the resulting regions would start becoming increasingly complex, and our tree would become unreasonably deep. Such a Decision Tree would learn too much from the noise of the training examples and not enough generalizable rules.
Does this ring familiar? It is the well known tradeoff that we have explored in our explainer on
! In this case, going too deep results in a tree that
We're done! We can simply pass any new data point's
values through the newly created Decision Tree to classify them as either an Apple, Cherry, or Oak tree!
