import json


def render_graph_html(graph: dict) -> str:
    graph_json = json.dumps(graph)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>TalkingDB Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    #graph-container {{
      width: 100vw;
      height: 100vh;
    }}

    svg {{
      width: 100%;
      height: 100%;
      cursor: grab;
      background: #ffffff;
    }}

    svg:active {{
      cursor: grabbing;
    }}

    .tooltip {{
      position: absolute;
      padding: 6px 10px;
      background: rgba(15, 23, 42, 0.95);
      color: white;
      border-radius: 6px;
      font-size: 12px;
      pointer-events: none;
      white-space: nowrap;
      opacity: 0;
      transition: opacity 0.1s ease;
      z-index: 1000;
      max-width: 360px;
      white-space: normal;
    }}

    .panel {{
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(255, 255, 255, 0.98);
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
      padding: 14px 16px;
      font-size: 13px;
      color: #0f172a;
      width: 260px;
      max-height: calc(100vh - 32px);
      overflow-y: auto;
    }}

    .panel h3 {{
      margin: 0 0 6px 0;
      font-size: 13px;
      font-weight: 600;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .panel h4 {{
      margin: 12px 0 6px 0;
      font-size: 11px;
      font-weight: 600;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .panel label {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      cursor: pointer;
      user-select: none;
    }}

    .panel label:hover {{
      color: #2563eb;
    }}

    .panel input[type="checkbox"], .panel input[type="radio"] {{
      margin: 0;
      cursor: pointer;
    }}

    .swatch {{
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }}

    .swatch-line {{
      display: inline-block;
      width: 18px;
      height: 3px;
      border-radius: 2px;
      flex-shrink: 0;
    }}

    .panel-divider {{
      height: 1px;
      background: #e2e8f0;
      margin: 12px 0 4px 0;
    }}

    .search-box {{
      width: 100%;
      box-sizing: border-box;
      padding: 6px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 12px;
      outline: none;
      margin-top: 4px;
    }}

    .search-box:focus {{
      border-color: #2563eb;
    }}

    .btn-row {{
      display: flex;
      gap: 6px;
      margin-top: 8px;
    }}

    .btn {{
      flex: 1;
      padding: 6px 10px;
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      border-radius: 6px;
      cursor: pointer;
      font-size: 11px;
      color: #0f172a;
    }}

    .btn:hover {{
      background: #eff6ff;
      border-color: #2563eb;
      color: #2563eb;
    }}

    .stats {{
      font-size: 11px;
      color: #64748b;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px dashed #e2e8f0;
    }}

    .node-faded {{
      opacity: 0.08 !important;
    }}

    .link-faded {{
      opacity: 0.05 !important;
    }}

    .node-highlight {{
      stroke: #0f172a;
      stroke-width: 2.5px;
    }}

    .link-highlight {{
      stroke: #0f172a !important;
      stroke-opacity: 1 !important;
      stroke-width: 2.2px !important;
    }}
  </style>
</head>
<body>
<div class="tooltip" id="tooltip"></div>

<div class="panel" id="panel">
  <h3>TalkingDB Graph</h3>

  <input type="text" class="search-box" id="search" placeholder="Search nodes by label or ID..." />

  <h4>Relationship (edge)</h4>
  <div id="edge-filters"></div>

  <h4>Node type</h4>
  <div id="node-filters"></div>

  <div class="panel-divider"></div>

  <h4>Highlight mode</h4>
  <label><input type="radio" name="hl-mode" value="filter" checked /> Filter (hide others)</label>
  <label><input type="radio" name="hl-mode" value="highlight" /> Highlight (fade others)</label>

  <div class="btn-row">
    <button class="btn" id="btn-all">Select all</button>
    <button class="btn" id="btn-none">Clear</button>
    <button class="btn" id="btn-reset">Reset view</button>
  </div>

  <div class="stats" id="stats"></div>
</div>

<div id="graph-container">
  <svg></svg>
</div>

<script>
const data = {graph_json};

// --- Normalize: networkx node_link_data may emit "links" or "edges" ---
const rawLinks = data.links || data.edges || [];

// Defensive: build unique edge type and node type lists
const EDGE_COLORS = {{
  "part_of":   "#2563eb",
  "contains":  "#16a34a",
  "key_value": "#d97706",
  "describes": "#9333ea",
  "unknown":   "#94a3b8"
}};

const NODE_COLORS = {{
  "file@root":        "#0f172a",
  "section@outline":  "#1d4ed8",
  "section@para":     "#60a5fa",
  "paragraph":        "#0ea5e9",
  "table":            "#f59e0b",
  "header":           "#ea580c",
  "unigram":          "#16a34a",
  "bigram":           "#22c55e",
  "trigram":          "#84cc16",
  "unknown":          "#94a3b8"
}};

function nodeKind(n) {{
  if (n.index && NODE_COLORS[n.index]) return n.index;
  if (n.type && NODE_COLORS[n.type]) return n.type;
  return n.type || n.index || "unknown";
}}

function edgeKind(e) {{
  return e.type || "unknown";
}}

const edgeTypes = Array.from(new Set(rawLinks.map(edgeKind))).sort();
const nodeTypes = Array.from(new Set(data.nodes.map(nodeKind))).sort();

const activeEdgeTypes = new Set(edgeTypes);
const activeNodeTypes = new Set(nodeTypes);
let highlightMode = "filter"; // or "highlight"
let searchTerm = "";

// --- Build filter UI ---
const edgeFilterDiv = document.getElementById("edge-filters");
edgeTypes.forEach(t => {{
  const color = EDGE_COLORS[t] || EDGE_COLORS.unknown;
  const id = "edge-" + t;
  const label = document.createElement("label");
  label.innerHTML = `<input type="checkbox" id="${{id}}" checked data-edge="${{t}}"/>
    <span class="swatch-line" style="background:${{color}}"></span>
    <span>${{t}}</span>`;
  edgeFilterDiv.appendChild(label);
}});

const nodeFilterDiv = document.getElementById("node-filters");
nodeTypes.forEach(t => {{
  const color = NODE_COLORS[t] || NODE_COLORS.unknown;
  const id = "node-" + t;
  const label = document.createElement("label");
  label.innerHTML = `<input type="checkbox" id="${{id}}" checked data-node="${{t}}"/>
    <span class="swatch" style="background:${{color}}"></span>
    <span>${{t}}</span>`;
  nodeFilterDiv.appendChild(label);
}});

// --- D3 setup ---
const svg = d3.select("svg");
const container = document.getElementById("graph-container");
let width = container.clientWidth;
let height = container.clientHeight;

const g = svg.append("g");

const zoom = d3.zoom()
  .scaleExtent([0.1, 5])
  .on("zoom", (event) => {{
    g.attr("transform", event.transform);
  }});

svg.call(zoom);

// Force simulation — run once, then pin nodes so layout stays stable
// while the user types/filters.
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(rawLinks).id(d => d.id).distance(90))
  .force("charge", d3.forceManyBody().strength(-350))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .alphaDecay(0.035);

// Once initial layout settles, pin every node so the graph stops moving.
// Dragging still works: dragstarted/dragended update fx/fy.
simulation.on("end", () => {{
  data.nodes.forEach(n => {{
    if (n.fx == null) n.fx = n.x;
    if (n.fy == null) n.fy = n.y;
  }});
}});

// Links
const link = g.append("g")
  .attr("stroke-opacity", 0.7)
  .selectAll("line")
  .data(rawLinks)
  .enter()
  .append("line")
  .attr("stroke", d => EDGE_COLORS[edgeKind(d)] || EDGE_COLORS.unknown)
  .attr("stroke-width", 1.4);

// Nodes
const node = g.append("g")
  .selectAll("circle")
  .data(data.nodes)
  .enter()
  .append("circle")
  .attr("r", d => {{
    const k = nodeKind(d);
    if (k === "file@root") return 14;
    if (k === "section@outline") return 11;
    if (k === "paragraph" || k === "section@para" || k === "table") return 9;
    return 6;
  }})
  .attr("fill", d => NODE_COLORS[nodeKind(d)] || NODE_COLORS.unknown)
  .attr("stroke", "#ffffff")
  .attr("stroke-width", 1.2)
  .call(
    d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended)
  );

// Tooltip
const tooltip = d3.select("#tooltip");

node
  .on("mouseenter", (event, d) => {{
    const parts = [
      `<strong>${{d.label ?? d.id}}</strong>`,
      `type: ${{d.type ?? "-"}}`,
      d.index ? `index: ${{d.index}}` : null,
      d.text ? `text: ${{(d.text + "").slice(0, 120)}}${{(d.text + "").length > 120 ? "…" : ""}}` : null
    ].filter(Boolean);
    tooltip.style("opacity", 1).html(parts.join("<br/>"));
  }})
  .on("mousemove", (event) => {{
    tooltip
      .style("left", event.pageX + 12 + "px")
      .style("top", event.pageY + 12 + "px");
  }})
  .on("mouseleave", () => {{
    tooltip.style("opacity", 0);
  }})
  .on("click", (event, d) => {{
    event.stopPropagation();
    focusNodeNeighborhood(d);
  }});

link
  .on("mouseenter", (event, d) => {{
    tooltip.style("opacity", 1).html(
      `<strong>${{edgeKind(d)}}</strong><br/>` +
      `${{(d.source.id ?? d.source)}} → ${{(d.target.id ?? d.target)}}`
    );
  }})
  .on("mousemove", (event) => {{
    tooltip
      .style("left", event.pageX + 12 + "px")
      .style("top", event.pageY + 12 + "px");
  }})
  .on("mouseleave", () => {{
    tooltip.style("opacity", 0);
  }});

// Clear focus on background click
svg.on("click", () => applyFilters());

// Tick update
simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);
}});

// Drag handlers
function dragstarted(event, d) {{
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}}

function dragged(event, d) {{
  d.fx = event.x;
  d.fy = event.y;
}}

function dragended(event, d) {{
  if (!event.active) simulation.alphaTarget(0);
  // Keep the node pinned at its new location so the graph doesn't drift.
  d.fx = d.x;
  d.fy = d.y;
}}

// --- Filtering / search logic ---
function edgeSrcId(e) {{ return (e.source && e.source.id) ?? e.source; }}
function edgeDstId(e) {{ return (e.target && e.target.id) ?? e.target; }}

function edgePassesTypeFilters(e) {{
  if (!activeEdgeTypes.has(edgeKind(e))) return false;
  const sNode = typeof e.source === "object" ? e.source : null;
  const tNode = typeof e.target === "object" ? e.target : null;
  if (sNode && !activeNodeTypes.has(nodeKind(sNode))) return false;
  if (tNode && !activeNodeTypes.has(nodeKind(tNode))) return false;
  return true;
}}

function nodeMatchesSearch(n) {{
  if (!searchTerm) return false;
  const q = searchTerm.toLowerCase();
  return (
    (n.id + "").toLowerCase().includes(q) ||
    (n.label ? (n.label + "").toLowerCase().includes(q) : false) ||
    (n.text ? (n.text + "").toLowerCase().includes(q) : false)
  );
}}

// Matched nodes + all neighbors reachable via currently-active edge types.
function computeSearchSubgraph() {{
  const matched = new Set();
  data.nodes.forEach(n => {{
    if (activeNodeTypes.has(nodeKind(n)) && nodeMatchesSearch(n)) matched.add(n.id);
  }});
  if (matched.size === 0) return {{ matched, nodes: new Set(), edges: new Set() }};

  const subNodes = new Set(matched);
  const subEdges = new Set();

  rawLinks.forEach(e => {{
    if (!activeEdgeTypes.has(edgeKind(e))) return;
    const sid = edgeSrcId(e);
    const tid = edgeDstId(e);
    if (matched.has(sid) || matched.has(tid)) {{
      subEdges.add(e);
      subNodes.add(sid);
      subNodes.add(tid);
    }}
  }});

  return {{ matched, nodes: subNodes, edges: subEdges }};
}}

// Called on every filter/search change. Does NOT touch the simulation,
// so nothing moves — only classes/styles update.
function applyView() {{
  // SEARCH MODE: fade everything except the matched subgraph.
  if (searchTerm) {{
    const sg = computeSearchSubgraph();

    node
      .style("display", null)
      .classed("node-faded", d => !sg.nodes.has(d.id))
      .classed("node-highlight", d => sg.matched.has(d.id));

    link
      .style("display", null)
      .classed("link-faded", e => !sg.edges.has(e))
      .classed("link-highlight", e => sg.edges.has(e));

    const matchCount = sg.matched.size;
    updateStats(
      sg.edges.size,
      sg.nodes.size,
      matchCount
        ? `${{matchCount}} match${{matchCount === 1 ? "" : "es"}} for "${{searchTerm}}"`
        : `No matches for "${{searchTerm}}"`
    );
    return;
  }}

  // FILTER-ONLY MODE: apply edge/node-type checkboxes.
  const visibleEdges = new Set(rawLinks.filter(edgePassesTypeFilters));
  const visibleNodes = new Set();
  visibleEdges.forEach(e => {{
    visibleNodes.add(edgeSrcId(e));
    visibleNodes.add(edgeDstId(e));
  }});
  // Keep isolated nodes whose type passes the filter
  data.nodes.forEach(n => {{
    if (activeNodeTypes.has(nodeKind(n))) visibleNodes.add(n.id);
  }});

  if (highlightMode === "filter") {{
    node
      .classed("node-faded", false)
      .classed("node-highlight", false)
      .style("display", d => visibleNodes.has(d.id) ? null : "none");

    link
      .classed("link-faded", false)
      .classed("link-highlight", false)
      .style("display", e => visibleEdges.has(e) ? null : "none");
  }} else {{
    node
      .style("display", null)
      .classed("node-faded", d => !visibleNodes.has(d.id))
      .classed("node-highlight", false);

    link
      .style("display", null)
      .classed("link-faded", e => !visibleEdges.has(e))
      .classed("link-highlight", false);
  }}

  updateStats(visibleEdges.size, visibleNodes.size);
}}

// Keep old name as alias so existing handlers still work.
const applyFilters = applyView;

function focusNodeNeighborhood(d) {{
  const neighborIds = new Set([d.id]);
  const keepEdges = new Set();

  const queue = [d.id];
  while (queue.length) {{
    const cur = queue.shift();
    rawLinks.forEach(e => {{
      if (!activeEdgeTypes.has(edgeKind(e))) return;
      const sid = edgeSrcId(e);
      const tid = edgeDstId(e);
      if (sid === cur && !neighborIds.has(tid)) {{
        neighborIds.add(tid);
        keepEdges.add(e);
        queue.push(tid);
      }} else if (tid === cur && !neighborIds.has(sid)) {{
        neighborIds.add(sid);
        keepEdges.add(e);
        queue.push(sid);
      }} else if (sid === cur || tid === cur) {{
        keepEdges.add(e);
      }}
    }});
  }}

  node
    .style("display", null)
    .classed("node-faded", n => !neighborIds.has(n.id))
    .classed("node-highlight", n => n.id === d.id);

  link
    .style("display", null)
    .classed("link-faded", e => !keepEdges.has(e))
    .classed("link-highlight", e => keepEdges.has(e));

  updateStats(keepEdges.size, neighborIds.size, `Focused on "${{d.label ?? d.id}}"`);
}}

function updateStats(visibleEdgeCount, visibleNodeCount, note) {{
  const totalNodes = data.nodes.length;
  const totalEdges = rawLinks.length;
  const shownNodes = visibleNodeCount !== undefined
    ? visibleNodeCount
    : data.nodes.filter(n => activeNodeTypes.has(nodeKind(n)) && nodeMatchesSearch(n)).length;
  const shownEdges = visibleEdgeCount !== undefined ? visibleEdgeCount : totalEdges;

  document.getElementById("stats").innerHTML =
    `Nodes: <strong>${{shownNodes}}</strong> / ${{totalNodes}}<br/>` +
    `Edges: <strong>${{shownEdges}}</strong> / ${{totalEdges}}` +
    (note ? `<br/><em>${{note}}</em>` : "");
}}

// --- Wire up UI events ---
document.querySelectorAll('input[data-edge]').forEach(cb => {{
  cb.addEventListener("change", () => {{
    const t = cb.dataset.edge;
    if (cb.checked) activeEdgeTypes.add(t); else activeEdgeTypes.delete(t);
    applyFilters();
  }});
}});

document.querySelectorAll('input[data-node]').forEach(cb => {{
  cb.addEventListener("change", () => {{
    const t = cb.dataset.node;
    if (cb.checked) activeNodeTypes.add(t); else activeNodeTypes.delete(t);
    applyFilters();
  }});
}});

document.querySelectorAll('input[name="hl-mode"]').forEach(r => {{
  r.addEventListener("change", () => {{
    highlightMode = r.value;
    applyFilters();
  }});
}});

document.getElementById("search").addEventListener("input", (e) => {{
  searchTerm = e.target.value.trim();
  applyFilters();
}});

document.getElementById("btn-all").addEventListener("click", () => {{
  edgeTypes.forEach(t => activeEdgeTypes.add(t));
  nodeTypes.forEach(t => activeNodeTypes.add(t));
  document.querySelectorAll('input[data-edge], input[data-node]').forEach(cb => cb.checked = true);
  applyFilters();
}});

document.getElementById("btn-none").addEventListener("click", () => {{
  activeEdgeTypes.clear();
  activeNodeTypes.clear();
  document.querySelectorAll('input[data-edge], input[data-node]').forEach(cb => cb.checked = false);
  applyFilters();
}});

document.getElementById("btn-reset").addEventListener("click", () => {{
  searchTerm = "";
  document.getElementById("search").value = "";
  edgeTypes.forEach(t => activeEdgeTypes.add(t));
  nodeTypes.forEach(t => activeNodeTypes.add(t));
  document.querySelectorAll('input[data-edge], input[data-node]').forEach(cb => cb.checked = true);
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
  applyFilters();
}});

// Initial render
applyFilters();

// Handle resize
window.addEventListener("resize", () => {{
  width = container.clientWidth;
  height = container.clientHeight;
  simulation.force("center", d3.forceCenter(width / 2, height / 2));
  simulation.alpha(0.3).restart();
}});
</script>

</body>
</html>
"""
