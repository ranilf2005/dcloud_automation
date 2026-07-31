# dCloud Automation — Lab Guide (docs)

Attendee-facing training lab guide for the two automation projects, published to
GitHub Pages: **<https://ranilf2005.github.io/dcloud_automation/>**

- **Lab 1 — NetDevOps CI/CD** (`clmel26_automation/`)
- **Lab 2 — Cisco Security IaC** (`cisco_security_iac/`)

## How it works

The site is **multi-page**. Each page is one Markdown file in [`content/`](content/) —
edit the Markdown, push, and GitHub Actions rebuilds and republishes the page
automatically (no need to touch any HTML).

| Path | Purpose |
|------|---------|
| [`content/index.md`](content/index.md) | **Home** — overview, lab access, code-server IDE, nav cards |
| [`content/lab1-netdevops.md`](content/lab1-netdevops.md) | **Lab 1** — NetDevOps CI/CD |
| [`content/lab2-security-iac.md`](content/lab2-security-iac.md) | **Lab 2** — Cisco Security IaC (FMC/FTD) |
| [`content/appendix.md`](content/appendix.md) | **Appendix** — credentials, cheat-sheet, troubleshooting |
| `build_html.py` | Renders every `content/*.md` into a self-contained `<slug>.html` |
| `*.html` | Generated pages (built by the workflow / `build_html.py`) |
| `../.github/workflows/pages.yml` | Runs the build and deploys to GitHub Pages on push |

## Edit a page

1. Open the matching file in [`content/`](content/) and edit the Markdown.
2. Commit and push to `main`.
3. The **Deploy Lab Guide to GitHub Pages** workflow runs `build_html.py` and
   republishes — the live page updates in a minute or two.

## Front-matter

Each `content/*.md` starts with a small block that controls its title, sidebar
label, sort order, and home-page card:

```yaml
---
title: Lab 1 — NetDevOps CI/CD   # <title> + card heading
nav: Lab 1 · NetDevOps           # short label in the sidebar / cards
order: 2                         # sort order across the site
eyebrow: Lab 1                   # small kicker above the card title
description: one-line summary     # <meta> + card body text
---
```

The home page (order 1) contains a `<!-- CARDS -->` marker that is replaced with
navigation cards for every other page. **Add a new page** by dropping another
`content/<name>.md` with front-matter — it appears in the sidebar and cards
automatically.

## Preview / rebuild locally

```bash
python3 build_html.py     # writes index.html + one .html per content/*.md
```

Open any generated `.html` in a browser. Each page embeds its Markdown inline and
renders it with marked + Mermaid + highlight.js (via CDN), so it works opened
directly (`file://`) or served statically.
