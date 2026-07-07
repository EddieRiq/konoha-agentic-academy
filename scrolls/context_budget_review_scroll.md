# Context Budget Review Scroll

Status: documentation-first Scroll.

Use this Scroll to review whether a mission loads the minimum safe amount of context.

## Purpose

This Scroll prevents agents from loading excessive Markdown instructions, private context, or irrelevant source files.

It also prevents unsafe under-loading when full source is required.

## Inputs

- Mission Charter;
- context budget;
- context capsules;
- source file list;
- role policy;
- relevant safety or permission policy;
- token budget.

## Review questions

### Context necessity

- Is each context source necessary?
- Can a validated capsule replace a full-source read?
- Is any required source missing?
- Are irrelevant guides excluded?

### Capsule safety

- Are capsules current?
- Are source hashes present?
- Are full-source triggers clear?
- Are capsule limitations stated?

### Full-source requirement

Full source is required for:

- doctrine changes;
- safety conflicts;
- permissions;
- private context;
- release readiness;
- runtime or adapter boundaries;
- ambiguous instructions;
- stale or missing capsule hashes.

Check whether the mission correctly identifies these cases.

### Token control

- Is intake budget stated?
- Is there a hard stop threshold?
- Is there a plan if source load exceeds budget?
- Is the mission split when needed?

### Privacy

- Does the context include private Village files?
- Is private access explicitly authorized?
- Are local memory and private literature excluded by default?

## Verdicts

### Pass

Context budget is safe and sufficient.

### Pass with notes

Context budget is acceptable with monitoring.

### Needs changes

Context budget should be narrowed, expanded, or clarified.

### Blocked

Context budget risks privacy, safety, or correctness.

## Required output

A review must state:

- verdict;
- approved context mode;
- allowed capsules;
- allowed source files;
- excluded paths;
- full-source triggers;
- token limit;
- stop conditions.

## Stop conditions

Stop if:

- context budget is missing;
- private context is included without approval;
- capsule is stale and source is required;
- token budget is clearly unrealistic;
- the mission asks to load everything by default.
