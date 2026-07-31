#!/usr/bin/env python3
"""Generate the "project files" appendix pages from the real lab source.

Reads every relevant file in each lab folder and writes a Markdown appendix that
shows the file in full, in a syntax-highlighted, copy-buttoned code block. Running
this keeps the appendices in sync with the actual scripts — never hand-edit the
generated pages; edit the source file and re-run this script.

    python tools/build_file_appendices.py

Output:
    content/appendix-lab1-files.md   (Lab 1 — clmel26_automation)
    content/appendix-lab2-files.md   (Lab 2 — cisco_security_iac)
"""
from __future__ import annotations

import pathlib

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent      # docs_labguide/
REPO_ROOT = DOCS_DIR.parent                                    # repo root
CONTENT_DIR = DOCS_DIR / "content"

# Directories we never dump (repo/site infra, caches, generated state).
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", ".terraform",
             "node_modules", "docs", ".github", "tools", ".pytest_cache",
             "collections", ".ansible"}
# We skip Markdown (its own code fences would collide) and binaries/locks.
SKIP_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
                 ".pyc", ".lock", ".retry"}
SKIP_NAMES = {".DS_Store", ".terraform.lock.hcl"}


def lang_for(path: pathlib.Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name.endswith(".tfvars.example") or suffix in (".tf", ".tfvars"):
        return "hcl"
    if name.endswith(".env.example") or name.startswith("config.env") or suffix == ".env":
        return "ini"
    if name in (".gitlab-ci.yml", ".yamllint", ".ansible-lint") or suffix in (".yml", ".yaml"):
        return "yaml"
    if suffix == ".py":
        return "python"
    if suffix in (".cfg", ".ini") or name in ("pytest.ini", "ansible.cfg"):
        return "ini"
    if suffix == ".json":
        return "json"
    if suffix == ".sh":
        return "bash"
    return "text"  # requirements.txt, .gitignore, plain text


def fence_for(content: str) -> str:
    """Return a backtick fence longer than any backtick run in the content."""
    longest = 0
    run = 0
    for ch in content:
        if ch == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return "`" * max(4, longest + 1)


def collect_files(root: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        if p.name in SKIP_NAMES or p.suffix.lower() in SKIP_SUFFIXES:
            continue
        files.append(p)
    # Root-level files first, then by folder, then by name.
    files.sort(key=lambda f: (len(f.relative_to(root).parts), str(f.relative_to(root)).lower()))
    return files


# Short, friendly descriptions for the well-known files (optional; falls back to
# nothing). Keyed by path relative to the lab root.
DESCRIPTIONS = {
    # ---- Lab 1 ----
    ".gitlab-ci.yml": "The pipeline definition: three stages — validate → network_check → deploy.",
    "requirements.txt": "Python dependencies (pyATS, Genie, PyYAML).",
    "testbed/testbed.yaml": "pyATS testbed — each device's OS, management IP, credentials, and SSH options.",
    "jobs/smoke_job.py": "pyATS job entry point that runs the test cases.",
    "jobs/configure_loopback.py": "Applies Loopback300 to the routers once the tests pass.",
    "jobs/ping_and_loopback.py": "Ping gate — pings the target and, only if all pass, creates Loopback3.",
    "jobs/tests/test_ping_routes.py": "pyATS test cases: ping 192.168.1.1 and compare static routes.",
    "configs/loopbacks.yaml": "Declarative Loopback300 definition.",
    "configs/loopback3.yaml": "Declarative Loopback3 addresses and the ping target.",
    "ansible/vars/vlans.yml": "VLAN intent — the file attendees edit; validated before any device is touched.",
    "ansible/playbooks/validate_vlans.yml": "Offline schema asserts for every VLAN (no device is touched).",
    "ansible/playbooks/configure_vlans.yml": "Applies the validated VLANs to the routers.",
    "ansible/inventory/hosts.yml": "Test and production device groups.",
    "ansible/group_vars/all.yml": "Shared connection credentials for the routers.",
    "ansible/requirements.yml": "Ansible collections (cisco.ios, ansible.netcommon).",
    "ansible/ansible.cfg": "Ansible configuration for the playbooks.",
    # ---- Lab 2 ----
    "terraform/versions.tf": "Terraform and provider version constraints.",
    "terraform/providers.tf": "FMC connection settings (url, username, password, insecure).",
    "terraform/variables.tf": "Inputs: FMC URL, credentials, inside/outside CIDRs, policy name.",
    "terraform/objects.tf": "Two fmc_network objects (inside/outside subnets).",
    "terraform/zones.tf": "Two fmc_security_zone objects (inside/outside).",
    "terraform/access_policy.tf": "The access control policy plus the inline ALLOW rule.",
    "terraform/outputs.tf": "Prints the created object / policy IDs.",
    "terraform/terraform.tfvars.example": "Example variable values — copy to terraform.tfvars.",
    "rest_api/fmc_access_policy.py": "Python client: token auth → objects → policy → rule (defaults to a safe dry-run).",
    "rest_api/tests/test_payloads.py": "Offline unit tests for the JSON payload builders.",
    "rest_api/requirements.txt": "Python dependencies (requests, PyYAML, pytest).",
    "rest_api/config.env.example": "Example environment variables — copy to config.env.",
    "rest_api/pytest.ini": "pytest configuration.",
    "ansible/create_access_policy.yml": "Playbook: create the objects → policy → rule via the FMC REST API.",
    "ansible/inventory.yml": "FMC management hosts.",
    "ansible/group_vars/fmc.yml": "httpapi connection settings for the FMC.",
}


def group_of(rel: pathlib.Path) -> str:
    parts = rel.parts
    return "Project root" if len(parts) == 1 else parts[0] + "/"


def render_lab(root: pathlib.Path) -> str:
    """Render each file as a collapsible <details> block, grouped by folder.

    The blank lines around the fenced code block are required so the Markdown
    renderer parses the code (and applies syntax highlighting) instead of treating
    it as raw HTML inside <details>.
    """
    files = collect_files(root)
    lines: list[str] = []
    current_group = None
    for f in files:
        rel = f.relative_to(root)
        rel_posix = rel.as_posix()
        group = group_of(rel)
        if group != current_group:
            lines.append(f"\n## {group}\n")
            current_group = group
        content = f.read_text(encoding="utf-8", errors="replace").rstrip("\n")
        lang = lang_for(f)
        fence = fence_for(content)
        desc = DESCRIPTIONS.get(rel_posix, "")
        desc_html = f' <span class="file-desc">— {desc}</span>' if desc else ""
        lines.append(f'<details class="file">')
        lines.append(f"<summary><code>{rel_posix}</code>{desc_html}</summary>")
        lines.append("")  # blank line: resume Markdown parsing for the code block
        lines.append(f"{fence}{lang}")
        lines.append(content)
        lines.append(fence)
        lines.append("")  # blank line before closing the HTML block
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


LABS = [
    {
        "root": REPO_ROOT / "clmel26_automation",
        "out": CONTENT_DIR / "appendix-lab1-files.md",
        "frontmatter": (
            "---\n"
            "title: Appendix — Lab 1 project files\n"
            "nav: Project files\n"
            "group: Lab 1 · NetDevOps\n"
            "order: 6\n"
            "eyebrow: Lab 1 · Reference\n"
            "description: Every Lab 1 (NetDevOps) project file in full — syntax-highlighted, with a copy button.\n"
            "---\n"
        ),
        "intro": (
            "# Appendix — Lab 1 project files\n\n"
            "> **Reference dump of the NetDevOps project (`clmel26_automation/`).** Every file the\n"
            "> [Lab 1 walkthrough](lab1-hands-on.html) uses is shown below in full. Hover a code\n"
            "> block and click **Copy** to copy it. These pages are generated from the real source\n"
            "> files, so they always match what you run in the lab.\n"
        ),
    },
    {
        "root": REPO_ROOT / "cisco_security_iac",
        "out": CONTENT_DIR / "appendix-lab2-files.md",
        "frontmatter": (
            "---\n"
            "title: Appendix — Lab 2 project files\n"
            "nav: Project files\n"
            "group: Lab 2 · Security IaC\n"
            "order: 7\n"
            "eyebrow: Lab 2 · Reference\n"
            "description: Every Lab 2 (Security IaC) project file in full — Terraform, REST API, and Ansible — with a copy button.\n"
            "---\n"
        ),
        "intro": (
            "# Appendix — Lab 2 project files\n\n"
            "> **Reference dump of the Security IaC project (`cisco_security_iac/`).** Every file for\n"
            "> the [Lab 2](lab2-security-iac.html) Terraform, REST API, and Ansible scenarios is shown\n"
            "> below in full. Hover a code block and click **Copy** to copy it. These pages are\n"
            "> generated from the real source files, so they always match what you run in the lab.\n"
        ),
    },
]


def main() -> None:
    for lab in LABS:
        root = lab["root"]
        if not root.is_dir():
            print(f"SKIP (missing): {root}")
            continue
        body = render_lab(root)
        text = lab["frontmatter"] + "\n" + lab["intro"] + body + "\n"
        lab["out"].write_text(text, encoding="utf-8")
        n = text.count('<details class="file">')
        print(f"Wrote {lab['out'].relative_to(DOCS_DIR).as_posix()}  ({n} files, {len(text):,} bytes)")


if __name__ == "__main__":
    main()
