---
title: SBCL Fibers – Lightweight Cooperative Threads
source: hacker_news
url: https://atgreen.github.io/repl-yell/posts/sbcl-fibers/
---

Title: SBCL Fibers – Lightweight Cooperative Threads
Score: 25 points by anonzzzies
Comments: 2

Article content:
This is a work-in-progress draft document
userland cooperative threads for SBCL. The implementation is under
active development and details may change. This is a living
Fiber Parking (Condition-Based Suspend/Resume)
Fiber-Aware Blocking Primitives
Fiber Pinning (Preventing Yield)
Register Save/Restore Convention
Stack Frame Initialization for New Fibers
The Entry Trampoline (Assembly to C to Lisp)
Zero-Allocation Design (No SAPs, No GC Pressure)
Thread Register Patching on Carrier Migration
Control Stack Layout and Guard Pages
Binding Stack (Separate Allocation)
Stack Overflow Detection in Signal Handlers
Stack Size Tradeoffs (No Dynamic Growth)
Dynamic Variable Bindings (TLS)
TLS Overlay Arrays (Save/Restore Without Unbinding)
Carrier Value Update on Migration
Catch Block and Unwind-Protect Chain Save/Restore
Same-Carrier Resume Optimization
The Two-List Design: Suspended Fibers vs. Active Contexts
: Conservative Control Stack Scanning
: Carrier + Fiber Stack Visibility
Precise Binding Stack Scavenging
Persistent Carrier Context (Lock-Free Hot Path)
Thread Struct Slot (O(1) Lookup)
Correctness Argument: Why Partial Updates Are Safe
Fast Path: Skip Maintenance When Deque Is Hot
Maintenance: Pending Queue Drain, Deadline Expiry, Wake Checks
Post-Switch Dispatch (Suspended, Dead)
Idle Detection and Carrier Parking
Maintenance Frequency Backstop (Every 64 Fibers)
Owner Operations (Push/Pop from Bottom, LIFO)
Thief Operations (Steal from Top, FIFO, CAS)
Buffer Growth (Power-of-Two Circular Array)
Fiber Migration and Thread Register Fixup
Platform Abstraction (epoll, kqueue, poll Fallback)
Edge-Triggered Mode with One-Shot (
Indexed I/O Waiters (fd-to-Fiber Table)
Batched FD Polling vs. Per-Fiber Polling
Binary Min-Heap with Inline Index
Batch Expiry (Pop All Expired in One Pass)
Interaction with I/O Waiters (Dual-Indexed Fibers)
Error Handling and Result Capture
Binding Stack Cleanup on Death (Without
Mutex and Condition Variable Dispatch
Pinned Blocking Fallback to OS Primitives
Scalability Under High Connection Counts
Platform-Specific Assembly and I/O Backends
Appendix A: Using Hunchentoot with Fibers
Many server workloads are concurrent but not parallel. A web server
handling 10,000 connections spends almost all of its time waiting for
network I/O; the actual computation per request is trivial. The
natural programming model is one thread of control per connection —
read a request, compute a response, write it back — but OS threads
are too expensive to use this way at scale.
Each OS thread in SBCL carries a full-sized control stack (typically
8 MB), a binding stack, signal handling infrastructure, and a kernel
task_struct. Creating a thread requires
setup; destroying one requires the reverse. Context switching between
threads requires a kernel transition, TLB management, and scheduler
bookkeeping. At 10,000 concurrent connections, this means 80 GB of
virtual address space for stacks alone, and the kernel scheduler —
designed for dozens to hundreds
