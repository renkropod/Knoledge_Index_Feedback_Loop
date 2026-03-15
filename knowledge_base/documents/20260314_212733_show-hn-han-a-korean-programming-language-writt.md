---
title: Show HN: Han – A Korean programming language written in Rust
source: hacker_news
url: https://github.com/xodn348/han
---

Title: Show HN: Han – A Korean programming language written in Rust
Score: 110 points by xodn348
Comments: 67

A few weeks ago I saw a post about someone converting an entire C++ codebase to Rust using AI in under two weeks.<p>That inspired me — if AI can rewrite a whole language stack that fast, I wanted to try building a programming language from scratch with AI assistance.<p>I&#x27;ve also been noticing growing global interest in Korean language and culture, and I wondered: what would a programming language look like if every keyword was in Hangul (the Korean writing system)?<p>Han is the result. It&#x27;s a statically-typed language written in Rust with a full compiler pipeline (lexer → parser → AST → interpreter + LLVM IR codegen).<p>It supports arrays, structs with impl blocks, closures, pattern matching, try&#x2F;catch, file I&#x2F;O, module imports, a REPL, and a basic LSP server.<p>This is a side project, not a &quot;you should use this instead of Python&quot; pitch. 
Feedback on language design, compiler architecture, or the Korean keyword choices is very welcome.<p><a href="https:&#x2F;&#x2F;github.com&#x2F;xodn348&#x2F;han" rel="nofollow">https:&#x2F;&#x2F;github.com&#x2F;xodn348&#x2F;han</a>

Article content:
A general-purpose compiled language with Korean keywords — written in Rust
Han is a statically-typed, compiled programming language where every keyword is written in Korean. It compiles to native binaries through LLVM IR and also ships with a tree-walking interpreter for instant execution. The compiler toolchain is written entirely in Rust.
Han was born from the idea that programming doesn't have to look the same in every country. Hangul — the Korean writing system — is one of the most scientifically designed scripts in human history, and Han puts it to work as a first-class programming language rather than just a display string.
— name your variables and functions in Korean
— generates LLVM IR → clang → native binary
for editor hover docs and completion
with field access and impl blocks
변수 텍스트 = "hello world hello han world hello"
반복 변수 i = 0; i < 단어들.길이(); i += 1 {
반복 변수 j = 0; j < 단어목록.길이(); j += 1 {
반복 변수 i = 0; i < 단어목록.길이(); i += 1 {
출력(형식("{0}: {1}", 단어목록[i], 개수목록[i]))
반복 변수 i = 0; i < 목록.길이(); i += 1 {
출력(형식("{0} {1}. {2}", 상태, i + 1, 목록[i].제목))
파일쓰기("/tmp/test.txt", "첫번째 줄\n두번째 줄\n세번째 줄\n")
출력(형식("줄 수: {0}", 줄수세기("/tmp/test.txt")))
git clone https://github.com/xodn348/han.git
to launch with syntax highlighting + LSP support.
hgl interpret <file.hgl>    Run with interpreter (no clang needed)
hgl build <file.hgl>        Compile to native binary (requires clang)
hgl run <file.hgl>          Compile and run immediately
hgl repl                    Interactive REPL
hgl lsp                     Start LSP server (hover + completion)
Arrays with negative indexing —
Structs with field access and mutation —
for-loop with init, condition, step
pattern matching — integer, string, bool, wildcard
Named functions with typed parameters and return types
Recursion (fibonacci, factorial, etc.)
Closures / anonymous functions with environment capture —
Closures passed as arguments (without type annotation)
변수 p = 사람 { 이름: "홍길동", 나이: 30 }
구현 사람 { 함수 인사(자신: 사람) { ... } }
— catches any runtime error including division by zero, file not found, out-of-bounds
— substitutes from current scope
— type params are parsed and erased at runtime
fails. Pass closures without type annotation.
not supported — only one level deep
Codegen stubs for arrays/structs — interpreter only for those features
Standard library: network, process
Deep recursion will stack overflow
Hangul (한글) is not just a writing system — it is a feat of deliberate linguistic design. Created in 1443 by King Sejong the Great, each character encodes phonetic information in its geometric shape. Consonants mirror the tongue and mouth positions used to pronounce them. Vowels are composed from three cosmic symbols: heaven (·), earth (ㅡ), and human (ㅣ).
Han brings this elegance into programming. When you write
, you are not just defining a function — you are writing in a script that was purpose-built for clarity and beauty.
Hangul is also surprisingly easy to learn —
you can learn the whole system in an afternoon

