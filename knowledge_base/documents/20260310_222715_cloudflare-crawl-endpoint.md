---
title: Cloudflare crawl endpoint
source: hacker_news
url: https://developers.cloudflare.com/changelog/post/2026-03-10-br-crawl-endpoint/
points: 496
---

Title: Cloudflare crawl endpoint
Points: 496, Author: jeffpalmer, Comments: 183

Qwen3.5 is Alibaba’s new model family, including Qwen3.5-
series: Qwen3.5-0.8B, 2B, 4B and 9B. The multimodal hybrid reasoning LLMs deliver the strongest performances for their sizes. They support
thinking, and excel in agentic coding, vision, chat, and long-context tasks. The 35B and 27B models work on a 22GB Mac / RAM device. See all
. See some improvements in chat, coding, long context, and tool-calling use-cases.
following our chat template fixes.
for Unsloth performance results + our
We're retiring MXFP4 layers from 3 Qwen3.5 GGUFs: Q2_K_XL, Q3_K_XL and Q4_K_XL.
for SOTA quantization performance - so 4-bit has important layers upcasted to 8 or 16-bit. Thank you Qwen for providing Unsloth with day zero access. You can also
To enable or disable thinking see
How to enable or disable reasoning & thinking
.Qwen3.5 Small models disables by default. Also see
Table: Inference hardware requirements
(units = total memory: RAM + VRAM, or unified memory)
For best performance, make sure your total available memory (VRAM + system RAM) exceeds the size of the quantized model file you’re downloading. If it doesn’t, llama.cpp can still run via SSD/HDD offloading, but inference will be slower.
, use 27B if you want slightly more accurate results and can't fit in your device. Go for 35B-A3B if you want much faster inference.
(can be extended to 1M via YaRN)
default this is off, but to reduce repetitions, you can use this, however using a higher value may result in
If you're getting gibberish, your context length might be set too low. Or try using
--cache-type-k bf16 --cache-type-v bf16
As Qwen3.5 is hybrid reasoning, thinking and non-thinking mode have different settings:
Precise coding tasks (e.g. WebDev)
repeat penalty = disabled or 1.0
repeat penalty = disabled or 1.0
Thinking mode for general tasks:
Thinking mode for precise coding tasks:
Instruct (non-thinking) mode settings:
repeat penalty = disabled or 1.0
repeat penalty = disabled or 1.0
--chat-template-kwargs '{"enable_thinking":false}'
--chat-template-kwargs "{\"enable_thinking\":false}"
Use 'true' and 'false' interchangeably.
For Qwen3.5 0.8B, 2B, 4B and 9B, reasoning is disabled by default
--chat-template-kwargs '{"enable_thinking":true}'
Instruct (non-thinking) for general tasks:
Instruct (non-thinking) for reasoning tasks:
Because Qwen3.5 comes in many different sizes, we'll be using Dynamic 4-bit
GGUF variants for all inference workloads. Click below to navigate to designated model instructions:
default this is off, but to reduce repetitions, you can use this, however using a higher value may result in
slight decrease in performance.
Currently no Qwen3.5 GGUF works in Ollama due to separate mmproj vision files. Use llama.cpp compatible backends.
For this guide we will be utilizing Dynamic 4-bit which works great on a 24GB RAM / Mac device for fast inference. Because the model is only around 72GB at full F16 precision, we won't need to worry much about performance. GGUF:
For these tutorials, we w
