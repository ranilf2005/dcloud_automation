# REST API — FMC "inside → outside" access policy

A self-contained Python client for the **FMC REST API** that creates two network
objects and an Access Control Policy with an ALLOW rule (inside → outside).

## Files

| File | Purpose |
|------|---------|
| `fmc_access_policy.py` | CLI script (token auth → objects → policy → rule) |
| `tests/test_payloads.py` | Offline unit tests for the JSON payload builders |
| `requirements.txt` | `requests`, `PyYAML`, `pytest` |
| `config.env.example` | Sample connection settings |
| `pytest.ini` | pytest config (adds project dir to `pythonpath`) |

## Safety

The script **defaults to `--dry-run`**: it prints the exact REST calls and JSON
payloads and contacts **no FMC**. Add `--apply` to run it against a live FMC.

## Usage

```bash
pip install -r requirements.txt

# 1) Dry run — prints the 4 REST calls + payloads, no FMC contacted:
python fmc_access_policy.py --dry-run           # (dry-run is the default)

# 2) Offline unit tests (no FMC):
pytest

# 3) Against a live FMC (only when you intend to change it):
cp config.env.example config.env && $EDITOR config.env
source config.env
python fmc_access_policy.py --apply
```

## REST flow

1. `POST /api/fmc_platform/v1/auth/generatetoken` (HTTP Basic) → `X-auth-access-token`, `DOMAIN_UUID`
2. `POST /api/fmc_config/v1/domain/{domain}/object/networks` — inside + outside subnets
3. `POST /api/fmc_config/v1/domain/{domain}/policy/accesspolicies` — default action `BLOCK`
4. `POST .../policy/accesspolicies/{id}/accessrules` — `ALLOW` inside → outside

Credentials come from `FMC_HOST` / `FMC_USERNAME` / `FMC_PASSWORD` (or CLI flags).
`config.env` is gitignored — never commit real secrets.
