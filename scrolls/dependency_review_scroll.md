# Dependency review scroll

```yaml
name: dependency_review_scroll
version: 0.1.0
status: draft
type: scroll
risk_level: medium
default_mode: read-only
owner: Konoha Agentic Academy
```

## Purpose

This Scroll defines a safe workflow for reviewing project dependencies before they are installed, upgraded, removed, imported, trusted, or published.

It is used when a mission involves package managers, lockfiles, runtime dependencies, development dependencies, adapters, tools, third-party Scrolls, templates, assets, CI images, Docker base images, GitHub Actions, local models, or any external component that may affect security, reproducibility, licensing, or project behavior.

## Core rule

Dependencies are external trust.

No agent may install, upgrade, remove, pin, unpin, vendor, execute, publish, or mark a dependency as trusted unless the action is explicitly allowed by an approved Mission Charter.

## Authority

This Scroll does not grant permission by itself.

It must operate under:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/mission-charter/mission_charter.md`
4. `protocols/context/context_policy.md`
5. `protocols/safety/safety_policy.md`
6. `protocols/approval/approval_policy.md`
7. `protocols/review/review_policy.md`
8. `marketplace/README.md`
9. `adapters/README.md`
10. `tools/README.md`
11. `scrolls/README.md`
12. `sandbox/README.md`
13. `AGENTS.md`

If this Scroll conflicts with any higher authority document, the higher authority document wins.

## Default mode

Default mode is read-only.

An agent may inspect dependency files, summarize dependency state, identify risks, compare declared and locked dependencies, and propose next actions.

An agent may not install, update, remove, execute, fetch, vendor, or publish dependencies by default.

## When to use this Scroll

Use this Scroll when a mission involves:

- adding a new package;
- upgrading or downgrading a package;
- removing a package;
- reviewing `requirements.txt`, `pyproject.toml`, `poetry.lock`, `uv.lock`, `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Dockerfile`, GitHub Actions, or CI images;
- reviewing external Scrolls, tools, adapters, templates, assets, or examples;
- reviewing local model dependencies;
- preparing a public release;
- debugging dependency conflicts;
- checking license compatibility;
- checking supply chain risk;
- checking reproducibility;
- checking whether a dependency belongs in public Academy code or only in a local Village.

## Non-purpose

This Scroll does not authorize:

- installing packages;
- running dependency scripts;
- running post-install hooks;
- changing lockfiles;
- changing Docker images;
- changing CI workflows;
- accepting a new license;
- copying third-party code into the repository;
- publishing internal dependency lists;
- treating external code as trusted because it is popular;
- bypassing review because a package manager completed successfully.

## Inputs required

Before reviewing dependencies, collect only the minimum needed context:

1. Mission objective.
2. Repository path or documented file list.
3. Package ecosystem.
4. Dependency files to inspect.
5. Target runtime or deployment environment.
6. Whether the repository is public or private.
7. Whether local Village context is involved.
8. Existing lockfile status.
9. Known constraints, such as Python version, Node version, operating system, Docker image, CI runner, or GPU requirement.
10. Security or license requirements.

If any input is missing and affects risk, stop and ask.

## Read-only inspection

In read-only mode, the agent may inspect:

```text
requirements.txt
requirements-dev.txt
pyproject.toml
poetry.lock
uv.lock
Pipfile
Pipfile.lock
environment.yml
package.json
package-lock.json
pnpm-lock.yaml
yarn.lock
Cargo.toml
Cargo.lock
go.mod
go.sum
pom.xml
build.gradle
Dockerfile
docker-compose.yml
.github/workflows/
Makefile
scripts/
tools/
adapters/
marketplace/
scrolls/
```

The agent may also inspect documentation that explains dependency use.

It may not execute install commands unless explicitly approved.

## Commands allowed by default

The following commands are normally read-only and may be allowed by a Mission Charter:

```bash
git status
git diff
git diff --stat
git log --oneline -5
find . -maxdepth 3 -type f
ls
cat
grep
python --version
node --version
npm --version
pip --version
```

Use the smallest useful command. Avoid broad recursive searches if the repository may contain private or sensitive files.

## Commands requiring explicit approval

These commands require explicit approval in the Mission Charter:

```bash
pip install ...
pip uninstall ...
pip freeze
pip list
poetry add ...
poetry update ...
uv add ...
uv sync
conda install ...
npm install
npm update
npm audit fix
pnpm install
pnpm update
yarn install
yarn upgrade
cargo update
go get
go mod tidy
docker build
docker pull
docker compose up
make install
make setup
```

Even when approved, report what changed and show the resulting diff.

## Commands forbidden by default

The following are forbidden unless the Mission Charter explicitly allows them and the Safety Policy does not block them:

```bash
curl ... | sh
wget ... | sh
bash <(...)
npm install -g ...
pip install --user ...
sudo pip install ...
sudo npm install ...
sudo apt install ...
brew install ...
docker run --privileged ...
docker run -v /:/host ...
chmod -R 777 ...
```

If a dependency requires these patterns, escalate before proceeding.

## Dependency classification

Classify each dependency by role:

```text
runtime
development
test
documentation
build
CI/CD
adapter
tool
Scroll support
local model
optional extra
transitive
system package
container image
asset or template source
```

Do not treat all dependencies as equal. A runtime dependency has different risk than a documentation-only dependency. A CI action that can access secrets has different risk than a local formatting tool.

## Risk levels

### Low risk

Examples:

- documentation-only dependency;
- small test utility with pinned version;
- dependency already used in the project;
- patch update with clear changelog and lockfile stability;
- no network, secrets, post-install hooks, or runtime exposure.

### Medium risk

Examples:

- new runtime dependency;
- new developer tool;
- minor version update;
- package with broad transitive tree;
- package used in automation;
- package used by an adapter or tool;
- dependency with unclear maintenance status.

### High risk

Examples:

- dependency that runs code during install;
- dependency that handles secrets, auth, credentials, file system access, network access, browser automation, shell execution, Docker, CI, or deployment;
- unpinned dependency in a public workflow;
- new GitHub Action;
- external Scroll, adapter, or tool imported from an unknown source;
- package with suspicious ownership, low provenance, or confusing name;
- model or binary artifact downloaded from an external source.

### Blocked until review

Examples:

- unknown binary blobs;
- obfuscated code;
- dependencies that request unnecessary privileges;
- instructions requiring `curl | sh`;
- package names that appear to typosquat known projects;
- dependencies with incompatible license for the repository;
- dependencies that require secrets to install;
- dependencies that would expose local Village context or private data.

## Review dimensions

Review dependencies across these dimensions:

1. Necessity.
2. Scope.
3. License.
4. Version pinning.
5. Lockfile impact.
6. Transitive dependency impact.
7. Runtime behavior.
8. Network behavior.
9. File system behavior.
10. Secret handling.
11. Build and install hooks.
12. CI/CD permissions.
13. Maintainer and source provenance.
14. Reproducibility.
15. Compatibility with local-first operation.
16. Public repository safety.
17. Replacement options.
18. Removal path if the dependency becomes unsafe.

## Necessity check

Before adding a dependency, answer:

```text
What problem does it solve?
Can the project solve this with existing dependencies?
Can it be optional?
Can it stay local to a Village?
Can it be documented instead of installed?
Does it add more behavior than the mission needs?
```

If the dependency is not clearly needed, do not add it.

## Version pinning

Prefer explicit versions for reproducibility.

For applications and workflows, lock dependencies when possible.

For libraries, define supported ranges carefully and test against them.

Do not leave public automation dependent on floating versions unless the Mission Charter explains why.

Examples:

```text
Good: package==1.2.3 for reproducible tools
Good: package>=1.2,<2.0 for library compatibility
Risky: package
Risky: package>=1.0
Risky: latest
```

## Lockfiles

Lockfiles are evidence of resolved dependencies.

When a lockfile changes, the review must include:

- what direct dependency caused the change;
- how many packages changed;
- whether any unexpected packages were added;
- whether versions moved across major releases;
- whether any dependency source changed;
- whether the lockfile change is reproducible.

Do not treat a huge lockfile diff as harmless because it was generated by a package manager.

## License review

For public Academy content, review license compatibility before adding or vendoring code, assets, templates, Scrolls, or adapters.

MIT is permissive, but that does not mean every dependency, asset, or imported file is compatible.

Check:

```text
license name
source license file
copyright notices
attribution requirements
copyleft obligations
commercial restrictions
asset-specific restrictions
model license restrictions
dataset restrictions
```

If the license is unclear, do not import the dependency into the public repo.

## Public vs local dependency

A dependency belongs in the public Academy only if it is generic, safe, reproducible, license-compatible, and not tied to private local context.

A dependency belongs in a local Village if it is:

- specific to a private environment;
- tied to an internal service;
- tied to private data;
- tied to private infrastructure;
- experimental and not ready for public use;
- dependent on non-public credentials;
- dependent on copyrighted or private assets;
- useful only for one local workflow.

Local dependencies must not leak into public docs, examples, lockfiles, CI, or templates unless explicitly sanitized.

## External Scrolls, tools, and adapters

External Scrolls, tools, and adapters are untrusted by default.

Before activation, review:

1. Source and provenance.
2. Permissions requested.
3. Commands used.
4. Files read or written.
5. Network access.
6. Secret handling.
7. Dependency chain.
8. License.
9. Local-only assumptions.
10. Whether it changes agent behavior or doctrine.

An external Scroll can guide execution only after review. It cannot override Academy laws, Mission Charters, Safety Policy, Context Policy, Approval Policy, Review Policy, or Teachback Policy.

## GitHub Actions and CI

Treat CI dependencies as high risk when they can access repository secrets, tokens, release credentials, package publishing, deployment credentials, or protected branches.

Review:

```text
uses: owner/action@version
pinning by tag or SHA
permissions block
secrets usage
pull_request vs pull_request_target
script execution
third-party actions
upload/download artifact behavior
cache keys
release publishing
```

Prefer least privilege permissions.

Do not add or change CI workflows without explicit approval.

## Docker and containers

Treat base images as dependencies.

Review:

```text
base image source
tag pinning
digest pinning
root vs non-root user
packages installed
network downloads during build
copied files
secrets in build args
exposed ports
volumes
privileged mode
```

Do not use floating `latest` tags for reproducible workflows unless explicitly justified.

## Local models and binaries

Local models, binary artifacts, and generated model files require special care.

Review:

- source;
- license;
- file size;
- checksum if available;
- intended use;
- whether the artifact is public or local only;
- whether it contains training data, embeddings, cached context, or private information;
- whether it belongs in Git at all.

Most large artifacts should not be committed to the public repo.

## Sensitive information

Dependency review must not reproduce secrets or private data.

If a dependency file or configuration contains secrets:

1. Stop.
2. Do not quote the secret.
3. Report the file path and the type of issue.
4. Recommend rotation if the secret was committed or exposed.
5. Escalate according to Safety Policy.

Examples of sensitive content:

```text
tokens
API keys
passwords
private URLs
internal hostnames
database credentials
personal data
customer identifiers
private package indexes with credentials
.env files
model artifacts containing private data
```

## Supply chain red flags

Escalate if you see:

- package name similar to a popular package but not the same;
- abandoned package with recent ownership change;
- unexpected install scripts;
- obfuscated source;
- minified code in non-browser packages;
- binary downloads from unknown hosts;
- broad file system access;
- broad network access;
- dependency requires admin privileges;
- dependency requests tokens during install;
- dependency with no clear license;
- dependency maintained by an unknown source but used in sensitive flow;
- package manager output that changes many unrelated packages.

## Review workflow

### Step 1: confirm mission boundaries

Identify:

```text
mission mode
allowed files
allowed commands
network permissions
public vs local scope
approval level
review level
```

If boundaries are unclear, stop and ask.

### Step 2: inventory dependency files

List relevant files and their role.

Do not inspect private directories unless allowed.

### Step 3: classify dependencies

Separate direct, transitive, runtime, development, CI, adapter, tool, and local-only dependencies.

### Step 4: identify proposed change

If reviewing a diff, state exactly what changed:

```text
added
removed
upgraded
downgraded
repinned
moved from dev to runtime
moved from local to public
```

### Step 5: assess risk

Use the risk levels in this Scroll.

State uncertainty explicitly.

### Step 6: check license and provenance

Verify source and license where feasible within mission scope.

Do not invent license status.

If license cannot be confirmed, mark as unknown.

### Step 7: check reproducibility

Check version pinning, lockfiles, CI images, Docker tags, and environment constraints.

### Step 8: check safety

Look for secrets, private URLs, dangerous install commands, external scripts, and permissions.

### Step 9: propose decision

Recommend one of:

```text
approve as-is
approve with notes
approve only as local Village dependency
request changes
block
escalate to Jounin review
escalate to Kage Summit
```

### Step 10: produce report

Provide evidence and paths. Do not include secrets.

## Output format

Use this report format:

```md
# Dependency review report

## Mission

- Mission ID:
- Repository:
- Mode:
- Reviewed by:
- Date:

## Files inspected

- `path`: reason

## Proposed dependency changes

| Dependency | Change | Role | Source | Risk | Notes |
| --- | --- | --- | --- | --- | --- |

## Lockfile impact

- Lockfiles inspected:
- Lockfiles changed:
- Unexpected changes:

## License and provenance

- Confirmed:
- Unknown:
- Blockers:

## Security and safety

- Secrets found:
- Dangerous install patterns:
- CI/CD risks:
- Network risks:
- Binary/model risks:

## Recommendation

Decision:

Reason:

Required approvals:

Required review:

## Evidence

- Command or file inspected:
- Relevant finding:

## Stop conditions triggered

- None, or list conditions.

## Follow-up

- Required:
- Optional:
```

## Approval rules

### No approval needed

No approval is normally needed to read dependency files that are already inside the approved repository scope.

### Human approval required

Human approval is required to:

- install dependencies;
- update lockfiles;
- remove dependencies;
- change dependency files;
- change CI workflows;
- change Dockerfiles;
- vendor third-party code;
- add external assets;
- add local model artifacts;
- publish dependency changes;
- use private package registries;
- run commands with network access.

### Jounin review required

Jounin review is required for:

- runtime dependencies;
- CI/CD dependency changes;
- Docker changes;
- security-related dependencies;
- dependencies that handle secrets;
- dependencies that execute shell commands;
- dependency changes in public release preparation;
- dependency changes affecting agent behavior, tools, adapters, or Scrolls.

### Kage Summit required

Kage Summit is required for:

- dependency changes that alter Academy doctrine or behavior;
- accepting an external Scroll ecosystem;
- adopting a new package manager standard;
- adding public dependency policy;
- accepting unclear license risk;
- overriding a blocked dependency decision.

## Stop conditions

Stop and ask if:

- the dependency purpose is unclear;
- the source cannot be identified;
- license is missing or incompatible;
- dependency asks for secrets;
- install scripts are suspicious;
- a command requires network access but network permission is not approved;
- a package manager wants to change many unrelated packages;
- a lockfile change cannot be explained;
- private local context appears in public dependency files;
- a CI change can access secrets;
- a Docker image or binary source is unknown;
- the requested action would modify project state but the Mission Charter is read-only.

## Violations

The following are violations:

- installing dependencies without approval;
- changing lockfiles silently;
- committing dependency changes without review;
- hiding transitive changes;
- claiming a dependency is safe without evidence;
- importing code with unclear license;
- copying private dependency config into the public repo;
- using external tools that bypass Mission Charter;
- running install scripts that were not approved;
- publishing private package names, URLs, tokens, or internal paths.

## Completion checklist

A dependency review is complete only when:

```text
[ ] Mission boundaries were checked.
[ ] Relevant dependency files were inspected.
[ ] Proposed changes were classified.
[ ] Risks were assessed.
[ ] License and provenance were checked within scope.
[ ] Lockfile impact was reviewed.
[ ] CI, Docker, tools, adapters, and Scrolls were considered when relevant.
[ ] Sensitive information was not reproduced.
[ ] Recommendation is explicit.
[ ] Required approvals are listed.
[ ] Required review level is listed.
[ ] Stop conditions are documented.
[ ] User can explain the decision.
```

## Final note

A package manager can resolve dependencies.

It cannot decide whether the dependency belongs in the mission.
