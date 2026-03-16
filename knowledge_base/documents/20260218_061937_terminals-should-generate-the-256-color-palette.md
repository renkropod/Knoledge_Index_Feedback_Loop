---
title: Terminals should generate the 256-color palette
source: hacker_news
url: https://gist.github.com/jake-stewart/0a8ea46159a7da2c808e5be2177e1783
points: 495
---

Title: Terminals should generate the 256-color palette
Points: 495, Author: tosh, Comments: 206

Let your Coding Agent debug your browser session with Chrome DevTools MCP
Stay organized with collections
Save and categorize content based on your preferences.
We shipped an enhancement to the Chrome DevTools MCP server that many of our
users have been asking for: the ability for coding agents to directly connect to
With this enhancement, coding agents are able to:
Re-use an existing browser session:
Imagine you want your coding agent
to fix an issue that is gated behind a sign-in. Your coding agent can now
directly access your current browsing session not requiring an additional
Access active debugging sessions:
Coding agents can now access an active
debugging session in the DevTools UI. For example, when you discover a
failing network request in the Chrome DevTools network panel, select the
request and ask your coding agent to investigate it. The same also works
with elements selected in the Elements panel. We are excited about this new
ability to seamlessly transition between manual and AI-assisted debugging.
The auto connection feature is an addition to the existing ways for the Chrome
DevTools MCP to connect to a Chrome instance. Note that you can still:
Run Chrome with a Chrome DevTools MCP server-specific user profile (current
Connect to a running Chrome instance with a remote debug port.
Run multiple Chrome instances in isolation with each instance running in a
We've added a new feature to Chrome M144 (currently in Beta) that allows the
Chrome DevTools MCP server to request a remote debugging connection. This new
existing remote debugging capabilities of
debugging connections are disabled in Chrome. Developers have to explicitly
enable the feature first by going to
chrome://inspect#remote-debugging
When the Chrome DevTools MCP server is configured with the
option, the MCP server will connect to an active Chrome instance and request a
remote debugging session. To avoid misuse by malicious actors, every time the
Chrome DevTools MCP server requests a remote debugging session, Chrome will show
a dialog to the user and ask for their permission to allow the remote debugging
session. In addition to that, while a debugging session is active, Chrome
displays the "Chrome is being controlled by automated test software" banner at
The new remote debugging flow and UI in Chrome.
To use the new remote debugging capabilities. You have to first enable remote
debugging in Chrome and then configure the Chrome DevTools MCP server to use the
Step 1: Set up remote debugging in Chrome
In Chrome (>=144), do the following to set up remote debugging:
chrome://inspect/#remote-debugging
Follow the dialog UI to allow or disallow incoming debugging connections.
Remote debugging needs to be enabled, before clients can request a remote debugging connection.
Step 2: Configure Chrome DevTools MCP server to automatically connect to a running Chrome Instance
server to the running Chrome instance, use
command line argument for the MCP server set.
The following code snippet 
