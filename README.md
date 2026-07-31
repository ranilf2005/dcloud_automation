# dCloud Automation

Monorepo for the **dCloud automation training labs**. It brings together two
hands-on labs and the attendee lab guide.

| Folder | Lab | Tech |
|--------|-----|------|
| [`clmel26_automation/`](clmel26_automation) | NetDevOps CI/CD — routers as code | pyATS · Ansible · GitLab CI/CD |
| [`cisco_security_iac/`](cisco_security_iac) | Cisco Security IaC — FMC/FTD firewall as code | Terraform · REST API · Ansible |
| [`docs_labguide/`](docs_labguide) | Attendee training lab guide | Multi-page site auto-built from Markdown |

## Start here

**▶ Live lab guide (GitHub Pages): <https://ranilf2005.github.io/dcloud_automation/>**

The guide is a multi-page site. Edit the Markdown in
[`docs_labguide/content/`](docs_labguide/content), push, and GitHub Actions rebuilds
and republishes it automatically (see [`docs_labguide/README.md`](docs_labguide/README.md)).

| Page | Live link |
|------|-----------|
| Home — overview, lab access, code-server IDE | <https://ranilf2005.github.io/dcloud_automation/index.html> |
| Lab 1 — Concepts & pipeline | <https://ranilf2005.github.io/dcloud_automation/lab1-netdevops.html> |
| Lab 1 — Hands-on walkthrough (screenshots) | <https://ranilf2005.github.io/dcloud_automation/lab1-hands-on.html> |
| Lab 2 — Security IaC (Terraform · REST · Ansible) | <https://ranilf2005.github.io/dcloud_automation/lab2-security-iac.html> |
| Appendix — credentials, cheat-sheet, troubleshooting | <https://ranilf2005.github.io/dcloud_automation/appendix.html> |
| Appendix — Lab 1 project files | <https://ranilf2005.github.io/dcloud_automation/appendix-lab1-files.html> |
| Appendix — Lab 2 project files | <https://ranilf2005.github.io/dcloud_automation/appendix-lab2-files.html> |

- **Markdown source:** [`docs_labguide/content/`](docs_labguide/content) (one `.md` per page)
- **HTML (local):** open `docs_labguide/index.html` in a browser
- The original single-file guide is archived at [`archive/LAB_GUIDE.md`](archive/LAB_GUIDE.md).

## Lab environment (summary)

| Service | Address | Credentials |
|---------|---------|-------------|
| code-server | `https://198.18.1.18:8080` | `C1sco12345` |
| GitLab | `http://198.18.1.18:8929` | `root / C1sco12345` |
| Devbox | `198.18.1.4` | `cisco / C1sco12345` |
| Cisco CML | `https://198.18.1.2` | `admin / C1sco12345` |

> Secrets are never committed. Credentials for devices are supplied at run time via
> environment variables (see each lab's README).
