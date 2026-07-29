# Cisco Secure Firewall (FMC / FTD) — Infrastructure as Code

Three parallel Infrastructure-as-Code scenarios that each create, on a Cisco
Secure Firewall Management Center (FMC), a **network object** and an **Access
Control Policy that allows traffic from inside to outside**:

| Scenario | Tooling | Folder |
|----------|---------|--------|
| Terraform | `CiscoDevNet/fmc` provider (v2.x, FMC 7.6) | [`terraform/`](terraform/) |
| REST API | Python + `requests` | [`rest_api/`](rest_api/) |
| Ansible | `cisco.fmcansible` collection | [`ansible/`](ansible/) |

> **Safety:** none of these are executed against the live FMC in this repository.
> Each scenario ships with an **offline validation** path (Terraform
> `init`/`validate`, REST `--dry-run` + `pytest`, Ansible `--syntax-check`) that
> contacts no device. The apply/run steps are documented but intentionally not run.

## Lab topology

```
inside (198.18.1.0/24)            outside (198.18.2.0/24)
        │                                  │
   FTD interface1  ───►  [ FTD ]  ───►  FTD interface4
                           ▲
                           │ managed by
                        [ FMC ]  (HTTPS / REST API 443)
```

### Addressing (as provided)

| Role | Pair A (v7.6) | Pair B |
|------|---------------|--------|
| FMC management | `198.18.1.10` | `198.18.1.11` |
| FTD management | `198.18.1.20` | `198.18.1.21` |
| FTD interface1 (inside) | `198.18.1.12` | `198.18.1.15` |
| FTD interface4 (outside) | `198.18.2.12` | `198.18.2.13` |

Credentials (FMC + FTD): user `admin`. The password is supplied out-of-band via
environment variable and is **never** committed (see each scenario's README).

## Quick start (offline validation)

```bash
# Terraform
cd terraform && terraform init && terraform validate

# REST API
cd rest_api && pip install -r requirements.txt && python fmc_access_policy.py --dry-run && pytest

# Ansible
cd ansible && ansible-galaxy collection install -r requirements.yml && ansible-playbook create_access_policy.yml --syntax-check
```

## What gets created (all three scenarios)

1. Network object `inside-net` = `198.18.1.0/24`
2. Network object `outside-net` = `198.18.2.0/24`
3. Access Control Policy `inside-to-outside-policy` (default action `BLOCK`)
4. Rule `allow-inside-to-outside` — action `ALLOW`, source `inside-net`,
   destination `outside-net`.

## Security

- No plaintext secrets are committed. Passwords come from env vars
  (`TF_VAR_fmc_password`, `FMC_PASSWORD`) or `ansible-vault`.
- `terraform.tfvars`, `*.tfstate`, `config.env`, `.venv/`, and provider caches are
  gitignored (see [`.gitignore`](.gitignore)).
