---
title: Lab 1 — Hands-on Walkthrough (step by step)
nav: Lab 1 · Hands-on steps
order: 3
eyebrow: Lab 1 · Walkthrough
description: A fully illustrated, numbered walkthrough — start the lab, build the GitLab project, run the pipeline, and troubleshoot it to a green run.
---

# Lab 1 — Hands-on Walkthrough (step by step)

> **Follow this page top to bottom.** Every step is numbered and includes a
> screenshot. Do the steps in order — each one builds on the previous.
>
> **Before you start**, read the [Home](index.html) page for lab access
> (code-server, GitLab, CML) and the [Lab 1 concepts](lab1-netdevops.html) page
> for *why* the pipeline works the way it does. This page is the *how*.

**What you will do:** start the virtual network, create a GitLab project, push
the pipeline files, watch the pipeline **fail on purpose**, and then fix it
**stage by stage** until every stage passes.

| Credential | Value |
|------------|-------|
| code-server | `https://198.18.1.18:8080` · password `C1sco12345` |
| GitLab | `http://198.18.1.18:8929` · `root` / `C1sco12345` |
| Cisco CML | `https://198.18.1.2` · `admin` / `C1sco12345` |
| Routers (`csr1000v-0`, `iosv-1`, `iosv-0`) | `admin` / `C1sco12345` |

---

## Part A — Start the lab environment

### Step 1 — Start the CML topology

Open Cisco Modeling Labs at **`https://198.18.1.2`** and sign in
(`admin` / `C1sco12345`). It uses a self-signed certificate, so accept the
browser warning once. On the **Dashboard**, find the **network_automation** lab
and click the blue **▶ (Start)** button. Wait until every node shows a green
"running" status before you continue.

![Start the network_automation lab in the CML dashboard](images/lab1-hands-on-01.png)
*Figure 1 — In the CML dashboard, open the **network_automation** lab and click **▶ Start**.*

### Step 2 — Open code-server and trust the workspace

Open **code-server** at **`https://198.18.1.18:8080`** and enter the password
`C1sco12345`. The first time it opens the `/home/cisco` folder, VS Code asks
whether you trust the files in this workspace. Click **Manage**, then click
**Trust** so that terminals, linters, and extensions are allowed to run.

![code-server workspace trust prompt — click Manage](images/lab1-hands-on-02.png)
*Figure 2 — When code-server opens, click **Manage** on the workspace-trust prompt.*

![Click Trust to trust the workspace authors](images/lab1-hands-on-03.png)
*Figure 3 — Click **Trust** so the IDE can run terminals and extensions.*

![code-server Explorer showing the home folder](images/lab1-hands-on-04.png)
*Figure 4 — code-server opens on `/home/cisco`; your lab folders live under `automation_projects/`.*

![code-server ready with the integrated terminal](images/lab1-hands-on-05.png)
*Figure 5 — Open a terminal with **Terminal ▸ New Terminal** — every command below runs here.*

### Step 3 — Open the project folder and confirm the services are running

In the integrated terminal, change into the Lab 1 project folder and confirm the
GitLab and runner containers are healthy:

```bash
cd automation_projects/clmel26_automation/
docker ps -a
```

You should see the GitLab server (`gitlab`, status **healthy**) and two GitLab
runners (`clmel-runner-pyats` and `clmel-runner-docker`), all **Up**. If they are
not running, wait a minute and re-run `docker ps -a`.

![docker ps -a showing GitLab and the two runners Up and healthy](images/lab1-hands-on-06.png)
*Figure 6 — `docker ps -a` confirms the GitLab server and both runners are running.*

---

## Part B — Create the GitLab project

### Step 4 — Sign in to GitLab and create a new project

Open GitLab at **`http://198.18.1.18:8929`** and sign in as `root` /
`C1sco12345`. Click **+ ▸ New project/repository**, then choose
**Create blank project**.

![Sign in to GitLab and start a new project](images/lab1-hands-on-07.png)
*Figure 7 — In GitLab, sign in and choose to create a new project.*

![Choose Create blank project](images/lab1-hands-on-08.png)
*Figure 8 — Select **Create blank project**.*

![Enter the project name and visibility](images/lab1-hands-on-09.png)
*Figure 9 — Give the project a name (for example `myproject`) and create it.*

### Step 5 — Copy the project's HTTPS clone command

On the new (empty) project page, open the **Add files** panel and select the
**HTTPS** tab. GitLab shows a ready-made **"Create a new repository"** block —
you will use these commands in the next steps. Note the clone URL, which looks
like `http://198.18.1.18:8929/root/myproject.git`.

![Empty project page with the HTTPS clone commands](images/lab1-hands-on-10.png)
*Figure 10 — On the empty project, use the **HTTPS** tab and copy the clone URL.*

### Step 6 — Confirm the GitLab runners are online

Go to **Settings ▸ CI/CD ▸ Runners** and confirm at least one runner shows a
**green** "online" dot. The runners are what actually execute your pipeline; if
they are offline, the pipeline will stay stuck in "pending".

![GitLab runners showing online for the project](images/lab1-hands-on-11.png)
*Figure 11 — Confirm the project's GitLab runners are online (green).*

---

## Part C — Clone and seed the repository

### Step 7 — Clone the empty project in code-server

Back in the code-server terminal, clone the project into your working folder.
Enter your GitLab username (`root`) and password (`C1sco12345`) when Git prompts
for credentials:

```bash
cd ~/automation_projects
git clone http://198.18.1.18:8929/root/myproject.git
cd myproject
```

![git clone in code-server prompting for the GitLab username](images/lab1-hands-on-12.png)
*Figure 12 — Clone the project in code-server; enter your GitLab username and password when prompted.*

### Step 8 — (Optional) Create the first commit

If this is a brand-new, empty repository, seed it with a first file so the
`main` branch exists on the server:

```bash
git switch --create main
touch README.md
git add README.md
git commit -m "add README"
git push --set-upstream origin main
```

> **If Git says `Author identity unknown` / "Please tell me who you are":** set
> your name and email once (the first commit failed because Git did not know who
> you are), then re-run the commit and push:
>
> ```bash
> git config --global user.email "root@example.com"
> git config --global user.name "root"
> git commit -m "add README"
> git push --set-upstream origin main
> ```

![Creating and pushing the first README commit](images/lab1-hands-on-13.png)
*Figure 13 — Create the `main` branch and a first `README.md`.*

![Staging and committing the first file](images/lab1-hands-on-14.png)
*Figure 14 — Stage and commit the file.*

![Pushing the first commit to GitLab](images/lab1-hands-on-15.png)
*Figure 15 — Push to GitLab with `--set-upstream origin main`.*

### Step 9 — Verify the initial file in the GitLab UI

Refresh the project in the GitLab web UI. You should now see your `README.md` (or
the first files) listed in the repository.

![Initial files shown in the GitLab project](images/lab1-hands-on-16.png)
*Figure 16 — Confirm the initial file appears in GitLab.*

---

## Part D — Add the pipeline project files

### Step 10 — Add the required project files

The pipeline needs a specific set of files. The **easiest** way is to **copy them
from the `solution_for_network_automation` folder** (already on the workstation)
into your `myproject` folder. Do it in the terminal — go into the solution folder
and copy everything (including hidden dot-files) into your project:

```bash
cd ~/automation_projects/solution_for_network_automation
ls -al                                              # see what you are copying
cp -a ./ ~/automation_projects/myproject/           # copy every file into your project
```

> **Tip:** You can also copy the files in the code-server **Explorer** — select
> them, **Copy**, then **Paste** into your project — or create them by hand
> (`mkdir <folder>` and edit in the code-server editor). The `cp -a` command above
> is the fastest and preserves the folder structure.

Your project ends up with this structure:

```text
myproject/
├── .gitlab-ci.yml                     # the pipeline: validate → network_check → deploy
├── testbed/testbed.yaml               # pyATS device inventory (IPs, creds, SSH options)
├── jobs/
│   ├── smoke_job.py                   # pyATS job entry point
│   ├── configure_loopback.py          # applies Loopback300 when tests pass
│   ├── ping_and_loopback.py           # ping gate → creates Loopback3
│   └── tests/test_ping_routes.py      # ping + static-route test cases
├── configs/
│   ├── loopbacks.yaml                 # declarative Loopback300
│   └── loopback3.yaml                 # declarative Loopback3 + ping target
└── ansible/
    ├── ansible.cfg
    ├── requirements.yml
    ├── group_vars/all.yml
    ├── inventory/hosts.yml
    ├── vars/vlans.yml                 # VLAN intent — you edit this later
    └── playbooks/
        ├── validate_vlans.yml
        └── configure_vlans.yml
```

![The solution folder with the files to copy](images/lab1-hands-on-17.png)
*Figure 17 — Copy the required files from the `solution_for_network_automation` folder …*

![Pasting the files into your project folder](images/lab1-hands-on-18.png)
*Figure 18 — … and paste them into your `myproject` folder in the Explorer.*

### Step 11 — Commit and push all the files

Stage, commit, and push everything to GitLab. Use the **Source Control** panel in
code-server, or run in the terminal:

```bash
cd ~/automation_projects/myproject
git add .
git commit -m "first commit"
git push
```

![Staging and committing all project files](images/lab1-hands-on-19.png)
*Figure 19 — Stage and commit all of the project files.*

![Pushing the project files to the GitLab remote](images/lab1-hands-on-20.png)
*Figure 20 — Push the files to the GitLab remote.*

### Step 12 — Confirm the files in GitLab

Refresh the project in GitLab and confirm the full file tree is present
(`.gitlab-ci.yml`, `ansible/`, `configs/`, `jobs/`, `testbed/`).

![The complete project file tree in GitLab](images/lab1-hands-on-21.png)
*Figure 21 — Confirm all files are now in the GitLab repository.*

---

## Part E — Run and troubleshoot the pipeline

Pushing `.gitlab-ci.yml` automatically starts a pipeline. **It is meant to fail
the first time** — that is the whole point of the exercise. You will now read the
failures and fix them one stage at a time.

### Step 13 — Watch the first pipeline fail

Go to **Build ▸ Pipelines**. The latest pipeline shows a red **Failed** status.

![The first pipeline run shown as Failed](images/lab1-hands-on-22.png)
*Figure 22 — **Build ▸ Pipelines** — the first run has **Failed**. This is expected.*

### Step 14 — Open the failed job and read the error

Click the failed pipeline, then click the first failed **stage** and its **job**
to open the log. Read the error message at the bottom — it tells you exactly what
is wrong. Here, the **validate** stage reports an **invalid VLAN id**:

```text
[ERROR]: INVALID VLAN id '5000' (name 'VOICE'). VLAN ids must be a whole number
1-4094 and must not use the reserved range 1002-1005. Fix vars/vlans.yml and push again.
Origin: ansible/playbooks/validate_vlans.yml
```

![Opening the failed job](images/lab1-hands-on-23.png)
*Figure 23 — Click the failed stage and job to open its log.*

![The validate job error — invalid VLAN id 5000](images/lab1-hands-on-24.png)
*Figure 24 — The **validate** stage fails because `vlans.yml` contains an invalid VLAN id (`5000`).*

### Step 15 — Make the stages run in order

Before fixing the VLAN, make the pipeline **stop at the first broken stage**.
Right now the `ping_and_loopback` job has `needs: []`, which lets it start
**independently** of the `validate` stage — so a failure in Stage 1 does not stop
Stage 2. Go to **Build ▸ Pipeline editor** and **comment out** that line by adding
a `#` in front of it:

```yaml
ping_and_loopback:
  stage: network_check
  #needs: []          # commented out so this job waits for the validate stage
  script:
    - ...
```

![Pipeline editor showing needs: [] before the change](images/lab1-hands-on-25.png)
*Figure 25 — Open **Build ▸ Pipeline editor**.*

![The needs: [] line that makes the job independent](images/lab1-hands-on-26.png)
*Figure 26 — Find `needs: []` on the `ping_and_loopback` job — it makes the job independent of `validate`.*

![The needs line commented out](images/lab1-hands-on-27.png)
*Figure 27 — Add `#` to comment it out (`#needs: []`) so `network_check` only runs after `validate` passes.*

### Step 16 — Commit the pipeline change and confirm gating

Enter a commit message (for example *"Update .gitlab-ci.yml file"*) and click
**Commit changes**. Run the pipeline again and confirm the behaviour: now, when a
stage fails, the pipeline **stops** and the later stages do not run.

![Commit the pipeline editor change](images/lab1-hands-on-28.png)
*Figure 28 — Commit the change to `.gitlab-ci.yml`.*

![Pipeline now stops when an earlier stage fails](images/lab1-hands-on-29.png)
*Figure 29 — The pipeline now **stops** at the first failed stage instead of continuing.*

### Step 17 — Fix Stage 1: correct the invalid VLAN

Now fix the actual problem from Step 14. Go to **Code ▸ Repository ▸
`ansible/vars/vlans.yml`**, click **Edit ▸ Edit single file**, and change the
invalid VLAN. The bad entry is `id: 5000` (name `VOICE`) — change it to a valid
id such as **`20`**:

```yaml
- id: 20            # was 5000 — VLAN ids must be 1-4094
  name: VOICE
  interfaces:
    - GigabitEthernet0/2
```

Enter a commit message and click **Commit changes**.

![Editing vlans.yml in the GitLab web editor](images/lab1-hands-on-30.png)
*Figure 30 — Open `ansible/vars/vlans.yml` and choose **Edit ▸ Edit single file**.*

![Changing the VLAN id from 5000 to 20](images/lab1-hands-on-31.png)
*Figure 31 — Change the invalid `id: 5000` to a valid id such as `20`.*

![Committing the vlans.yml change](images/lab1-hands-on-32.png)
*Figure 32 — Click **Commit changes**.*

### Step 18 — Confirm Stage 1 passes and read the Stage 2 error

The new commit starts another pipeline. This time **Stage 1 (validate) passes**,
but **Stage 2 (network_check) fails**. Open the failed `ping_and_loopback` job to
read why — every router fails to **ping `192.168.1.1`**:

```text
STEP 1  Ping pre-check  ->  every router must reach 192.168.1.1
  [FAIL] iosv-1     -> 192.168.1.1: success rate 0%
  [FAIL] csr1000v-0 -> 192.168.1.1: success rate 0%
PIPELINE FAILED - ping pre-check did not pass
```

![Stage 1 passing and Stage 2 failing](images/lab1-hands-on-33.png)
*Figure 33 — Stage 1 now passes; Stage 2 (network_check) fails. Click it to see why.*

![The ping pre-check failure — routers cannot reach 192.168.1.1](images/lab1-hands-on-34.png)
*Figure 34 — Both routers fail to ping `192.168.1.1`, so nothing is configured.*

### Step 19 — Fix Stage 2: bring up Loopback2 on iosv-0

`192.168.1.1` lives on interface **`Loopback2`** of the middle router **`iosv-0`**,
and it is **shut down by default** — that is why the ping fails. Fix it on the
device. In CML, **right-click `iosv-0` ▸ Console ▸ Open Console**, then bring the
interface up:

```text
enable
configure terminal
 interface Loopback2
  no shutdown
 end
write memory
```

The console confirms `Interface Loopback2, changed state to up`.

![Open the iosv-0 console in CML](images/lab1-hands-on-35.png)
*Figure 35 — In CML, right-click **iosv-0** and open its console.*

![The iosv-0 console](images/lab1-hands-on-36.png)
*Figure 36 — The `iosv-0` console opens.*

![no shutdown on Loopback2 brings 192.168.1.1 up](images/lab1-hands-on-37.png)
*Figure 37 — `interface Loopback2` → `no shutdown` brings `192.168.1.1` up.*

### Step 20 — Re-run the pipeline

Go back to GitLab, open **Build ▸ Pipelines**, and click **New pipeline ▸ New
pipeline** to run it again against the now-fixed network.

![Return to GitLab pipelines](images/lab1-hands-on-38.png)
*Figure 38 — Back in GitLab, go to **Build ▸ Pipelines**.*

![Click New pipeline to run again](images/lab1-hands-on-39.png)
*Figure 39 — Click **New pipeline** to trigger a fresh run.*

### Step 21 — Confirm every stage passes

This time **validate** and **network_check** both pass (green). The **deploy**
stage is a **manual** gate — click its **▶** button to deploy when you are ready.
🎉 You have completed Lab 1.

![All pipeline stages passing](images/lab1-hands-on-40.png)
*Figure 40 — **validate** and **network_check** pass; **deploy** waits for a manual click.*

---

## Appendix — Keep your local copy in sync

Because you edited some files in the **GitLab web UI** (Steps 15–17), your local
clone in code-server is now behind the remote. Pull the latest changes down before
you edit locally again:

```bash
git fetch origin
git pull origin main
```

![git fetch and git pull sync the remote edits back to local](images/lab1-hands-on-41.png)
*Figure 41 — `git fetch` + `git pull origin main` bring the web-UI edits back to your local copy.*

From here you can edit any file in **code-server**, then commit and push it back to
the remote — either from the **Source Control** panel, or from the terminal with
the same edit-commit-push loop:

```bash
git status                              # see what you changed
git add .
git commit -m "checking CLI commit"
git push
```

![Editing a file in code-server and committing to the remote](images/lab1-hands-on-42.png)
*Figure 42 — Edit in code-server, then commit and push back to the GitLab remote.*
