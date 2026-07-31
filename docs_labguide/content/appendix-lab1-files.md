---
title: Appendix — Lab 1 project files
nav: Project files
group: Lab 1 · NetDevOps
order: 6
eyebrow: Lab 1 · Reference
description: Every Lab 1 (NetDevOps) project file in full — syntax-highlighted, with a copy button.
---

# Appendix — Lab 1 project files

> **Reference dump of the NetDevOps project (`clmel26_automation/`).** Every file the
> [Lab 1 walkthrough](lab1-hands-on.html) uses is shown below in full. Hover a code
> block and click **Copy** to copy it. These pages are generated from the real source
> files, so they always match what you run in the lab.

## Project root

<details class="file">
<summary><code>.gitignore</code></summary>

````text
# pyATS / Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# pyATS run artifacts
logs/
*.log
archive/
runinfo/
*.tar.gz

# Editor / OS
.vscode/
.idea/
.DS_Store
````

</details>

<details class="file">
<summary><code>.gitlab-ci.yml</code> <span class="file-desc">— The pipeline definition: three stages — validate → network_check → deploy.</span></summary>

````yaml
# =====================================================================
#  Ansible VLAN CI/CD  -  lab GitLab pipeline (runs on 198.18.1.4)
#  Mirrors the GitHub Actions design so attendees hit the same gate:
#    validate -> Test/Dev : lint + schema asserts (NO device needed)
#    deploy   -> Prod     : manual gate, applies VLANs to routers .6/.7
#  Runs on the pyats-fast runner (docker executor) using the local
#  registry pyATS image; ansible-core is pip-installed when jobs start.
# =====================================================================
stages:
  - validate
  - network_check
  - deploy

default:
  tags: ["pyats-fast"]                                 # your live fast runner
  image: "198.18.1.4:5050/root/pyatscml/pyats:1.0.0"   # local registry image

variables:
  ANSIBLE_FORCE_COLOR: "1"
  PIP_DISABLE_PIP_VERSION_CHECK: "1"

# -------- Stage 1: Test/Dev - validate intent (no device touched) --------
validate_intent:
  stage: validate
  before_script:
    - python -m pip install --quiet --upgrade "ansible-core>=2.16" ansible-lint yamllint
    - export PATH="$HOME/.local/bin:$PATH"   # image user is 'ci'; pip puts scripts here
    - cd ansible
    - ansible-galaxy collection install -r requirements.yml
  script:
    - echo "== Lint YAML =="
    - yamllint .
    - echo "== Lint playbooks =="
    - ansible-lint playbooks/
    - echo "== Syntax check =="
    - ansible-playbook playbooks/configure_vlans.yml --syntax-check
    - echo "== Validate VLAN and interface intent =="
    - ansible-playbook playbooks/validate_vlans.yml

# -------- Stage 2: Production - only if validate passed (manual gate) --------
deploy_prod:
  stage: deploy
  needs: ["validate_intent"]      # blocked until validate_intent passes (the gate)
  when: manual                    # production gate: a human clicks Deploy in the UI
  before_script:
    - python -m pip install --quiet --upgrade "ansible-core>=2.16"
    - export PATH="$HOME/.local/bin:$PATH"   # image user is 'ci'; pip puts scripts here
    - cd ansible
    - ansible-galaxy collection install -r requirements.yml
  script:
    - echo "== Pre-flight dry run (no changes) =="
    - ansible-playbook -i inventory/hosts.yml playbooks/configure_vlans.yml -e target=prod --check --diff
    - echo "== Deploy VLANs to production routers .6/.7 =="
    - ansible-playbook -i inventory/hosts.yml playbooks/configure_vlans.yml -e target=prod

# -------- Network check: both routers ping a target, then (if OK) create Loopback3 --------
# Runs on the pyATS runner image (has pyats/genie/unicon). Talks to the routers.
#   ping fails  -> job exits 1 -> pipeline FAILS with a clear reason (nothing configured)
#   ping passes -> creates Loopback3 (3.3.3.1 / 3.3.3.2), skipping any duplicate
ping_and_loopback:
  stage: network_check
  needs: []                       # independent of the VLAN validate job
  script:
    - echo "== Step 1: both routers ping 192.168.1.1 =="
    - echo "== Step 2: if ping OK, create duplicate-checked Loopback3 from configs/loopback3.yaml =="
    - python jobs/ping_and_loopback.py --testbed testbed/testbed.yaml --config configs/loopback3.yaml
````

</details>

<details class="file">
<summary><code>requirements.txt</code> <span class="file-desc">— Python dependencies (pyATS, Genie, PyYAML).</span></summary>

````text
# Cisco test/automation frameworks used by the pipeline jobs
pyats[full]
genie
PyYAML
````

</details>


## ansible/

<details class="file">
<summary><code>ansible/.ansible-lint</code></summary>

````yaml
---
# Keep the demo focused: fail on real errors, not style opinions.
profile: min
exclude_paths:
  - collections/
````

</details>

<details class="file">
<summary><code>ansible/.yamllint</code></summary>

````yaml
---
extends: default
rules:
  line-length:
    max: 160
    level: warning
  comments:
    min-spaces-from-content: 1
  comments-indentation: disable
  truthy:
    allowed-values: ["true", "false"]
    check-keys: false
ignore: |
  collections/
````

</details>

<details class="file">
<summary><code>ansible/ansible.cfg</code> <span class="file-desc">— Ansible configuration for the playbooks.</span></summary>

````ini
# Ansible configuration for the CLMEL26 VLAN CI/CD task.
[defaults]
inventory            = inventory/hosts.yml
collections_path     = collections:~/.ansible/collections
host_key_checking    = False
retry_files_enabled  = False
stdout_callback      = default
interpreter_python   = auto_silent
gathering            = explicit
deprecation_warnings = False

[persistent_connection]
command_timeout = 60
connect_timeout = 60
````

</details>

<details class="file">
<summary><code>ansible/requirements.yml</code> <span class="file-desc">— Ansible collections (cisco.ios, ansible.netcommon).</span></summary>

````yaml
---
# Install with: ansible-galaxy collection install -r requirements.yml
collections:
  - name: cisco.ios
    version: ">=5.0.0"
  - name: ansible.netcommon
    version: ">=5.0.0"
````

</details>


## configs/

<details class="file">
<summary><code>configs/loopback3.yaml</code> <span class="file-desc">— Declarative Loopback3 addresses and the ping target.</span></summary>

````yaml
# =====================================================================
#  Loopback3 definition - consumed by jobs/ping_and_loopback.py
#
#  The job runs in two steps:
#    1. Every router must first PING `ping_target`.
#    2. Only if all pings pass, it creates each Loopback3 below - but it
#       checks for a DUPLICATE first (an existing Loopback3, or the IP
#       already in use on another interface) and skips if found.
#  If the ping fails, the CI/CD pipeline fails and NOTHING is configured.
# =====================================================================
ping_target: 192.168.1.1            # both routers must reach this first

devices:
  csr1000v-0:                       # 198.18.1.6 (IOS-XE)
    - name: Loopback3
      ip: 3.3.3.1
      mask: 255.255.255.255

  iosv-1:                           # 198.18.1.7 (IOS)
    - name: Loopback3
      ip: 3.3.3.2
      mask: 255.255.255.255
````

</details>

<details class="file">
<summary><code>configs/loopbacks.yaml</code> <span class="file-desc">— Declarative Loopback300 definition.</span></summary>

````yaml
devices:
  iosv-1:
    - name: Loopback300
      ip: 2.2.2.2
      mask: 255.255.255.255

  csr1000v-0:
    - name: Loopback300
      ip: 2.2.2.2
      mask: 255.255.255.255
````

</details>


## jobs/

<details class="file">
<summary><code>jobs/configure_loopback.py</code> <span class="file-desc">— Applies Loopback300 to the routers once the tests pass.</span></summary>

````python
import sys
import yaml
import argparse
from genie.testbed import load as load_testbed


def has_ip(dev, iface, ip):
    out = dev.execute("show ip interface brief")
    # Lines often look like: Loopback300     2.2.2.2     YES ...
    return (iface in out) and (ip in out)


def save_config(dev):
    try:
        dev.execute("write memory")
    except Exception:
        try:
            dev.execute("copy running-config startup-config\n\n")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testbed", required=True)
    parser.add_argument("--config", required=True)  # configs/loopbacks.yaml
    args = parser.parse_args()

    tb = load_testbed(args.testbed)
    with open(args.config) as f:
        payload = yaml.safe_load(f)

    overall_ok = True

    for dev_name, interfaces in payload.get("devices", {}).items():
        if dev_name not in tb.devices:
            print(f"[WARN] Skipping {dev_name}: not found in testbed")
            overall_ok = False
            continue

        dev = tb.devices[dev_name]
        print(f"\n=== Connecting to {dev_name} ===")
        dev.connect(log_stdout=False)

        for iface in interfaces:
            name = iface["name"]
            ip = iface["ip"]
            mask = iface["mask"]

            if has_ip(dev, name, ip):
                print(f"[OK] {dev_name}: {name} already has {ip} - skipping")
                continue

            cfg = [
                f"interface {name}",
                f" ip address {ip} {mask}",
                "exit"
            ]
            print(f"[CFG] {dev_name}: configuring {name} {ip} {mask}")
            dev.configure("\n".join(cfg))

            save_config(dev)

            # Verify
            if has_ip(dev, name, ip):
                print(f"[OK] {dev_name}: verified {name} has {ip}")
            else:
                print(f"[ERROR] {dev_name}: verification failed for {name} {ip}")
                overall_ok = False

        try:
            dev.disconnect()
        except Exception:
            pass

    if not overall_ok:
        print("\nOne or more devices failed verification. Exiting 1.")
        sys.exit(1)


if __name__ == "__main__":
    main()
````

</details>

<details class="file">
<summary><code>jobs/ping_and_loopback.py</code> <span class="file-desc">— Ping gate — pings the target and, only if all pass, creates Loopback3.</span></summary>

````python
#!/usr/bin/env python3
"""
ping_and_loopback.py  -  CLMEL26 lab job

Flow (any problem fails the CI/CD pipeline with a clear message):

  STEP 1  Both routers (csr1000v-0 198.18.1.6, iosv-1 198.18.1.7) ping a
          target IP. Ping is read-only and changes nothing.
  STEP 2  ONLY if every router reached the target, read the loopback config
          file and create each Loopback3 - but for every router it first
          checks for a DUPLICATE (an existing Loopback3, or the IP already in
          use on another interface) and skips creation if one is found.
  FAIL    If ANY router fails the ping, print a clear error and exit 1 so the
          pipeline stops BEFORE touching any device configuration.

Usage:
  python jobs/ping_and_loopback.py \
      --testbed testbed/testbed.yaml \
      --config  configs/loopback3.yaml \
      [--target 198.168.1.1] [--dry-run]
"""
import re
import sys
import argparse

import yaml
from genie.testbed import load as load_testbed

DEFAULT_TARGET = "198.168.1.1"
MIN_SUCCESS = 80            # a router "passes" if ping success rate >= this (%)


def banner(title):
    line = "=" * 70
    print(f"\n{line}\n{title}\n{line}")


def ping(dev, target):
    """Ping the target from dev. Read-only. Returns (ok, rate, last_line)."""
    out = dev.execute(f"ping {target} repeat 5 timeout 2")
    m = re.search(r"Success +rate +is +(\d+) +percent", out, re.I)
    rate = int(m.group(1)) if m else 0
    last = out.strip().splitlines()[-1] if out.strip() else "(no output)"
    return rate >= MIN_SUCCESS, rate, last


def find_interface(dev, name, ip):
    """
    Inspect 'show ip interface brief' and report duplicates.
    Returns (iface_exists, ip_owner) where ip_owner is the interface that
    already carries `ip` (or None).
    """
    out = dev.execute("show ip interface brief")
    iface_exists = re.search(rf"^{re.escape(name)}\b", out, re.M) is not None
    owner = re.search(rf"^(\S+)\s+{re.escape(ip)}\b", out, re.M)
    return iface_exists, (owner.group(1) if owner else None)


def save_config(dev):
    try:
        dev.execute("write memory")
    except Exception:
        try:
            dev.execute("copy running-config startup-config\n\n")
        except Exception:
            pass


def disconnect_all(tb):
    for dev in tb.devices.values():
        try:
            dev.disconnect()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Ping pre-check, then create Loopback3 only if there is no duplicate."
    )
    parser.add_argument("--testbed", required=True)
    parser.add_argument("--config", required=True,
                        help="loopback config file, e.g. configs/loopback3.yaml")
    parser.add_argument("--target", help="override the ping target IP")
    parser.add_argument("--dry-run", action="store_true",
                        help="ping and report only; never change device config")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f) or {}
    target = args.target or cfg.get("ping_target") or DEFAULT_TARGET
    plan = cfg.get("devices", {})

    tb = load_testbed(args.testbed)

    # ---------------- STEP 1: ping pre-check on EVERY router ----------------
    banner(f"STEP 1  Ping pre-check  ->  every router must reach {target}")
    ping_failures = []
    for name, dev in tb.devices.items():
        try:
            dev.connect(log_stdout=False)
        except Exception as exc:
            print(f"  [FAIL] {name}: could not connect - {exc}")
            ping_failures.append(f"{name}: SSH connection failed ({exc})")
            continue
        ok, rate, last = ping(dev, target)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} -> {target}: "
              f"success rate {rate}%   ({last})")
        if not ok:
            ping_failures.append(
                f"{name} could NOT reach {target} - success rate {rate}% "
                f"(need >= {MIN_SUCCESS}%)"
            )

    if ping_failures:
        banner("PIPELINE FAILED  -  ping pre-check did not pass")
        print(f"One or more routers cannot reach {target}, so Loopback3 was")
        print("NOT created on ANY device. Fix reachability and re-run the pipeline.\n")
        for item in ping_failures:
            print(f"  - {item}")
        print()
        disconnect_all(tb)
        sys.exit(1)

    print(f"\n  OK: every router reached {target}. Proceeding to Loopback3.")

    # ------------- STEP 2: create Loopback3 (duplicate-checked) -------------
    banner("STEP 2  Create Loopback3 on each router (skip if duplicate)")
    errors = []
    for name, loopbacks in plan.items():
        if name not in tb.devices:
            print(f"  [WARN] {name} is in the config but not in the testbed - skipping")
            continue
        dev = tb.devices[name]
        for lb in loopbacks:
            iface = lb["name"]
            ip = lb["ip"]
            mask = lb.get("mask", "255.255.255.255")

            exists, ip_owner = find_interface(dev, iface, ip)

            # ---- duplicate checks BEFORE creating anything ----
            if exists:
                print(f"  [SKIP] {name}: {iface} already exists (duplicate) - not re-creating")
                continue
            if ip_owner and ip_owner != iface:
                print(f"  [SKIP] {name}: {ip} already used by {ip_owner} (duplicate IP) - "
                      f"not creating {iface}")
                continue

            if args.dry_run:
                print(f"  [DRY ] {name}: would create {iface} with {ip} {mask}")
                continue

            print(f"  [CFG ] {name}: creating {iface} {ip} {mask}")
            dev.configure("\n".join([f"interface {iface}",
                                     f" ip address {ip} {mask}",
                                     "exit"]))
            save_config(dev)

            exists_after, _ = find_interface(dev, iface, ip)
            if exists_after:
                print(f"  [OK  ] {name}: verified {iface} has {ip}")
            else:
                print(f"  [ERROR] {name}: verification FAILED for {iface} {ip}")
                errors.append(f"{name}: {iface} {ip} failed verification")

    disconnect_all(tb)

    if errors:
        banner("PIPELINE FAILED  -  Loopback3 creation had problems")
        for item in errors:
            print(f"  - {item}")
        sys.exit(1)

    banner("SUCCESS  -  ping passed and Loopback3 is in place on all routers")


if __name__ == "__main__":
    main()
````

</details>

<details class="file">
<summary><code>jobs/smoke_job.py</code> <span class="file-desc">— pyATS job entry point that runs the test cases.</span></summary>

````python
import os
from pyats.easypy import run


def main(runtime):
    testbed = runtime.testbed
    here = os.path.dirname(__file__)
    testscript = os.path.join(here, "tests", "test_ping_routes.py")
    run(testscript=testscript, testbed=testbed)
````

</details>


## testbed/

<details class="file">
<summary><code>testbed/testbed.yaml</code> <span class="file-desc">— pyATS testbed — each device's OS, management IP, credentials, and SSH options.</span></summary>

````yaml
testbed:
  name: ios_iosxe_testbed

devices:
  iosv-1:
    os: ios
    type: router
    connections:
      defaults:
        class: unicon.Unicon
      cli:
        protocol: ssh
        ip: 198.18.1.7
        arguments:
          ssh_options: >
            -oKexAlgorithms=+diffie-hellman-group14-sha1
            -oHostKeyAlgorithms=+ssh-rsa
            -oPubkeyAcceptedKeyTypes=+ssh-rsa
    credentials:
      default:
        username: admin
        password: C1sco12345
      enable:
        password: C1sco12345

  csr1000v-0:
    os: iosxe
    type: router
    connections:
      defaults:
        class: unicon.Unicon
      cli:
        protocol: ssh
        ip: 198.18.1.6
        arguments:
          ssh_options: >
            -oKexAlgorithms=+diffie-hellman-group14-sha1
            -oHostKeyAlgorithms=+ssh-rsa
            -oPubkeyAcceptedKeyTypes=+ssh-rsa
    credentials:
      default:
        username: admin
        password: C1sco12345
      enable:
        password: C1sco12345
````

</details>


## ansible/

<details class="file">
<summary><code>ansible/group_vars/all.yml</code> <span class="file-desc">— Shared connection credentials for the routers.</span></summary>

````yaml
---
# Connection settings for every router (Cisco IOS / IOS-XE over SSH).
# NOTE: lab credentials only. For real deployments keep secrets in
# Ansible Vault or CI/CD secrets - never commit plain-text passwords.
ansible_connection: ansible.netcommon.network_cli
ansible_network_os: cisco.ios.ios
ansible_user: admin
ansible_password: C1sco12345
ansible_become: true
ansible_become_method: enable
ansible_become_password: C1sco12345
````

</details>

<details class="file">
<summary><code>ansible/inventory/hosts.yml</code> <span class="file-desc">— Test and production device groups.</span></summary>

````yaml
---
# Two logical environments share the same CML devices in this lab:
#   test  -> used for validation / dry-runs (the "test/dev" stage)
#   prod  -> only touched by the gated "production" stage after approval
all:
  children:
    test:
      hosts:
        iosv-1:
          ansible_host: 198.18.1.7
        csr1000v-0:
          ansible_host: 198.18.1.6
    prod:
      hosts:
        iosv-1:
          ansible_host: 198.18.1.7
        csr1000v-0:
          ansible_host: 198.18.1.6
````

</details>

<details class="file">
<summary><code>ansible/playbooks/configure_vlans.yml</code> <span class="file-desc">— Applies the validated VLANs to the routers.</span></summary>

````yaml
---
# Applies the validated VLANs and access interfaces to the routers.
#   -e target=test  -> validation / dry-run devices (default)
#   -e target=prod  -> production devices (gated deploy job only)
- name: "Configure VLANs and access ports from vars/vlans.yml"
  hosts: "{{ target | default('test') }}"
  gather_facts: false
  vars_files:
    - ../vars/vlans.yml
  tasks:
    - name: Build the ios_vlans config list
      ansible.builtin.set_fact:
        vlan_config: "{{ vlan_config | default([]) + [{'vlan_id': item.id, 'name': item.name}] }}"
      loop: "{{ vlans }}"
      loop_control:
        label: "vlan {{ item.id }} ({{ item.name }})"

    - name: Create or update VLANs
      cisco.ios.ios_vlans:
        config: "{{ vlan_config }}"
        state: merged

    - name: Assign access VLANs to interfaces
      cisco.ios.ios_l2_interfaces:
        config:
          - name: "{{ item.1 }}"
            mode: access
            access:
              vlan: "{{ item.0.id }}"
        state: merged
      loop: "{{ vlans | subelements('interfaces') }}"
      loop_control:
        label: "{{ item.1 }} -> vlan {{ item.0.id }}"

    - name: Save running-config to startup-config
      cisco.ios.ios_config:
        save_when: modified
````

</details>

<details class="file">
<summary><code>ansible/playbooks/validate_vlans.yml</code> <span class="file-desc">— Offline schema asserts for every VLAN (no device is touched).</span></summary>

````yaml
---
# TEST / DEV gate - pure static validation, no device connection required.
# Run by the GitHub Actions "validate" job. If any assertion fails the job
# stops with a detailed message and the production deploy never runs.
- name: "TEST/DEV - validate VLAN and interface intent"
  hosts: localhost
  connection: local
  gather_facts: false
  vars_files:
    - ../vars/vlans.yml
  tasks:
    - name: At least one VLAN must be defined
      ansible.builtin.assert:
        that:
          - vlans is defined
          - vlans | length > 0
        fail_msg: "No VLANs defined in vars/vlans.yml - nothing to deploy."
        success_msg: "Found {{ vlans | length }} VLAN definition(s) to validate."

    - name: "VLAN id must be a whole number in the range 1-4094"
      ansible.builtin.assert:
        that:
          - (item.id | string) is match('^[0-9]+$')
          - (item.id | int) >= 1
          - (item.id | int) <= 4094
          - not ((item.id | int) >= 1002 and (item.id | int) <= 1005)
        fail_msg: >-
          INVALID VLAN id '{{ item.id }}' (name '{{ item.name | default("?") }}').
          VLAN ids must be a whole number 1-4094 and must not use the reserved
          range 1002-1005. Fix vars/vlans.yml and push again.
        success_msg: "VLAN id {{ item.id }} OK."
        quiet: true
      loop: "{{ vlans }}"
      loop_control:
        label: "vlan {{ item.id | default('?') }}"

    - name: "VLAN name must be 1-32 chars with no spaces"
      ansible.builtin.assert:
        that:
          - item.name is defined
          - (item.name | string) | length > 0
          - (item.name | string) | length <= 32
          - item.name is match('^[A-Za-z0-9_-]+$')
        fail_msg: >-
          INVALID VLAN name '{{ item.name | default("") }}' for VLAN id
          {{ item.id | default("?") }}. Use 1-32 characters: letters, numbers,
          underscore or hyphen only (no spaces).
        quiet: true
      loop: "{{ vlans }}"
      loop_control:
        label: "vlan {{ item.id | default('?') }}"

    - name: "Interface must match GigabitEthernet<slot>/<port>"
      ansible.builtin.assert:
        that:
          - item.1 is match('^GigabitEthernet[0-9]+/[0-9]+$')
        fail_msg: >-
          INVALID interface '{{ item.1 }}' on VLAN {{ item.0.id }}. Interfaces
          must look like GigabitEthernet<slot>/<port> (for example
          GigabitEthernet0/1). Check for typos and push again.
        quiet: true
      loop: "{{ vlans | subelements('interfaces') }}"
      loop_control:
        label: "{{ item.1 }}"

    - name: "VLAN ids must be unique"
      ansible.builtin.assert:
        that:
          - (vlans | map(attribute='id') | list | length) ==
            (vlans | map(attribute='id') | list | unique | length)
        fail_msg: >-
          Duplicate VLAN ids detected in vars/vlans.yml. Every VLAN id must be
          unique.
        success_msg: "All VLAN ids are unique."

    - name: "Validation passed"
      ansible.builtin.debug:
        msg: "All VLAN/interface checks passed - safe to promote to production."
````

</details>

<details class="file">
<summary><code>ansible/vars/vlans.yml</code> <span class="file-desc">— VLAN intent — the file attendees edit; validated before any device is touched.</span></summary>

````yaml
---
# =====================================================================
#  EDIT ME - this is the file attendees change.
#  The test/dev pipeline validates every entry BEFORE any device is
#  touched. Rules enforced by playbooks/validate_vlans.yml:
#    - id        : whole number 1-4094 (1002-1005 are reserved)
#    - name      : 1-32 chars, letters/numbers/underscore/hyphen only
#    - interface : GigabitEthernet<slot>/<port>   e.g. GigabitEthernet0/1
# =====================================================================
vlans:
  - id: 10
    name: USERS
    interfaces:
      - GigabitEthernet0/1
  - id: 20
    name: VOICE
    interfaces:
      - GigabitEthernet0/2
  - id: 30
    name: MGMT
    interfaces:
      - GigabitEthernet0/3
````

</details>


## jobs/

<details class="file">
<summary><code>jobs/tests/test_ping_routes.py</code> <span class="file-desc">— pyATS test cases: ping 192.168.1.1 and compare static routes.</span></summary>

````python
from pyats import aetest
from genie.testbed import load as load_testbed
import re


# ------------------ Common Setup ------------------
class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect_to_all(self, testbed):
        # Load and connect to all devices
        tb = load_testbed(testbed) if isinstance(testbed, str) else testbed
        self.parent.parameters['tb'] = tb

        for name, dev in tb.devices.items():
            dev.connect(log_stdout=False)


# ------------------ Testcase 1: Ping specific IP ------------------
class PingGateway(aetest.Testcase):

    @aetest.test
    def ping_gateway(self):
        tb = self.parent.parameters['tb']
        target_ip = "192.168.1.1"   # Change here if you want another target

        errors = []
        for name, dev in tb.devices.items():
            out = dev.execute(f"ping {target_ip} repeat 5 timeout 2")
            match = re.search(r"Success +rate +is +(\d+) +percent", out, re.I)
            if not match or int(match.group(1)) < 100:
                errors.append(f"{name} failed to ping {target_ip}: {out.strip().splitlines()[-1]}")

        if errors:
            self.failed("Ping test failures:\n" + "\n".join(errors))


# ------------------ Testcase 2: Static routes equal ------------------
class StaticRoutesEqual(aetest.Testcase):

    def get_static_routes(self, dev):
        try:
            out = dev.execute("show ip route static")
        except Exception:
            out = dev.execute("show ip route")
        return {m.group(1) for m in re.finditer(r"S\s+(\d+\.\d+\.\d+\.\d+/\d+)", out)}

    @aetest.test
    def compare_routes(self):
        tb = self.parent.parameters['tb']
        devices = list(tb.devices.values())

        if len(devices) < 2:
            self.skipped("Need at least 2 devices to compare")

        baseline = self.get_static_routes(devices[0])
        diffs = []
        for dev in devices[1:]:
            routes = self.get_static_routes(dev)
            if routes != baseline:
                diffs.append(f"{dev.name} differs: {routes ^ baseline}")

        if diffs:
            self.failed("Route mismatches:\n" + "\n".join(diffs))


# ------------------ Common Cleanup ------------------
class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect_all(self):
        tb = self.parent.parameters['tb']
        for dev in tb.devices.values():
            try:
                dev.disconnect()
            except Exception:
                pass
````

</details>

