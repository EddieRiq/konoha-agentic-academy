# Konoha Capability Matrix

This matrix summarizes what Konoha Agentic Academy supports at v1.0.0.

| Capability | v1.0.0 status | Boundary |
|---|---:|---|
| Mission Charter doctrine | Supported | Required before execution-style workflows |
| Dry-run runtime packages | Supported | Validated before use |
| Runtime package validation | Supported | Read-only |
| Runtime package inspection | Supported | Read-only |
| Sandbox run preparation | Supported | Sandbox-only |
| Dry-run runtime runner | Supported | No mission execution |
| Run registry | Supported | Read-only |
| Public repo inspection | Supported | Read-only |
| Controlled artifact writing | Supported | Sandbox proposed outputs only |
| Apply plan preview | Supported | Preview by default |
| Approved apply to allowlisted paths | Supported | Human token required |
| Git readiness inspection | Supported | Read-only |
| Git staging gate | Supported | Explicit approval required |
| Git commit gate | Supported | Already staged allowlisted files only |
| Integrated smoke tests | Supported | Delegated safe checks |
| Mock adapter | Supported | Deterministic, local-only |
| Adapter invocation gate | Supported | Real adapters blocked by default |
| Dogfood mission suite | Supported | Final pre-release evidence |
| Real adapter execution | Not supported by default | Blocked |
| Autonomous shell execution | Not supported | Blocked |
| Autonomous Git push | Not supported | Blocked |
| Private context access by default | Not supported | Blocked |
| Network access | Not supported by runtime gates | Blocked |
| Background autonomous missions | Not supported | Blocked |

## v1.0 interpretation

v1.0.0 is a stable safe local-first dry-run runtime. It is not a fully autonomous agent platform.

The system is stable when:

- the command surface is understandable;
- evidence is generated before action;
- sandbox boundaries are preserved;
- approval tokens are required for sensitive transitions;
- real adapters remain disabled by default;
- Git write actions remain gated;
- release readiness can be checked repeatably.
