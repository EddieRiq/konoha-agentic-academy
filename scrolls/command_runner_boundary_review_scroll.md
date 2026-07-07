# Command Runner Boundary Review Scroll

Status: active review Scroll.

Use this Scroll to review any proposal that introduces command execution, command planning, shell access, task execution, or command runner behavior.

## Purpose

The Scroll protects Konoha from uncontrolled execution.

A command runner must remain bounded by Mission Charter, adapter permissions, execution gates, evidence, privacy rules, and explicit approval.

## Inputs

Review the following:

- Mission Charter;
- runtime plan;
- command runner boundary guide;
- command execution request template;
- command execution result template;
- command runner readiness template;
- adapter permission matrix;
- invocation contract;
- execution gate;
- evidence pack;
- dry-run result;
- safety policy;
- public/private boundary guide.

## Review questions

### Authority

- Does the Mission Charter explicitly allow command execution?
- Who approved the execution or implementation?
- Is the approval scoped and current?
- Is technical capability separated from authorization?

### Command scope

- Is the exact command known?
- Is the working directory explicit?
- Are target paths explicit?
- Are blocked paths explicit?
- Are private paths involved?

### Risk

- Is the command read-only, mutating, networked, Git-related, release-related, or destructive?
- Is the risk level accurate?
- Does the command need dry-run evidence?
- Does the command need rollback notes?

### Privacy

- Could command output expose secrets, paths, private content, logs, credentials, or local memory?
- Could the command cross from private Village paths into public repo paths?
- Could ignored files be staged, copied, summarized, or published?

### Git and release

- Does the command stage, commit, tag, push, publish, clean, reset, or release?
- Is Git/release authorization explicit?
- Is there a final safety audit before release operations?

### Evidence

- Is pre-execution evidence present?
- Is expected output defined?
- Is post-execution reporting defined?
- Is Git status evidence required before and after?
- Is result acceptance separated from command execution?

## Required verdicts

Choose one:

- Pass: boundary is respected.
- Pass with notes: safe, but documentation should improve.
- Needs changes: missing scope, evidence, or approval.
- Blocked: execution boundary is unsafe or unauthorized.

## Stop conditions

Block if:

- command execution is implied but not authorized;
- exact command is missing;
- path scope is ambiguous;
- private context may be exposed;
- Git or release operations are requested without explicit approval;
- destructive commands are requested without high-confidence approval;
- rollback is missing for state-changing commands;
- dry-run evidence is missing when required;
- output handling is undefined;
- implementation grants autonomous command execution.

## Output

The review must state:

- what was reviewed;
- verdict;
- command categories involved;
- allowed scope;
- blocked scope;
- required evidence;
- unresolved risks;
- required approvals before proceeding.

## Rule

Command runners execute only inside approved boundaries.

They do not infer permission from user intent, adapter confidence, model recommendation, or technical capability.
