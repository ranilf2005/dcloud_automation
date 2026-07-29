# Terraform — FMC "inside → outside" access policy

Creates, on a Cisco Secure Firewall Management Center (FMC), using the
[`CiscoDevNet/fmc`](https://registry.terraform.io/providers/CiscoDevNet/fmc/latest) provider (v2.x, tested against FMC 7.6):

- two **network objects** (`inside-net` = `198.18.2.0/24`, `outside-net` = `198.18.1.0/24`)
- two **security zones** (`inside-zone`, `outside-zone`)
- an **Access Control Policy** (`inside-to-outside-policy`) whose default action is
  `BLOCK`, containing one rule that **ALLOWs** traffic from the inside zone/network
  to the outside zone/network.

## Files

| File | Purpose |
|------|---------|
| `versions.tf` | Terraform + provider version constraints |
| `providers.tf` | FMC provider configuration |
| `variables.tf` | Input variables |
| `objects.tf` | `fmc_network` objects |
| `zones.tf` | `fmc_security_zone` objects |
| `access_policy.tf` | `fmc_access_control_policy` + allow rule |
| `outputs.tf` | Object / policy IDs |
| `terraform.tfvars.example` | Sample variable values |

## Prerequisites

- Terraform >= 1.0
- Network reachability to the FMC management IP (e.g. `198.18.1.10`)

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars     # edit as needed
export TF_VAR_fmc_password='Cisco@123'           # keep the secret out of files

terraform init          # downloads the CiscoDevNet/fmc provider (no FMC contact)
terraform fmt -check
terraform validate      # schema validation (no FMC contact)

# The following DO contact the FMC — run only when you intend to change it:
terraform plan
terraform apply
```

> Safety: `init`, `fmt` and `validate` are **offline** and never talk to the FMC.
> `plan`/`apply` connect to the FMC — this repo ships without running them.

## Credentials

Never commit secrets. Provide the password with `TF_VAR_fmc_password` (or
`FMC_PASSWORD`). `terraform.tfvars`, `*.tfstate`, and `.terraform/` are gitignored.
