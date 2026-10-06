# Operating notes for Claude sessions started here

The owner starts sessions in this repository, from an iPhone. Most of those
sessions are about the StegVerse ecosystem, not genealogy. Read this first.

## Work from the registries, not from chat

The owner built these so they do not have to coordinate sessions by hand. Use
them before doing anything else.

1. **Read the active goal and the task registry**:
   `StegVerse-org/.github` → `orchestration/task-registry.json` (`active_goal`,
   `tasks`). It is public, so read it with an anonymous clone; no attach is needed.
2. **Work only under a registered task.** Find the task the request belongs to
   and use its `task_id`. If none fits, say so and propose the task record
   (id, objective, owning repository) before starting. Never do untracked work.
3. **Title the session `TASK-ID · repository · purpose`**, using
   `set_session_title`, as soon as the task is known. Prefix it `DONE ·` when
   finished, and `NEEDS YOU ·` when blocked on the owner. A title that does not
   say the task makes the session impossible for the owner to track.
4. **Record the outcome on the task, not only in chat**: what was merged (PR
   links), what is blocked and on whom. The next session reads the registry,
   not this conversation.
5. **Before starting work, check the other open sessions** (`list_sessions`). If one
   already owns the task, continue there instead of starting a parallel attempt.

## One thread of work

- Attach repositories to this session with `add_repo` instead of opening a session per
  repository.
- **Exception:** repositories whose names begin with `.` (every org's `.github`)
  cannot be attached mid-session. The tool refuses the leading dot. Writing to one
  needs a session started with it as a source. When that happens, start one
  child session, give it a single bounded task, and archive it when it finishes.
  Never leave finished sessions open.
- Keep attachment bounded, as `StegVerse-org/.github/CLAUDE.md` describes.

## Where authority lives

| Surface | Governs |
| --- | --- |
| `StegVerse-org/.github` | Task registry, org transition ledger, resident runtime, Interlock/InTr boundary, and its own `CLAUDE.md` |
| `StegVerse-Labs/repo-standards` | ST-001…ST-020: repo layout, preflight, naming, validation |
| `StegVerse-Labs/StegDB` | Architecture canon (`stegverse.architecture.json`) |
| `StegVerse-org/StegVerse-SDK` | The `stegverse` package and the manifest builder |

Do not invent a local convention when one of these surfaces already defines it.

## Rules the owner has stated

- **The manifest directs the whole path.** Nothing fills in what the manifest
  does not declare.
- **Crossing from one org to another calls the receiving org's InTr endpoint**, in that
  org's `.github`, once per manifest.
- **Org records only.** Decisions are recorded in the organization's own ledgers,
  never in Master Records.
- **No experiment-specific code.** An experiment is a manifest's parameters. Its
  data lives only in the org receipts its runs produce.
- Open PRs **ready for review, never draft**, and never merge or close them.
- Report in chat, briefly. The owner reads on a phone.
