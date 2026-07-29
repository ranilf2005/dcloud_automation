# Ansible — FMC "inside → outside" access policy

Uses the [`cisco.fmcansible`](https://galaxy.ansible.com/ui/repo/published/cisco/fmcansible/)
collection to create two network objects and an Access Control Policy with an
ALLOW rule (inside → outside) through the FMC HTTP API.

## Files

| File | Purpose |
|------|---------|
| `create_access_policy.yml` | Playbook (objects → policy → rule) |
| `inventory.yml` | FMC management hosts |
| `group_vars/fmc.yml` | httpapi connection settings |
| `requirements.yml` | `cisco.fmcansible` collection |
| `ansible.cfg` | Ansible configuration |

## Safety

This ships **without** being run against a live FMC. The commands below that touch
the FMC are clearly marked; `--syntax-check` is offline.

## Usage

```bash
ansible-galaxy collection install -r requirements.yml

# Offline validation (no FMC contacted):
ansible-playbook create_access_policy.yml --syntax-check

# Against a live FMC (only when you intend to change it):
export FMC_PASSWORD='Cisco@123'
ansible-playbook create_access_policy.yml
```

## Notes

- Credentials: `ansible_user` is `admin`; the password is read from the
  `FMC_PASSWORD` environment variable (or use `ansible-vault`). Never commit secrets.
- Target FMC is set in `inventory.yml` (`fmc-760` = `198.18.1.10`; uncomment
  `fmc-100` = `198.18.1.11` for Pair B).
- `fmc_configuration` operation names (e.g. `createNetworkObject`,
  `createAccessPolicy`, `createAccessRule`) map to FMC REST API operations and may
  vary slightly by FMC/collection version.
