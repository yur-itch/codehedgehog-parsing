"""Turn output/graph.json (from crawl.py) into a single self-contained,
offline HTML file you can open directly in a browser - no server, no CDN,
no network access needed (cytoscape.js is vendored in hits_scraper/vendor).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VENDOR_JS = Path(__file__).parent / "vendor" / "cytoscape.min.js"

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>code.hits.university content graph</title>
<style>
  html, body {{ margin:0; height:100%; font-family: system-ui, sans-serif; background:#111; color:#eee; }}
  #cy {{ position:absolute; top:0; left:280px; right:0; bottom:0; }}
  #panel {{ position:absolute; top:0; left:0; width:280px; bottom:0; overflow:auto;
            box-sizing:border-box; padding:12px; background:#1a1a1a; border-right:1px solid #333; }}
  #panel h2 {{ font-size:14px; margin:0 0 8px; }}
  #panel .stat {{ font-size:12px; color:#aaa; margin-bottom:4px; }}
  #detail {{ font-size:12px; word-break:break-all; }}
  #detail .url {{ color:#8ecbff; }}
  #detail .req {{ margin:6px 0; padding:6px; background:#222; border-radius:4px; }}
  #detail .status-ok {{ color:#7ee787; }}
  #detail .status-bad {{ color:#ff7b72; }}
  a {{ color:#8ecbff; }}
</style>
</head>
<body>
<div id="panel">
  <h2>code.hits.university - content graph</h2>
  <div class="stat">nodes: {n_nodes}</div>
  <div class="stat">edges: {n_edges}</div>
  <div class="stat" style="margin-top:8px; color:#888;">click a node for details</div>
  <div id="detail"></div>
</div>
<div id="cy"></div>
<script>{cytoscape_js}</script>
<script>
const graph = {graph_json};

const nodeIds = new Set();
const elements = [];

for (const n of graph.nodes) {{
  nodeIds.add(n.id);
  elements.push({{ data: {{ id: n.id, label: n.title || n.url, url: n.url, error: !!n.error }} }});
}}
if (!nodeIds.has("__seed__")) {{
  elements.push({{ data: {{ id: "__seed__", label: "(start)", url: "", error: false }} }});
  nodeIds.add("__seed__");
}}

let i = 0;
for (const e of graph.edges) {{
  if (!nodeIds.has(e.from) || !nodeIds.has(e.to)) continue;
  const methods = [...new Set((e.requests||[]).map(r => r.method))].join(",");
  elements.push({{
    data: {{
      id: "e" + (i++),
      source: e.from,
      target: e.to,
      label: methods,
      requests: e.requests || [],
    }}
  }});
}}

const cy = cytoscape({{
  container: document.getElementById("cy"),
  elements: elements,
  style: [
    {{ selector: "node", style: {{
        "background-color": "#4c8dff",
        "label": "data(label)",
        "color": "#eee",
        "font-size": 9,
        "width": 18, "height": 18,
        "text-wrap": "ellipsis", "text-max-width": 140,
        "text-valign": "bottom", "text-halign": "center",
        "text-margin-y": 4,
    }} }},
    {{ selector: "node[id = '__seed__']", style: {{ "background-color": "#f0883e", "shape": "diamond" }} }},
    {{ selector: "node[?error]", style: {{ "background-color": "#ff7b72" }} }},
    {{ selector: "edge", style: {{
        "width": 1.5,
        "line-color": "#555",
        "target-arrow-color": "#555",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        "label": "data(label)",
        "font-size": 7,
        "color": "#999",
    }} }},
  ],
  layout: {{ name: "cose", animate: false, nodeRepulsion: 8000, idealEdgeLength: 80 }},
}});

cy.on("tap", "node", (evt) => {{
  const d = evt.target.data();
  const incoming = cy.edges(`[target = "${{d.id}}"]`);
  let html = `<div class="url">${{d.url || "(start)"}}</div>`;
  incoming.forEach((edge) => {{
    const reqs = edge.data("requests") || [];
    if (reqs.length === 0) {{
      html += `<div class="req">from ${{edge.data("source")}} (no new request - revisit/cached)</div>`;
    }}
    for (const r of reqs) {{
      const cls = (r.status && r.status < 400) ? "status-ok" : "status-bad";
      html += `<div class="req"><b>${{r.method}}</b> <span class="${{cls}}">${{r.status}}</span><br>${{r.url}}</div>`;
    }}
  }});
  document.getElementById("detail").innerHTML = html;
}});
</script>
</body>
</html>
"""


def render(graph_path: str, out_path: str):
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    cytoscape_js = VENDOR_JS.read_text(encoding="utf-8")
    html = TEMPLATE.format(
        n_nodes=len(graph["nodes"]),
        n_edges=len(graph["edges"]),
        graph_json=json.dumps(graph, ensure_ascii=False),
        cytoscape_js=cytoscape_js,
    )
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default="output/graph.json")
    parser.add_argument("--out", default="output/graph_view.html")
    args = parser.parse_args()
    render(args.graph, args.out)


if __name__ == "__main__":
    main()
