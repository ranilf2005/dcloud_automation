---
title: Appendix — Credentials, Cheat-sheet & Troubleshooting
nav: Appendix
order: 5
eyebrow: Reference
description: Credentials, a copy-paste command cheat-sheet, and a troubleshooting table for both labs.
---

# Appendix

> Quick reference for both labs. See [Home](index.html) for lab access,
> [Lab 1](lab1-netdevops.html), and [Lab 2](lab2-security-iac.html).

## Appendix A — Credentials

| System | User | Password |
|--------|------|----------|
| code-server / GitLab / devbox / CML | see the [Home access table](index.html#lab-environment--access) | `C1sco12345` |
| Routers `csr1000v-0` / `iosv-1` | `admin` | `C1sco12345` |
| FMC & FTD | `admin` | `Cisco@123` |

> Secrets are **never** committed. Terraform reads `TF_VAR_fmc_password`, the REST
> script reads `FMC_PASSWORD`, and Ansible reads `FMC_PASSWORD` (or `ansible-vault`).

## Appendix B — Command cheat-sheet

```bash
# ---- Lab 1: NetDevOps ----
cd ~/automation_projects/clmel26_automation && source .venv/bin/activate
ansible-playbook ansible/playbooks/validate_vlans.yml        # offline intent check
pyats run job jobs/smoke_job.py --testbed-file testbed/testbed.yaml   # on devbox

# ---- Lab 2: Security IaC ----
cd ~/automation_projects/cisco_security_iac && source .venv/bin/activate
( cd terraform && terraform init && terraform validate )     # Terraform
python rest_api/fmc_access_policy.py --dry-run && ( cd rest_api && pytest )   # REST
( cd ansible && ansible-galaxy collection install -r requirements.yml \
  && ansible-playbook create_access_policy.yml --syntax-check )              # Ansible
```

## Appendix C — Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Pipeline fails at ping `192.168.1.1` | **Intentional** — interface on `iosv-0` is shut | `no shutdown` it (Lab 1.7) |
| `terraform init` can't download provider | No internet from host | Check proxy / registry reachability |
| pyATS SSH fails to a router | Legacy KEX/host-key | Already handled in `testbed.yaml` `ssh_options` |
| Ansible/REST auth error | Wrong `FMC_PASSWORD` | `export FMC_PASSWORD='Cisco@123'` |
| code-server hidden files showing | — | `files.exclude` hides dotfiles; reload the tab |
