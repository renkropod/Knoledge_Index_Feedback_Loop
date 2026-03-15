---
title: Agents prefer structured queries over natural language when given the choice
source: hacker_news
url: 
---

Title: Agents prefer structured queries over natural language when given the choice
Score: 3 points by snoren
Comments: 2

Cala&#x27;s team shared a finding on LinkedIn that&#x27;s worth sitting with. They shipped an MCP server with three access patterns for their knowledge graph: natural language queries, a structured query language, and direct entity&#x2F;relationship traversal.<p>They expected agents to default to natural language. Instead, most agents switched to structured queries and graph traversal on their own. No prompting, no nudging.<p>The obvious explanation is &quot;agents prefer efficiency.&quot; I don&#x27;t think that&#x27;s quite right. What they prefer is determinism.<p>A natural language query introduces two interpretation layers: the agent generates a query in prose, a system interprets that prose, then returns a result the agent has to parse. At no point can the agent verify the query was understood correctly. With a structured query, the contract is explicit. The agent knows exactly what it asked for and can verify what it got back.<p>This isn&#x27;t an emergent preference for efficiency. It&#x27;s tool-use chain-of-thought doing what it&#x27;s supposed to do: picking the path where the agent can most reliably confirm it got the right answer before moving to the next step.<p>A few implications if this holds up:<p>- NL-first tool interfaces might be optimizing for the wrong user. The human operator wants NL. The agent doesn&#x27;t.                                                                                           
- MCP servers that only expose NL endpoints are forcing agents through a non-deterministic bottleneck they&#x27;d avoid if given the choice.
- Tool design for agents should probably default to structured access with NL as a fallback, not the other way around.
