#!/usr/bin/env python3
"""
build_html.py — render every Markdown page in content/ into a multi-page site.

Each file in content/*.md becomes one self-contained HTML page. The Markdown is
embedded inside the HTML (no fetch), so pages render when opened directly from
disk (file://) or served by GitHub / GitLab Pages — no server or CORS workaround
required. Diagrams use Mermaid; code uses highlight.js (via CDN).

Add a page:      drop a new  content/<name>.md  with front-matter (see below).
Edit a page:     change its  content/<name>.md  and re-run this script.
The GitHub Pages workflow runs this automatically on every push.

Front-matter (YAML-ish, one `key: value` per line, between two `---` lines):

    ---
    title: Lab 1 — NetDevOps CI/CD   # <title> + card heading
    nav: Lab 1 · NetDevOps           # short label in the sidebar / cards
    order: 2                         # sort order across the site
    eyebrow: Lab 1                   # small kicker above the card title
    description: one-line summary     # <meta> + card body text
    ---

The home page (order 1) may contain a  <!-- CARDS -->  marker, which is replaced
with navigation cards for every *other* page.

Usage:  python build_html.py
"""
import pathlib
import html

HERE = pathlib.Path(__file__).parent
CONTENT = HERE / "content"


def parse_front_matter(text):
    """Return (meta_dict, body). Front-matter is an optional leading --- block."""
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip()] = val.strip()
    return meta, body


def load_pages():
    pages = []
    for md_file in sorted(CONTENT.glob("*.md")):
        meta, body = parse_front_matter(md_file.read_text(encoding="utf-8"))
        slug = md_file.stem  # index.md -> index
        pages.append({
            "slug": slug,
            "output": slug + ".html",
            "title": meta.get("title", slug),
            "nav": meta.get("nav", meta.get("title", slug)),
            "eyebrow": meta.get("eyebrow", ""),
            "description": meta.get("description", ""),
            "order": int(meta.get("order", "999")),
            "body": body,
        })
    pages.sort(key=lambda p: (p["order"], p["slug"]))
    return pages


def build_cards(pages, current_slug):
    """HTML navigation cards for every page except the current one."""
    cards = []
    for p in pages:
        if p["slug"] == current_slug:
            continue
        cards.append(
            '<a class="card" href="{href}">'
            '<span class="card-eyebrow">{eyebrow}</span>'
            '<span class="card-title">{title}</span>'
            '<span class="card-desc">{desc}</span>'
            '<span class="card-go">Open →</span>'
            "</a>".format(
                href=html.escape(p["output"]),
                eyebrow=html.escape(p["eyebrow"] or p["nav"]),
                title=html.escape(p["nav"]),
                desc=html.escape(p["description"]),
            )
        )
    return '<div class="cards">' + "".join(cards) + "</div>"


def build_page_nav(pages, current_slug):
    """Server-rendered cross-page links for the sidebar."""
    links = []
    for p in pages:
        cls = "page-link active" if p["slug"] == current_slug else "page-link"
        links.append(
            '<a class="{cls}" href="{href}">{label}</a>'.format(
                cls=cls,
                href=html.escape(p["output"]),
                label=html.escape(p["nav"]),
            )
        )
    return "".join(links)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<meta name="description" content="__DESCRIPTION__">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%230d274d'/><text x='50' y='72' font-size='60' text-anchor='middle' fill='%2300bceb' font-family='Arial' font-weight='bold'>d</text></svg>">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css">
<style>
:root{
  --bg:#0b1a2f; --panel:#0f2645; --panel2:#12305a; --text:#e8eef7; --muted:#9db3d1;
  --accent:#00bceb; --accent2:#1ba0d7; --border:#1d3a63; --code-bg:#0a1526;
  --shadow:0 8px 30px rgba(0,0,0,.35);
}
[data-theme="light"]{
  --bg:#f4f7fb; --panel:#ffffff; --panel2:#eef4fb; --text:#12233d; --muted:#546b8a;
  --accent:#0d7fb0; --accent2:#0a6a95; --border:#d9e3f0; --code-bg:#0d1b2e;
  --shadow:0 6px 24px rgba(20,40,80,.12);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
  line-height:1.65;font-size:16px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
/* ---- layout ---- */
.sidebar{position:fixed;top:0;left:0;width:300px;height:100vh;overflow-y:auto;
  background:var(--panel);border-right:1px solid var(--border);padding:22px 18px}
.brand{font-weight:800;font-size:1.15rem;line-height:1.2;padding:6px 8px 14px;
  border-bottom:1px solid var(--border);margin-bottom:12px;display:block;color:var(--text)}
.brand:hover{text-decoration:none}
.brand small{display:block;color:var(--muted);font-weight:600;font-size:.72rem;margin-top:4px;letter-spacing:.04em}
.brand .dot{color:var(--accent)}
.nav-label{color:var(--muted);font-size:.68rem;font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;margin:14px 8px 6px}
#pages{display:flex;flex-direction:column;gap:2px}
#pages .page-link{color:var(--muted);padding:7px 10px;border-radius:7px;font-size:.92rem;
  border-left:2px solid transparent;font-weight:600}
#pages .page-link:hover{background:var(--panel2);color:var(--text);text-decoration:none}
#pages .page-link.active{color:var(--accent);border-left-color:var(--accent);background:var(--panel2)}
#toc{display:flex;flex-direction:column;gap:1px;margin-top:2px}
#toc a{color:var(--muted);padding:5px 10px;border-radius:7px;font-size:.88rem;border-left:2px solid transparent}
#toc a:hover{background:var(--panel2);color:var(--text);text-decoration:none}
#toc a.lvl3{padding-left:22px;font-size:.82rem}
#toc a.active{color:var(--accent);border-left-color:var(--accent);background:var(--panel2)}
.theme-toggle{margin-top:16px;width:100%;padding:8px;border:1px solid var(--border);
  background:var(--panel2);color:var(--text);border-radius:8px;cursor:pointer;font-size:.85rem}
.theme-toggle:hover{border-color:var(--accent)}
/* ---- content ---- */
.content{margin-left:300px;max-width:900px;padding:40px 48px 120px}
.content h1{font-size:2rem;line-height:1.2;margin:.2em 0 .4em;background:linear-gradient(90deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.content h2{font-size:1.5rem;margin:2.2em 0 .6em;padding-bottom:.3em;border-bottom:2px solid var(--border);scroll-margin-top:20px}
.content h3{font-size:1.18rem;margin:1.8em 0 .5em;color:var(--accent);scroll-margin-top:20px}
.content h4{font-size:1.02rem;margin:1.4em 0 .4em;scroll-margin-top:20px}
.content p,.content li{color:var(--text)}
.content ul,.content ol{padding-left:1.4em}
.content li{margin:.28em 0}
.content code{background:var(--code-bg);color:#e6edf3;padding:.15em .4em;border-radius:5px;font-size:.86em;
  font-family:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.content pre{background:var(--code-bg);border:1px solid var(--border);border-radius:12px;
  padding:16px 18px;overflow:auto;box-shadow:var(--shadow)}
.content pre code{background:none;padding:0;font-size:.85rem;line-height:1.55}
.content blockquote{margin:1.2em 0;padding:.6em 1.1em;background:var(--panel);
  border-left:4px solid var(--accent);border-radius:0 10px 10px 0;color:var(--text)}
.content blockquote p{margin:.4em 0}
.content table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:.92rem;
  background:var(--panel);border-radius:10px;overflow:hidden;box-shadow:var(--shadow)}
.content th,.content td{border:1px solid var(--border);padding:9px 13px;text-align:left;vertical-align:top}
.content th{background:var(--panel2);color:var(--text);font-weight:700}
.content tr:nth-child(even) td{background:rgba(127,127,127,.05)}
.content hr{border:none;border-top:1px solid var(--border);margin:2.4em 0}
.content h1,.content h2,.content h3,.content h4{position:relative}
.mermaid{background:#ffffff;border-radius:12px;padding:18px;margin:1.4em 0;text-align:center;
  box-shadow:var(--shadow);overflow:auto}
/* ---- nav cards (home page) ---- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:1.6em 0}
.card{display:flex;flex-direction:column;gap:6px;padding:18px 18px 16px;background:var(--panel);
  border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow);transition:transform .12s,border-color .12s}
.card:hover{transform:translateY(-3px);border-color:var(--accent);text-decoration:none}
.card-eyebrow{color:var(--accent);font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.card-title{color:var(--text);font-size:1.12rem;font-weight:800;line-height:1.2}
.card-desc{color:var(--muted);font-size:.88rem;line-height:1.45;flex:1}
.card-go{color:var(--accent);font-size:.82rem;font-weight:700;margin-top:2px}
.hamburger{display:none;position:fixed;top:12px;left:12px;z-index:30;background:var(--panel);
  color:var(--text);border:1px solid var(--border);border-radius:8px;font-size:1.2rem;padding:6px 12px;cursor:pointer}
.checkbox-note{color:var(--muted)}
@media(max-width:900px){
  .sidebar{transform:translateX(-100%);transition:transform .25s;z-index:25;width:82%;max-width:320px}
  .sidebar.open{transform:none}
  .content{margin-left:0;padding:64px 20px 100px}
  .hamburger{display:block}
}
</style>
</head>
<body>
<button class="hamburger" id="hamburger" aria-label="Menu">&#9776;</button>
<aside class="sidebar" id="sidebar">
  <a class="brand" href="index.html">dCloud<span class="dot">.</span>Automation<small>Training Lab Guide</small></a>
  <div class="nav-label">Guide</div>
  <nav id="pages" aria-label="Pages">__PAGE_NAV__</nav>
  <div class="nav-label">On this page</div>
  <nav id="toc" aria-label="Contents"></nav>
  <button class="theme-toggle" id="theme-toggle">&#9788; Toggle light / dark</button>
</aside>
<main class="content markdown-body" id="content"></main>

<script id="md" type="text/markdown">__MARKDOWN__</script>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
<script>
(function(){
  function slugify(t){
    return t.toLowerCase().trim().replace(/[^\w\s-]/g,"").replace(/\s/g,"-");
  }
  var src = document.getElementById("md").textContent;
  marked.setOptions({gfm:true, breaks:false, headerIds:false, mangle:false});
  var content = document.getElementById("content");
  content.innerHTML = marked.parse(src);

  // Give every heading a GitHub-style id so the in-page TOC anchors resolve.
  var used = {};
  content.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach(function(h){
    var id = slugify(h.textContent); if(used[id]){used[id]++; id=id+"-"+used[id];} else {used[id]=1;}
    h.id = id;
  });

  // Convert ```mermaid code blocks into <div class="mermaid"> (decoded text).
  content.querySelectorAll("code.language-mermaid").forEach(function(code){
    var div = document.createElement("div");
    div.className = "mermaid";
    div.textContent = code.textContent;
    code.parentNode.replaceWith(div);
  });
  try{
    mermaid.initialize({startOnLoad:false, theme:"default", securityLevel:"loose"});
    mermaid.run({querySelector:".mermaid"});
  }catch(e){console.error("mermaid",e);}

  // Highlight non-mermaid code blocks.
  content.querySelectorAll("pre code").forEach(function(el){
    if(!el.classList.contains("language-mermaid")){ try{hljs.highlightElement(el);}catch(e){} }
  });

  // Build the in-page TOC from h2 + h3.
  var toc = document.getElementById("toc");
  content.querySelectorAll("h2,h3").forEach(function(h){
    var a = document.createElement("a");
    a.href = "#"+h.id; a.textContent = h.textContent;
    if(h.tagName==="H3") a.className="lvl3";
    toc.appendChild(a);
  });

  // Active-link highlighting on scroll.
  var links = Array.prototype.slice.call(toc.querySelectorAll("a"));
  var map = {}; links.forEach(function(a){ map[a.getAttribute("href").slice(1)] = a; });
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        links.forEach(function(l){l.classList.remove("active");});
        var a = map[en.target.id]; if(a){a.classList.add("active");
          a.scrollIntoView({block:"nearest"});}
      }
    });
  },{rootMargin:"0px 0px -75% 0px"});
  content.querySelectorAll("h2,h3").forEach(function(h){obs.observe(h);});

  // Mobile menu.
  var sb = document.getElementById("sidebar");
  document.getElementById("hamburger").addEventListener("click",function(){sb.classList.toggle("open");});
  toc.addEventListener("click",function(){sb.classList.remove("open");});

  // Theme toggle (persisted).
  var stored = null; try{ stored = localStorage.getItem("labguide-theme"); }catch(e){}
  if(stored){ document.documentElement.setAttribute("data-theme", stored); }
  document.getElementById("theme-toggle").addEventListener("click",function(){
    var htmlEl = document.documentElement;
    var next = htmlEl.getAttribute("data-theme")==="dark" ? "light" : "dark";
    htmlEl.setAttribute("data-theme", next);
    try{ localStorage.setItem("labguide-theme", next); }catch(e){}
  });
})();
</script>
</body>
</html>"""


def render(page, pages):
    body = page["body"]
    if "<!-- CARDS -->" in body:
        body = body.replace("<!-- CARDS -->", build_cards(pages, page["slug"]))
    # Stop the embedded markdown from prematurely closing the <script> block.
    md_safe = body.replace("</script>", "<\\/script>")
    out = TEMPLATE
    out = out.replace("__TITLE__", html.escape(page["title"]))
    out = out.replace("__DESCRIPTION__", html.escape(page["description"]))
    out = out.replace("__PAGE_NAV__", build_page_nav(pages, page["slug"]))
    out = out.replace("__MARKDOWN__", md_safe)
    return out


def main():
    if not CONTENT.is_dir():
        raise SystemExit("No content/ directory found next to build_html.py")
    pages = load_pages()
    if not pages:
        raise SystemExit("No .md files found in content/")
    for page in pages:
        out = render(page, pages)
        dest = HERE / page["output"]
        dest.write_text(out, encoding="utf-8")
        print("Wrote {} ({:,} bytes)".format(dest.name, len(out)))
    print("Built {} page(s).".format(len(pages)))


if __name__ == "__main__":
    main()
