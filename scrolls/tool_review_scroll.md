# Tool review scroll

## Status

Draft.

## Purpose

This Scroll defines a safe review workflow for tools used by Konoha Agentic Academy.

A tool is any helper script, CLI command, local utility, workflow helper, model router, sanitizer, notifier, context pack builder, or automation that assists a mission.

Tools may support agents.

Tools do not become agents.

Tools do not grant authority.

## Core rule

Tools assist mission execution.

They may not authorize actions, expand scope, modify doctrine, access private context, store sensitive content by default, bypass review, or override the Mission Charter.

## When to use this Scroll

Use this Scroll when reviewing:

- tools in `tools/`;
- helper scripts proposed by agents;
- local utilities used by an Allied Village;
- context scoring tools;
- notification tools;
- budget or model routing tools;
- report sanitizers;
- memory helpers;
- learning merge helpers;
- code generation helpers;
- shell scripts;
- Python scripts;
- Git helpers;
- automation wrappers;
- tools imported from external repositories.

Use this Scroll before marking a tool as trusted, active, recommended, or safe for repeated use.

## What this Scroll is not

This Scroll is not:

- permission to run a tool;
- permission to install dependencies;
- permission to modify files;
- permission to access private paths;
- permission to read secrets;
- permission to publish outputs;
- a security audit certification;
- a replacement for Jounin review;
- a replacement for dependency review;
- a replacement for sensitive data review.

## Required inputs

Before reviewing a tool, collect:

```text
Tool name:
Tool path:
Tool owner:
Tool status:
Intended use:
Mission or workflow where it is used:
Inputs:
Outputs:
Files it reads:
Files it writes:
Commands it runs:
Network access:
Dependencies:
Sensitive data risk:
Current trust level:
Requested trust level:
```

If any critical field is unknown, mark it as unknown.

Do not infer permissions from intent.

## Review modes

### Mode 1: read-only tool review

Allowed by default when the Mission Charter permits repository inspection.

The reviewer may:

- read the tool source;
- inspect documentation;
- inspect declared inputs and outputs;
- inspect dependency references;
- inspect example usage;
- inspect tests;
- inspect logs if explicitly provided;
- produce a review report.

The reviewer may not:

- execute the tool;
- install dependencies;
- modify the tool;
- modify configuration;
- access local private paths;
- access secrets;
- publish results.

### Mode 2: dry-run review

Requires explicit approval in the Mission Charter.

The reviewer may run the tool only if:

- dry-run mode exists;
- inputs are synthetic or approved;
- outputs go to a sandbox or temporary path;
- no network access is used unless explicitly allowed;
- no secrets are required;
- logs are sanitized.

### Mode 3: execution review

Requires explicit human approval.

The reviewer may run the tool against real context only when:

- the Mission Charter names the exact tool;
- allowed paths are listed;
- allowed commands are listed;
- expected outputs are listed;
- rollback or cleanup steps are clear;
- required review level is defined;
- sensitive data handling is explicit.

## Tool authority check

For every tool, answer:

```text
Does the tool approve anything?
Does the tool modify doctrine?
Does the tool expand mission scope?
Does the tool choose actions without a Mission Charter?
Does the tool read private context by default?
Does the tool write memory by default?
Does the tool send data externally?
Does the tool modify Git history?
Does the tool execute shell commands?
Does the tool call other tools?
Does the tool hide outputs or errors?
```

Any "yes" requires review.

Some "yes" answers may block activation.

## Allowed behavior

A well-behaved tool may:

- transform explicitly provided input;
- validate structure;
- summarize allowed context;
- check for missing fields;
- detect risky patterns;
- generate reports;
- prepare draft files in a sandbox;
- create candidate outputs for review;
- notify that human input is needed;
- estimate token or cost usage;
- route work according to approved constraints;
- assist learning proposals without promoting doctrine.

## Prohibited behavior by default

A tool must not, by default:

- approve missions;
- approve file changes;
- approve doctrine changes;
- decide mission scope;
- read files outside allowed paths;
- inspect local machines;
- read `.env` files;
- read credentials;
- print secrets;
- store sensitive content;
- send data to external services;
- install packages;
- change Git remotes;
- commit;
- amend commits;
- push;
- force-push;
- delete files;
- delete branches;
- modify ignored Local Village content;
- modify Academy doctrine;
- silently rewrite outputs;
- hide failures;
- mark work complete.

## Inputs review

Inspect all inputs.

Check:

- whether inputs are explicit or inferred;
- whether inputs may contain sensitive data;
- whether input paths are restricted;
- whether wildcards are used safely;
- whether recursive reads are bounded;
- whether binary files are handled safely;
- whether large files are handled intentionally;
- whether unsupported inputs fail clearly.

Risk signs:

```text
Reads entire repo without filters.
Reads home directory.
Reads Downloads/Desktop/Documents by default.
Reads all Markdown files recursively without scope.
Reads `.env`, `.ssh`, `.aws`, `.config`, browser profiles, tokens, logs, or caches.
Accepts remote URLs without validation.
Accepts shell fragments as input.
```

## Outputs review

Inspect all outputs.

Check:

- where outputs are written;
- whether outputs overwrite files;
- whether output paths are derived safely;
- whether temporary files are cleaned up;
- whether sensitive content is redacted;
- whether reports separate facts from assumptions;
- whether generated Markdown is reviewable;
- whether output names are deterministic enough for traceability.

Risk signs:

```text
Writes directly to final paths.
Overwrites without confirmation.
Creates files outside the repo.
Writes to ignored private folders.
Stores raw private context.
Stores full transcripts by default.
Stores credentials in logs.
```

## Command review

If the tool runs commands, list every command.

Classify each command:

```text
Read-only:
State-changing:
Network:
Dependency install:
Git history-changing:
Destructive:
External publication:
Unknown:
```

Examples of sensitive commands:

```bash
git add
git commit
git commit --amend
git push
git push --force
git push --force-with-lease
git reset
git clean
git rebase
rm
mv
chmod
chown
pip install
npm install
curl
wget
ssh
scp
docker run
docker compose up
```

Sensitive commands require explicit approval.

Destructive commands require stronger approval or should be blocked.

## Network review

If the tool uses network access, identify:

```text
Destination:
Protocol:
Data sent:
Data received:
Authentication:
Logs:
Retry behavior:
Timeouts:
Failure behavior:
```

Network access is blocked by default unless the Mission Charter explicitly allows it.

External APIs must not receive private context unless explicitly approved.

## Dependency review

For each dependency, check:

- package name;
- source;
- version pinning;
- license;
- install method;
- runtime permissions;
- known alternatives;
- whether dependency is necessary;
- whether it introduces network behavior;
- whether it executes code at install time.

If dependency risk is non-trivial, invoke `dependency_review_scroll.md`.

## Sensitive data review

Inspect whether the tool may touch:

- credentials;
- tokens;
- `.env` files;
- private keys;
- personal data;
- customer data;
- internal company data;
- local project context;
- Local Village memory;
- raw transcripts;
- logs;
- screenshots;
- model artifacts;
- data extracts.

If any are possible, invoke `sensitive_data_review_scroll.md`.

## Local Village review

For tools used inside an Allied Village:

- local rules apply;
- local context stays local by default;
- local assets are not public by default;
- local memory is not Academy memory;
- local tool behavior must not leak private context into the public repo.

A tool may be useful locally and still be unsafe for public Academy activation.

## Logging review

Logs must be useful and safe.

Check that logs:

- show what happened;
- show paths without exposing sensitive values;
- avoid credentials;
- avoid raw private data;
- distinguish info, warning, and error;
- preserve enough evidence for review;
- do not claim success without validation.

Bad logging:

```text
print(connection_string)
print(os.environ)
print(full request payload with personal data)
print(raw private memory)
print(secret token)
```

## Error handling review

A safe tool should:

- fail closed;
- show actionable error messages;
- avoid silent fallback;
- avoid guessing missing paths;
- avoid continuing after critical validation failure;
- return non-zero exit codes when appropriate;
- preserve debug evidence safely.

Risk signs:

```text
except Exception: pass
auto-fixes errors without reporting
continues when config is missing
creates defaults that change behavior
falls back to broad paths
```

## Tests and examples

A tool should include, when practical:

- example command;
- expected input;
- expected output;
- dry-run example;
- failure example;
- minimal test;
- edge case test;
- sensitive data redaction test.

Lack of tests does not automatically block a low-risk tool, but it limits trust level.

## Trust levels

### Unreviewed

Default status.

The tool exists but should not be used for real work.

### Reviewed

Source and documentation were reviewed.

Execution may still be blocked.

### Tested

The tool passed safe dry-run or sandbox tests.

### Active

The tool is allowed for specific approved workflows.

Activation requires Jounin review if the tool can affect files, memory, Git, dependencies, network, private context, or doctrine-adjacent outputs.

### Deprecated

The tool should not be used for new missions.

### Blocked

The tool is unsafe or violates Academy policy.

## Review checklist

Before recommending a tool, confirm:

```text
[ ] Purpose is clear.
[ ] Inputs are explicit.
[ ] Outputs are explicit.
[ ] Read paths are bounded.
[ ] Write paths are bounded.
[ ] Sensitive data behavior is clear.
[ ] Network behavior is clear.
[ ] Dependencies are clear.
[ ] Commands are clear.
[ ] Error handling is safe.
[ ] Logs are safe.
[ ] Tool does not grant authority.
[ ] Tool does not bypass Mission Charter.
[ ] Tool does not modify doctrine.
[ ] Tool does not access private context by default.
[ ] Tool does not publish data externally by default.
[ ] Required review level is defined.
```

## Tool review report

Use this structure:

```markdown
# Tool review report

## Tool

Name:
Path:
Requested trust level:

## Summary

Short description of what the tool does.

## Verdict

Status: unreviewed | reviewed | tested | active | deprecated | blocked

Reason:

## Evidence reviewed

- Files:
- Commands inspected:
- Tests inspected:
- Documentation inspected:

## Inputs

Allowed inputs:
Risky inputs:
Unknown inputs:

## Outputs

Expected outputs:
Write paths:
Overwrite behavior:

## Commands

Read-only commands:
State-changing commands:
Network commands:
Destructive commands:

## Dependencies

Dependencies:
Version pinning:
License notes:
Risk notes:

## Sensitive data risk

Risk level:
Sensitive paths:
Redaction behavior:
Required restrictions:

## Safety findings

Finding 1:
Finding 2:

## Required changes

- Change 1
- Change 2

## Approved usage

Only if status allows it.

Allowed missions:
Allowed paths:
Allowed commands:
Required review:

## Stop conditions

- Condition 1
- Condition 2
```

## Activation rules

A tool may be marked active only when:

- purpose is clear;
- allowed use is narrow;
- sensitive behavior is known;
- commands are known;
- dependencies are known;
- failure behavior is acceptable;
- review level is satisfied;
- the user or authorized maintainer approves activation.

A tool cannot become active merely because it works once.

## Violations

A tool violates this Scroll if it:

- exceeds declared scope;
- reads private context without permission;
- writes files without permission;
- sends data externally without permission;
- modifies Git without permission;
- stores sensitive content by default;
- hides failures;
- grants authority;
- rewrites doctrine;
- bypasses review;
- claims completion without evidence.

Violations must be reported.

Unsafe tools must be blocked or quarantined.

## Related doctrine

- `tools/README.md`
- `adapters/README.md`
- `sandbox/README.md`
- `marketplace/README.md`
- `protocols/safety/safety_policy.md`
- `protocols/context/context_policy.md`
- `protocols/approval/approval_policy.md`
- `protocols/review/review_policy.md`
- `scrolls/dependency_review_scroll.md`
- `scrolls/sensitive_data_review_scroll.md`
- `scrolls/local_context_scroll.md`
- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
