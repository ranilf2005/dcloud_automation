---
title: Appendix — Lab 2 project files
nav: Lab 2 · Files
order: 7
eyebrow: Reference
description: Every Lab 2 (Security IaC) project file in full — Terraform, REST API, and Ansible — with a copy button.
---

# Appendix — Lab 2 project files

> **Reference dump of the Security IaC project (`cisco_security_iac/`).** Every file for
> the [Lab 2](lab2-security-iac.html) Terraform, REST API, and Ansible scenarios is shown
> below in full. Hover a code block and click **Copy** to copy it. These pages are
> generated from the real source files, so they always match what you run in the lab.

## Project root

### `.gitignore`

````text
# ---- Terraform ----
**/.terraform/*
*.tfstate
*.tfstate.*
crash.log
crash.*.log
*.tfvars
*.tfvars.json
!*.tfvars.example
override.tf
override.tf.json
*_override.tf
*_override.tf.json
.terraform.lock.hcl

# ---- Python ----
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/

# ---- Secrets / local env ----
config.env
*.vault
.vault_pass
.env

# ---- Ansible ----
ansible/collections/
*.retry

# ---- Editor / OS ----
.DS_Store
````


## ansible/

### `ansible/ansible.cfg`

Ansible configuration for the playbooks.

````ini
[defaults]
inventory            = inventory.yml
host_key_checking    = False
retry_files_enabled  = False
collections_path     = collections:~/.ansible/collections
stdout_callback      = default
interpreter_python   = auto_silent
gathering            = explicit

[persistent_connection]
command_timeout = 60
connect_timeout = 60
````

### `ansible/create_access_policy.yml`

Playbook: create the objects → policy → rule via the FMC REST API.

````yaml
---
# Create two network objects and an Access Control Policy whose ALLOW rule
# permits traffic from inside to outside, via the FMC HTTP API.
#
# Uses the generic cisco.fmcansible.fmc_configuration module: each task calls an
# FMC REST operation by name and can store its result with `register_as` for
# reuse in later tasks.
- name: "FMC — allow inside to outside"
  hosts: fmc
  connection: httpapi
  gather_facts: false
  vars:
    inside_cidr: "198.18.2.0/24"
    outside_cidr: "198.18.1.0/24"
    acp_name: "inside-to-outside-policy"

  tasks:
    - name: Create the inside network object
      cisco.fmcansible.fmc_configuration:
        operation: createNetworkObject
        data:
          name: inside-net
          value: "{{ inside_cidr }}"
          type: Network
        register_as: inside_net

    - name: Create the outside network object
      cisco.fmcansible.fmc_configuration:
        operation: createNetworkObject
        data:
          name: outside-net
          value: "{{ outside_cidr }}"
          type: Network
        register_as: outside_net

    - name: Create the access control policy (default action BLOCK)
      cisco.fmcansible.fmc_configuration:
        operation: createAccessPolicy
        data:
          name: "{{ acp_name }}"
          type: AccessPolicy
          defaultAction:
            action: BLOCK
            type: AccessPolicyDefaultAction
        register_as: access_policy

    - name: Create the ALLOW rule (inside -> outside)
      cisco.fmcansible.fmc_configuration:
        operation: createAccessRule
        path_params:
          containerUUID: "{{ access_policy.id }}"
        data:
          name: allow-inside-to-outside
          type: AccessRule
          action: ALLOW
          enabled: true
          sourceNetworks:
            objects:
              - "{{ inside_net }}"
          destinationNetworks:
            objects:
              - "{{ outside_net }}"
        register_as: allow_rule

    - name: Show the created policy
      ansible.builtin.debug:
        msg: "Created ACP '{{ acp_name }}' with an ALLOW rule inside -> outside."
````

### `ansible/inventory.yml`

FMC management hosts.

````yaml
---
# FMC management hosts. Pair A is the default target; Pair B is commented out.
all:
  children:
    fmc:
      hosts:
        fmc-760:
          ansible_host: 198.18.1.10
        # fmc-100:
        #   ansible_host: 198.18.1.11
````

### `ansible/requirements.yml`

Ansible collections (cisco.ios, ansible.netcommon).

````yaml
---
# Install with: ansible-galaxy collection install -r requirements.yml
collections:
  - name: cisco.fmcansible
````


## rest_api/

### `rest_api/config.env.example`

Example environment variables — copy to config.env.

````ini
# Copy to config.env and `source` it (config.env is gitignored).
#   Pair A (FMC 7.6): 198.18.1.10        Pair B: 198.18.1.11
export FMC_HOST=198.18.1.10
export FMC_USERNAME=admin
export FMC_PASSWORD=Cisco@123
````

### `rest_api/fmc_access_policy.py`

Python client: token auth → objects → policy → rule (defaults to a safe dry-run).

````python
#!/usr/bin/env python3
"""
fmc_access_policy.py — create an FMC network object + Access Control Policy that
allows traffic from inside to outside, using the FMC REST API.

SAFETY: this script defaults to --dry-run. In dry-run it prints the exact
sequence of REST calls and JSON payloads and does NOT contact any FMC.
Pass --apply to actually send the requests to a live FMC.

REST flow (FMC 7.x):
  1. POST /api/fmc_platform/v1/auth/generatetoken   (HTTP Basic) -> X-auth-access-token + DOMAIN_UUID
  2. POST /api/fmc_config/v1/domain/{domain}/object/networks         (inside + outside)
  3. POST /api/fmc_config/v1/domain/{domain}/policy/accesspolicies   (BLOCK default)
  4. POST /api/fmc_config/v1/domain/{domain}/policy/accesspolicies/{id}/accessrules  (ALLOW)
"""
import argparse
import json
import os
import sys

PLATFORM_AUTH = "/api/fmc_platform/v1/auth/generatetoken"
CONFIG_BASE = "/api/fmc_config/v1/domain/{domain}"


# --------------------------------------------------------------------------
# Pure payload builders (unit-tested in tests/test_payloads.py, no network).
# --------------------------------------------------------------------------
def build_network_payload(name, cidr, description=""):
    """Network object for a subnet in CIDR form."""
    return {"name": name, "type": "Network", "value": cidr, "description": description}


def build_access_policy_payload(name, default_action="BLOCK"):
    """Access Control Policy with the given default action."""
    return {"type": "AccessPolicy", "name": name, "defaultAction": {"action": default_action}}


def build_access_rule_payload(name, source_obj, destination_obj, action="ALLOW"):
    """Access rule allowing traffic from source to destination network objects."""
    return {
        "type": "AccessRule",
        "name": name,
        "action": action,
        "enabled": True,
        "sourceNetworks": {"objects": [source_obj]},
        "destinationNetworks": {"objects": [destination_obj]},
    }


# --------------------------------------------------------------------------
# Thin REST client (only imported/used when --apply is given).
# --------------------------------------------------------------------------
class FmcClient:
    def __init__(self, host, username, password, verify=False, timeout=30):
        import requests  # imported lazily so dry-run needs no dependency

        self._requests = requests
        self.base = f"https://{host}"
        self.username = username
        self.password = password
        self.verify = verify
        self.timeout = timeout
        self.token = None
        self.domain = None
        self.session = requests.Session()
        if not verify:
            from urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def login(self):
        r = self.session.post(
            self.base + PLATFORM_AUTH,
            auth=self._requests.auth.HTTPBasicAuth(self.username, self.password),
            verify=self.verify,
            timeout=self.timeout,
        )
        r.raise_for_status()
        self.token = r.headers["X-auth-access-token"]
        self.domain = r.headers.get("DOMAIN_UUID")
        return self.token

    def _headers(self):
        return {"X-auth-access-token": self.token, "Content-Type": "application/json"}

    def create(self, path, payload):
        url = self.base + CONFIG_BASE.format(domain=self.domain) + path
        r = self.session.post(
            url, headers=self._headers(), data=json.dumps(payload), verify=self.verify, timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=os.getenv("FMC_HOST", "198.18.1.10"))
    ap.add_argument("--username", default=os.getenv("FMC_USERNAME", "admin"))
    ap.add_argument("--password", default=os.getenv("FMC_PASSWORD"))
    ap.add_argument("--inside-cidr", default="198.18.2.0/24")
    ap.add_argument("--outside-cidr", default="198.18.1.0/24")
    ap.add_argument("--policy-name", default="inside-to-outside-policy")
    ap.add_argument("--verify-tls", action="store_true", help="Verify the FMC TLS certificate.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the REST calls and payloads without contacting the FMC (this is the default).",
    )
    ap.add_argument("--apply", action="store_true", help="Actually send requests to the FMC (default: dry-run).")
    return ap.parse_args(argv)


def dry_run(args):
    inside = build_network_payload("inside-net", args.inside_cidr, "Inside subnet (IaC demo)")
    outside = build_network_payload("outside-net", args.outside_cidr, "Outside subnet (IaC demo)")
    policy = build_access_policy_payload(args.policy_name)
    rule = build_access_rule_payload(
        "allow-inside-to-outside",
        {"type": "Network", "name": "inside-net", "id": "<INSIDE_ID>"},
        {"type": "Network", "name": "outside-net", "id": "<OUTSIDE_ID>"},
    )
    dom = CONFIG_BASE.format(domain="<DOMAIN_UUID>")
    print("=== DRY RUN — no FMC is contacted. Re-run with --apply to execute. ===\n")
    print(f"[1] POST https://{args.host}{PLATFORM_AUTH}")
    print(f"        Authorization: Basic ({args.username}:******)\n")
    print(f"[2] POST https://{args.host}{dom}/object/networks")
    print("        " + json.dumps(inside))
    print("        " + json.dumps(outside) + "\n")
    print(f"[3] POST https://{args.host}{dom}/policy/accesspolicies")
    print("        " + json.dumps(policy) + "\n")
    print(f"[4] POST https://{args.host}{dom}/policy/accesspolicies/<POLICY_ID>/accessrules")
    print("        " + json.dumps(rule))


def apply(args):
    if not args.password:
        print("ERROR: set --password or the FMC_PASSWORD env var to use --apply.", file=sys.stderr)
        return 2
    client = FmcClient(args.host, args.username, args.password, verify=args.verify_tls)
    client.login()
    src = client.create("/object/networks", build_network_payload("inside-net", args.inside_cidr, "Inside subnet (IaC demo)"))
    dst = client.create("/object/networks", build_network_payload("outside-net", args.outside_cidr, "Outside subnet (IaC demo)"))
    pol = client.create("/policy/accesspolicies", build_access_policy_payload(args.policy_name))
    rule = build_access_rule_payload(
        "allow-inside-to-outside",
        {"type": "Network", "name": src["name"], "id": src["id"]},
        {"type": "Network", "name": dst["name"], "id": dst["id"]},
    )
    client.create(f"/policy/accesspolicies/{pol['id']}/accessrules", rule)
    print(f"Created objects + policy '{pol['name']}' ({pol['id']}) with allow rule.")
    return 0


def main(argv=None):
    args = parse_args(argv)
    if args.apply:
        return apply(args)
    dry_run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

### `rest_api/pytest.ini`

pytest configuration.

````ini
[pytest]
pythonpath = .
testpaths = tests
````

### `rest_api/requirements.txt`

Python dependencies (requests, PyYAML, pytest).

````text
requests>=2.31
PyYAML>=6.0
pytest>=8.0
````


## terraform/

### `terraform/access_policy.tf`

The access control policy plus the inline ALLOW rule.

````hcl
# Access Control Policy with a single rule that ALLOWS traffic from the
# inside zone/network to the outside zone/network.
#
# Rules are managed inline (manage_rules = true) per the CiscoDevNet/fmc
# v2.x provider model.
resource "fmc_access_control_policy" "inside_to_outside" {
  name           = var.acp_name
  description    = "Allow traffic from inside to outside (IaC demo)"
  default_action = "BLOCK"

  default_action_log_connection_end = true
  default_action_send_events_to_fmc = true

  manage_rules = true
  rules = [
    {
      name    = "allow-inside-to-outside"
      action  = "ALLOW"
      enabled = true

      source_zones = [
        { id = fmc_security_zone.inside.id }
      ]
      destination_zones = [
        { id = fmc_security_zone.outside.id }
      ]

      source_network_objects = [
        { id = fmc_network.inside_net.id, type = "Network" }
      ]
      destination_network_objects = [
        { id = fmc_network.outside_net.id, type = "Network" }
      ]

      log_connection_end = true
      send_events_to_fmc = true
    }
  ]
}
````

### `terraform/objects.tf`

Two fmc_network objects (inside/outside subnets).

````hcl
# Network objects representing the inside and outside subnets.
resource "fmc_network" "inside_net" {
  name        = "inside-net"
  description = "Inside subnet (IaC demo)"
  prefix      = var.inside_network_cidr
}

resource "fmc_network" "outside_net" {
  name        = "outside-net"
  description = "Outside subnet (IaC demo)"
  prefix      = var.outside_network_cidr
}
````

### `terraform/outputs.tf`

Prints the created object / policy IDs.

````hcl
output "inside_network_object_id" {
  description = "ID of the inside network object."
  value       = fmc_network.inside_net.id
}

output "outside_network_object_id" {
  description = "ID of the outside network object."
  value       = fmc_network.outside_net.id
}

output "access_control_policy_id" {
  description = "ID of the created Access Control Policy."
  value       = fmc_access_control_policy.inside_to_outside.id
}
````

### `terraform/providers.tf`

FMC connection settings (url, username, password, insecure).

````hcl
# Cisco Secure Firewall Management Center (FMC) provider.
#
# Credentials may be supplied either through the variables below (see
# variables.tf / terraform.tfvars) OR via the provider's environment
# variables: FMC_URL, FMC_USERNAME, FMC_PASSWORD, FMC_INSECURE.
#
# NEVER commit real passwords. Prefer:  export TF_VAR_fmc_password='...'
provider "fmc" {
  url      = var.fmc_url
  username = var.fmc_username
  password = var.fmc_password
  insecure = var.fmc_insecure
}
````

### `terraform/terraform.tfvars.example`

Example variable values — copy to terraform.tfvars.

````hcl
# Copy to terraform.tfvars and adjust for your target FMC.
# DO NOT commit real secrets — terraform.tfvars is gitignored.
#
#   Pair A (FMC 7.6): https://198.18.1.10   (FTD mgmt 198.18.1.20)
#   Pair B          : https://198.18.1.11   (FTD mgmt 198.18.1.21)

fmc_url      = "https://198.18.1.10"
fmc_username = "admin"
fmc_insecure = true

# Prefer setting the password out-of-band instead of here:
#   export TF_VAR_fmc_password='Cisco@123'
# fmc_password = "Cisco@123"

inside_network_cidr  = "198.18.2.0/24"
outside_network_cidr = "198.18.1.0/24"
acp_name             = "inside-to-outside-policy"
````

### `terraform/variables.tf`

Inputs: FMC URL, credentials, inside/outside CIDRs, policy name.

````hcl
variable "fmc_url" {
  description = "Base URL of the FMC instance, e.g. https://198.18.1.10 (Pair A) or https://198.18.1.11 (Pair B)."
  type        = string
  default     = "https://198.18.1.10"
}

variable "fmc_username" {
  description = "FMC administrative username."
  type        = string
  default     = "admin"
}

variable "fmc_password" {
  description = "FMC administrative password. Set via TF_VAR_fmc_password or FMC_PASSWORD; do not commit."
  type        = string
  sensitive   = true
}

variable "fmc_insecure" {
  description = "Skip TLS certificate verification (lab FMC uses a self-signed certificate)."
  type        = bool
  default     = true
}

variable "inside_network_cidr" {
  description = "Inside subnet in CIDR notation (dCloud FTD interface4 / inside side)."
  type        = string
  default     = "198.18.2.0/24"
}

variable "outside_network_cidr" {
  description = "Outside subnet in CIDR notation (dCloud FTD interface1 / outside side)."
  type        = string
  default     = "198.18.1.0/24"
}

variable "acp_name" {
  description = "Name of the Access Control Policy to create."
  type        = string
  default     = "inside-to-outside-policy"
}
````

### `terraform/versions.tf`

Terraform and provider version constraints.

````hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    fmc = {
      source  = "CiscoDevNet/fmc"
      version = "~> 2.5"
    }
  }
}
````

### `terraform/zones.tf`

Two fmc_security_zone objects (inside/outside).

````hcl
# Security zones for the inside and outside interfaces.
resource "fmc_security_zone" "inside" {
  name           = "inside-zone"
  interface_type = "ROUTED"
}

resource "fmc_security_zone" "outside" {
  name           = "outside-zone"
  interface_type = "ROUTED"
}
````


## ansible/

### `ansible/group_vars/fmc.yml`

httpapi connection settings for the FMC.

````yaml
---
# Connection settings for the Cisco FMC HTTP API (cisco.fmcansible).
ansible_network_os: cisco.fmcansible.fmc
ansible_connection: httpapi
ansible_httpapi_use_ssl: true
ansible_httpapi_validate_certs: false
ansible_httpapi_port: 443
ansible_user: admin

# Provide the password out-of-band; never commit it.
#   export FMC_PASSWORD='Cisco@123'
# Alternatively store it with ansible-vault and reference it here.
ansible_password: "{{ lookup('ansible.builtin.env', 'FMC_PASSWORD') }}"
````


## rest_api/

### `rest_api/tests/test_payloads.py`

Offline unit tests for the JSON payload builders.

````python
"""Offline unit tests for the FMC REST payload builders (no FMC contacted)."""
from fmc_access_policy import (
    build_access_policy_payload,
    build_access_rule_payload,
    build_network_payload,
)


def test_network_payload():
    p = build_network_payload("inside-net", "198.18.2.0/24", "d")
    assert p["type"] == "Network"
    assert p["value"] == "198.18.2.0/24"
    assert p["name"] == "inside-net"
    assert p["description"] == "d"


def test_access_policy_payload_defaults_to_block():
    p = build_access_policy_payload("inside-to-outside-policy")
    assert p["type"] == "AccessPolicy"
    assert p["name"] == "inside-to-outside-policy"
    assert p["defaultAction"]["action"] == "BLOCK"


def test_access_rule_allows_inside_to_outside():
    src = {"type": "Network", "name": "inside-net", "id": "1"}
    dst = {"type": "Network", "name": "outside-net", "id": "2"}
    r = build_access_rule_payload("allow-inside-to-outside", src, dst)
    assert r["type"] == "AccessRule"
    assert r["action"] == "ALLOW"
    assert r["enabled"] is True
    assert r["sourceNetworks"]["objects"][0]["id"] == "1"
    assert r["destinationNetworks"]["objects"][0]["id"] == "2"
````

