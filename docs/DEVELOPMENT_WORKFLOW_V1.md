# DEVELOPMENT_WORKFLOW_V1

## Purpose

This document defines the mandatory development workflow for `workspace_ai_agent` and its integration with `workspace_ai_agent_web`.

## Repository boundaries

### `workspace_ai_agent`

This repository is the Agent/Core system and its PostgreSQL-backed domain. For Web integration work, it is treated as **read-only unless the user explicitly authorizes a change**.

Do not add, remove, or modify Agent code, database schema, migrations, APIs, authentication behavior, or documentation without explicit approval.

### `workspace_ai_agent_web`

This repository is the Web/Laravel implementation surface. Web changes must integrate with the existing Agent contracts rather than silently changing the Agent repository.

## Mandatory workflow

Every material change follows this order:

1. **Analyze**
   - Inspect the current code, database/schema contracts, APIs, configuration, tests, and relevant documentation.
   - Identify repository boundaries and dependencies before changing anything.

2. **Implement on GitHub**
   - Make the approved code change in the appropriate repository/branch.
   - Do not modify the other repository merely to make a test pass.

3. **Synchronize documentation**
   - Update the relevant documentation in the same change when behavior, architecture, API, configuration, security, database, or operational procedures change.
   - Documentation must describe the implementation that is actually committed, not a planned future state.

4. **Report GitHub state to the user**
   - Clearly identify repository, branch, commit, and the files/behavior changed.
   - Explicitly state: **GITHUB UPDATED — PULL TO LOCAL BEFORE TESTING.**

5. **Pull to local**
   - The user synchronizes the changed branch to the local working copy.
   - Do not treat a GitHub change as locally tested until the user has pulled/fetched the corresponding commit.

6. **Local verification**
   - Confirm branch and commit.
   - Inspect `git status` and the relevant diff.
   - Install/update dependencies only when required.
   - Apply migrations/configuration only when required and only after checking their impact.
   - Run the relevant unit, integration, smoke, API, browser, or end-to-end tests.

7. **Verify and report**
   - Report the exact commit tested locally, commands run, test results, failures, and known limitations.
   - Do not claim a feature is complete merely because it exists on GitHub.

8. **Close / Chốt**
   - A change is `FINAL` only after the implementation is documented and the corresponding local verification has passed, or the user explicitly accepts a documented exception.

## Status lifecycle

Use these states for material work:

- `PROPOSED` — design/analysis only.
- `IMPLEMENTED_GITHUB` — code committed on GitHub; not locally verified.
- `LOCAL_VERIFIED` — corresponding commit pulled and tests passed locally.
- `FINAL` — implementation, documentation, and verification are complete.
- `BLOCKED` — verification or an architectural dependency prevents completion.

## Database and authentication safety

- Never introduce a second source of truth for Agent users without explicit approval.
- Never create a local SQLite authentication database for the Web project when the approved architecture requires Agent PostgreSQL/API contracts.
- Do not copy Agent users into a Web-only credential table unless explicitly approved.
- Do not bypass an Agent API/security boundary by modifying the Agent repository merely to simplify Web implementation.

## Change discipline

Before each change, state which repository is being modified and why. If a requirement cannot be implemented without changing the other repository, stop and request approval instead of making the change implicitly.

## Definition of done

A change is considered done only when:

- the correct repository was changed;
- repository boundaries were respected;
- relevant docs were synchronized;
- the user was told to pull the GitHub commit;
- the corresponding commit was tested locally;
- test results and limitations were recorded; and
- the user explicitly accepts any remaining exception.
