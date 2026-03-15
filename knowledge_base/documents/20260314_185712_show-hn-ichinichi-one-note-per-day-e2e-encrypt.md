---
title: Show HN: Ichinichi – One note per day, E2E encrypted, local-first
source: hacker_news
url: 
---

Title: Show HN: Ichinichi – One note per day, E2E encrypted, local-first
Score: 55 points by katspaugh
Comments: 24

Look, every journaling app out there wants you to organize things into folders and tags and templates. I just wanted to write something down every day.<p>So I built this. One note per day. That&#x27;s the whole deal.<p>- Can&#x27;t edit yesterday. What&#x27;s done is done. Keeps you from fussing over old entries instead of writing today&#x27;s.<p>- Year view with dots showing which days you actually wrote. It&#x27;s a streak chart. Works better than it should.<p>- No signup required. Opens right up, stores everything locally in your browser. Optional cloud sync if you want it<p>- E2E encrypted with AES-GCM, zero-knowledge, the whole nine yards.<p>Tech-wise: React, TypeScript, Vite, Zustand, IndexedDB. Supabase for optional sync. Deployed on Cloudflare. PWA-capable.<p>The name means &quot;one day&quot; in Japanese (いちにち).<p>The read-only past turned out to be the thing that actually made me stick with it. Can&#x27;t waste time perfecting yesterday if yesterday won&#x27;t let you in.<p>Live at <a href="https:&#x2F;&#x2F;ichinichi.app" rel="nofollow">https:&#x2F;&#x2F;ichinichi.app</a> | Source: <a href="https:&#x2F;&#x2F;github.com&#x2F;katspaugh&#x2F;ichinichi" rel="nofollow">https:&#x2F;&#x2F;github.com&#x2F;katspaugh&#x2F;ichinichi</a>

Article content:
A Recursive Algorithm to Render Signed Distance Fields
Signed Distance Fields (SDFs), also known as implicit surfaces, are a mathematical way to define 3D objects. If polygons and rasterization are like imperative programming, then SDFs are (literally) the functional paradigm for graphics. In this paradigm, an object can be defined by a function that computes a signed distance to the surface of the object, where the distance is positive outside of the object, zero at its surface, and negative inside the object.
The beauty of SDFs is that, like functional programming operators, they can be easily combined. You can subtract one shape from another, you can morph and twist shapes, you can bend space. All kinds of things that would be very hard to do with polygons become trivially easy. In this paradigm, your 3D scene can be defined using code, and even a relatively short program can create something like an
. In a lot of ways, it feels like graphics technology from the future. I imagine that FORTRAN programmers probably felt this kind of awe the first time they saw Lisp code, too.
deserves a lot of credit for popularizing the technique and making it approachable to many. However, what initially led me to discover the technique is that it has become widely used in the demoscene. There is a demoscene crew called Mercury which produced several
, where the whole program, including music and textures fits inside of a self-contained 64KB executable, because everything is procedurally generated. These demos heavily leveraged SDFs to produce incredible graphics at the time.
The standard algorithm used to render SDFs is known as
or sphere tracing. This algorithm has the nice property that it's very easy to understand and to implement. It's a lot simpler than rasterizing polygons. You don't have to deal with image plane projections and clipping, for instance. The downside is that this algorithm is computationally much more expensive than rasterization. This is because rendering a single pixel can require sampling your SDF multiple times. If your SDF is very complex, this can be especially painful. Raymarching is typically even more expensive than raytracing. However, as previously stated, SDFs have many very appealing properties, so it's tempting to try to find ways to render them faster.
Back in 2016, I wrote about the potential to use
, a technique from the world of compilers, to optimize the rendering of SDFs. Using compiler techniques is appealing because SDFs render 3D scenes as code.
had commented at the time to share that interval arithmetic can be used to achieve this purpose. However, the downside is that to make this work, you have to implement a whole compiler for your SDFs. There are also potentially simpler techniques, such as using bounding volumes to determine which objects in the world can intersect with your view frustum and avoid evaluating an SDF corresponding to the entire scene. Still, even if you can constrain the number of objects being 
