# MCP SOP

MCP provides live tools; skills define how those tools are used. A connector being installed does not authorize every mutation.

## Approved capability classes

### Google Drive

Purpose: discover and read shared project documents; refresh the curated repo knowledge snapshot. Drive writes are outside the default workflow and require a separately approved plan.

Minimum permissions: read-only access to the TimeShuttler folder. Prefer file IDs from `Docs/Knowledge/source-manifest.yaml` over broad searches.

### Unreal Editor

Purpose: inspect Blueprint graphs/assets and, after approval, perform editor-aware changes, compile, save, run PIE, and collect evidence.

The team has not yet selected a canonical Unreal MCP server. Do not commit guessed server commands, ports, packages, or credentials. When one is selected, record the implementation, version, owner, transport, allowed tools, install steps, and health check in the registry below.

## Per-session preflight

1. Enumerate the tools actually exposed by the connector/server.
2. Confirm the target project/editor instance and UE 5.6 version.
3. Start read-only: query asset metadata, references, graph structure, or logs.
4. Map each proposed action to a real discovered tool. Never invent tool names.
5. Classify tools as read-only, mutating, destructive, or external-write.
6. Obtain approval through `Docs/Agent/approval-gate.md` before invoking mutating tools.
7. Use the narrowest tool and target. Re-read/compile after writes and preserve evidence.

## Unreal mutation rules

- Do not modify raw `.uasset`/`.umap` bytes or use filesystem copy tricks as an editing API.
- Prefer asset-specific/editor APIs. Use Unreal Python only inside the editor and only when the approved MCP path can execute and observe it safely.
- Avoid broad “save all” operations. Save only approved assets.
- Treat rename/move/delete, redirector fix-up, level saves, World Partition changes, plugin enablement, and project-wide resaves as high blast-radius operations requiring explicit mention in the proposal.
- Stop on compile errors, unexpected dirty assets, editor modal dialogs, lost connection, or target mismatch.

## Connector registry

| Capability | Implementation | Version | Access | Owner | Health check | Status |
|---|---|---|---|---|---|---|
| Google Drive | Codex Google Drive connector | Managed | Read-first | Team producer | List root folder by ID | In use |
| Unreal Editor | To be selected | Pin exact version | Least privilege | Tech owner | Read project + compile disposable/test asset | Blocked pending decision |

## Failure and recovery

- If discovery/authentication fails, do not substitute web search for private project documents.
- If the Unreal connection drops during a write, stop, inspect editor state manually, identify dirty assets, and do not blindly retry.
- If a tool reports success without verifiable editor state, treat the result as unverified.
- Never place tokens or credentials in the repo. Use each teammate's approved local secret/config mechanism.
