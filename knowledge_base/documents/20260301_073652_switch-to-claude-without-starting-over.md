---
title: Switch to Claude without starting over
source: hacker_news
url: https://claude.com/import-memory
points: 592
---

Title: Switch to Claude without starting over
Points: 592, Author: doener, Comments: 273

Every map is different. Every map is seeded and deterministic.
I've been obsessed with procedural maps since I was a kid rolling dice on the random dungeon tables in the AD&D Dungeon Master's Guide. There was something magical about it — you didn't
it, one room at a time, and the dice decided whether you got a treasure chamber or a dead end full of rats.
Years later, I decided to build my own map generator. It creates little medieval island worlds — with roads, rivers, coastlines, cliffs, forests, and villages — entirely procedurally. Built with Three.js WebGPU and TSL shaders, about 4,100 hex cells across 19 grids, generated in ~20 seconds.
Carcassonne, but a Computer Does It
(WFC), an algorithm originally created by
that's become a darling of procgen gamedev.
, you already understand WFC. You have a stack of tiles and place them so everything lines up. Each tile has edges — grass, road, city.
Adjacent tiles must have matching edges.
A road edge must connect to another road edge. Grass must meet grass. The only difference is that the computer does it faster, and complains less when it gets stuck.
The twist: hex tiles have 6 edges instead of 4. That's 50% more constraints per tile, and the combinatorial explosion is real. Square WFC is well-trodden territory. Hex WFC is... less so.
For this map there are 30 different tiles defining grass, water, roads, rivers, coasts and slopes. Each tile in the set has a definition which describes the terrain type of each of its 6 edges, plus a weight used for favoring some tiles over others.
30 tile types, each with 6 rotations and 5 elevation levels. That's 900 possible states per cell.
For example this 3-way junction has 3 road edges and 3 grass edges. Tile definition:
{ name: 'ROAD_D', mesh: 'hex_road_D',
edges: { NE: 'road', E: 'grass', SE: 'road', SW: 'grass', W: 'road', NW: 'grass' },
Each tile defines 6 edge types. Matching edges is the only rule.
Every cell on the grid begins as a superposition of
— all 30 types, all 6 rotations, all 5 elevation levels. Pure possibility.
Collapse the most constrained cell.
Pick the cell with the fewest remaining options (lowest entropy). Randomly choose one of its valid states.
That choice constrains its neighbors. Remove any neighbor states whose edges don't match. This cascades outward — one collapse can eliminate hundreds of possibilities across the grid.
until every cell is solved — or you get stuck.
Getting stuck is the interesting part.
WFC is reliable for small grids. But as the grid gets bigger, the chance of painting yourself into a dead end goes up fast. A 217-cell hex grid almost never fails. A 4123-cell grid fails regularly.
. Instead of one giant solve, the map is split into 19 hexagonal grids arranged in two rings around a center — about 4,100 cells total. Each grid is solved independently, but it has to match whatever tiles were already placed in neighboring grids. Those border tiles become fixed constraints.
And sometimes those constraints are simply inc
