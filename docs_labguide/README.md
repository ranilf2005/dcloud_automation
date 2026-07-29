# dCloud Automation — Lab Guide (docs)

Attendee-facing training lab guide for the two automation projects:

- **Lab 1 — NetDevOps CI/CD** (`clmel26_automation/`)
- **Lab 2 — Cisco Security IaC** (`cisco_security_iac/`)

## Contents

| File | Purpose |
|------|---------|
| [`LAB_GUIDE.md`](LAB_GUIDE.md) | The full guide in Markdown (source of truth) |
| `index.html` | Self-contained HTML render of the guide (open in any browser) |
| `build_html.py` | Regenerates `index.html` from `LAB_GUIDE.md` |
| `.gitlab-ci.yml` | GitLab Pages job that publishes the guide as a web page |

## Read it

- **HTML:** open `index.html` in a browser, or via GitLab Pages once published.
- **Markdown:** read `LAB_GUIDE.md` directly on GitHub/GitLab.

## Rebuild the HTML after editing the Markdown

```bash
python3 build_html.py     # writes index.html
```

The HTML embeds the Markdown inline and renders it with marked + Mermaid +
highlight.js (via CDN), so it works when opened directly or served statically.
