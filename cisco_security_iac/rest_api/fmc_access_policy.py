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
    ap.add_argument("--inside-cidr", default="198.18.1.0/24")
    ap.add_argument("--outside-cidr", default="198.18.2.0/24")
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
