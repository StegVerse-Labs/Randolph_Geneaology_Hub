# Registered Namespaces

Every Canonical ID (`<NS>-<BirthYear>-<Sequence>-<BirthState>`) starts
with a namespace: a short code identifying which family line it belongs
to. This file is the registry of which namespaces **this repository** is
authoritative for. `tools/validate_ledger.py` enforces it: any
`Individuals/*.md` file whose `Canonical_ID` uses a namespace not listed
below fails validation.

## Issued in this repository

| Namespace | Family |
|---|---|
| `RND` | Randolph |
| `LND` | Lindley (connects into the Randolph line via marriage — see `LND-1885-001-MN`) |

## Forking this hub for your own family

The CID format, evidence grading, schema, and Claims/corroboration
tooling in this repository are family-agnostic — see
[`docs/start.md`](docs/start.md) for the full walkthrough. In short:

1. Fork this repository.
2. Pick a namespace for your family: 2–4 uppercase letters, not already
   listed above (that constraint only matters if you're extending *this*
   repo rather than forking it — a fresh fork can reuse any namespace,
   including `RND`, since it's a separate ledger).
3. Replace the table above with your own namespace(s).
4. Start adding `Individuals/` records or `Claims/` under your namespace.
   `tools/validate_ledger.py` will fail closed on anything using a
   namespace you haven't registered here — that's what stops a stray
   typo or an accidental cross-family reference from entering your ledger
   unnoticed.

## Adding a second family to *this* repository

This repo could also grow a second namespace directly (e.g. through
marriage into another documented line) rather than living only in a
fork. Register it in the table above in the same PR that adds its first
`Individuals/` record.
