---
title: Deriving Type Erasure
source: hacker_news
url: https://david.alvarezrosa.com/posts/deriving-type-erasure/
---

Title: Deriving Type Erasure
Score: 26 points by dalvrosa
Comments: 7

Article content:
and wondered what’s going on behind the
scenes? Beneath the intimidating interface is a classic technique
called type erasure: concrete types hidden behind a small, uniform
Starting from familiar tools like virtual functions and templates, we’ll
. By the end, you’ll have a clear
understanding of how type erasure works under the hood.
The typical way to achieve polymorphism is to define an interface
consisting of pure-virtual methods you want to be able to call. Then,
for each implementation that you want to use polymorphically, you create
a subclass that inherits from the base class and implement those
As an example, let’s implement shape classes that have an
method. We start with an interface
Remember that interfaces that are intended to be used through a
must have a virtual destructor, to ensure derived
classes are properly destructed
And add a couple of concrete implementations for
Now, we can use these implementations generically, by coding against the
Inheritance is a good solution to problems that require polymorphism,
but sometimes the concrete types you want to handle polymorphically
cannot share a common base class.
In some cases, you may not have control of the concrete types
possible for the concrete type to inherit (e.g. builtins like
provide the same interface, you can use a template to get polymorphism
because the compiler generates a version of the function for each
concrete type you use, and the call is valid as long as that generated
If you tried to pass in a type that doesn’t conform to the
), the compiler would hit an error when
you try to compile the method call, complaining that
Unfortunately, template-based polymorphism has two main downsides.
templates do not give you one shared runtime base type like
. Each instantiation is a distinct type, so there is no common
type for a homogeneous container; you cannot store a mix of
in one array and handle them uniformly the way you can with a
Since you’re employing polymorphism in the first place, most
callers will likely fall into the second group, and will need to be
templates themselves too so they can pass the type through. That can
quickly spread templates across the codebase, making it harder to read
and structure, increasing compile times, and producing larger binaries
is a little more subtle. Anybody who uses
specify the concrete type, or be a template itself, to pass along the
are fixed types with no shared base class,
and you cannot change them to inherit from one. But you still want to
handle them through a single common interface.
One way to do that is to introduce wrappers. Define your own
interface, then create wrapper classes that inherit from
; each wrapper implements the virtual
methods by simply forwarding calls to the wrapped object
Now we can work directly with instances of
This approach works, but it has an obvious downside: you need a separate
) for every concrete type you want to
), which quickly turns into a pile of
boilerplate. Luckily, templates can offload 
