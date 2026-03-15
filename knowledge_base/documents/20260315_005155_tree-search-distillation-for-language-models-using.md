---
title: Tree Search Distillation for Language Models Using PPO
source: hacker_news
url: https://ayushtambde.com/blog/tree-search-distillation-for-language-models-using-ppo/
---

Title: Tree Search Distillation for Language Models Using PPO
Score: 10 points by at2005
Comments: 0

Article content:
Tree Search Distillation for Language Models using PPO
03-01-2026 · Updated 03-03-2026
Game-playing neural networks like AlphaZero achieve superhuman performance in board games by augmenting the raw policy with a test-time search harness and distilling the stronger, augmented policy back into the network. Why aren’t similar techniques used in language modelling today? The DeepSeek-R1 authors mention they found
on why they may have faced this problem, namely their choice of UCT instead of pUCT.
The purpose of this post is to explore two questions:
Is it possible that search distillation actually improves language model reasoning?
How does it perform relative to standard language RL methods, e.g. GRPO?
To explore this, I applied MCTS across reasoning steps to Qwen-2.5-1.5B-Instruct, to search for stronger trajectories and distill these back into the model via an online PPO loop. On the task of
, a combinatorial arithmetic game, the distilled model (evaluated without a search harness) achieves an asymptotic mean@16 eval score of 11.3%, compared to 8.4% for CISPO and 7.7% for best-of-N. Relative to the pre-RL instruct model (3.1%), this is an 8.2 percentage point improvement.
The low absolute scores reflect the fact that these are small-scale experiments on a 1.5B model. I want to use this post as the first in a series, and hope to see these scores increase in subsequent blog posts as I use larger models and compute budgets.
I initially tried using GSM8K as the environment to test this method, but found minimal differences between GRPO and MCTS to make a strong claim either way. Instead, I decided to go with the game of Countdown as our environment. The premise is simple: given a set of N positive integers, use standard operations (+, -, /, *) to compute a particular target. Why Countdown? The hypothesis is that combinatorial problems benefit more from the sort of parallel adaptive reasoning tree search enables, as opposed to, say, GSM8K where sequential reasoning also leads to effective outcomes. We train on a dataset of 20,000 samples, and evaluate on a test set of 820 samples. Each sample consists of four input integers, between 1 and 13.
I found that using a sparse reward (0/1 for correctness) during training results in unstable training. Switching to a dense reward function:
$1.0 - 2 \cdot \min\left(\frac{|t - p|}{t}, 1.0\right)$ if formatting is correct, else $-1.0$
Here, $t$ is the true target and $p$ is the predicted target.
However, evaluation still uses the sparse reward function, since we’d like to be able to intuit the scores (e.g. % pass rate).
The MCTS algorithm has been covered in-depth by others, so I’m going to skip a detailed description: for the purposes of this post I’d like to focus on the delta between classical MCTS and the method I tried. Briefly speaking, MCTS iteratively builds a search tree to intelligently explore the action space, guided by a value function.
Board games have a relatively meaningful action space, i.e. each
