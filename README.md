# dCloud Automation

Monorepo for the **dCloud automation training labs**. It brings together two
hands-on labs and the attendee lab guide.

| Folder | Lab | Tech |
|--------|-----|------|
| [`clmel26_automation/`](clmel26_automation) | NetDevOps CI/CD — routers as code | pyATS · Ansible · GitLab CI/CD |
| [`cisco_security_iac/`](cisco_security_iac) | Cisco Security IaC — FMC/FTD firewall as code | Terraform · REST API · Ansible |
| [`docs_labguide/`](docs_labguide) | Attendee training lab guide | HTML + Markdown |

## Start here

Read the full step-by-step training guide:

- **Markdown:** [`docs_labguide/LAB_GUIDE.md`](docs_labguide/LAB_GUIDE.md)
- **HTML:** open `docs_labguide/index.html` (or the published GitLab Pages site)

## Lab environment (summary)

| Service | Address | Credentials |
|---------|---------|-------------|
| code-server | `http://198.18.1.18:8080` | `C1sco12345` |
| GitLab | `http://198.18.1.18:8929` | `root / C1sco12345` |
| Devbox | `198.18.1.4` | `cisco / C1sco12345` |
| Cisco CML | `https://198.18.1.2` | `admin / C1sco12345` |

> Secrets are never committed. Credentials for devices are supplied at run time via
> environment variables (see each lab's README).
