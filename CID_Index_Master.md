# Randolph CID Master Index

This file lists every Canonical Identity ID issued in the ledger.

---

## Issued CIDs

This list is generated from `Individuals/*.md` — do not hand-edit it.
Run `python3 tools/validate_ledger.py --write` after adding or changing an
Individuals/ file to regenerate it, then commit the result.

<!-- BEGIN GENERATED: tools/validate_ledger.py -->
LND-1727-001-NJ – Caleb Lindley Sr
LND-1765-001-NJ – Naphtali Lindley
LND-1791-001-PA – Josephus Lindley
LND-1819-001-PA – Isaac Chandler Lindley
LND-1885-001-MN – Lucy Ann Lindley Jones
RND-c1760-001-VA – Peyton Randolph Sr.
RND-1796-001-TN – Ruben Randolph
RND-1827-001-TN – Isaac Randolph
RND-1829-001-TN – Elijah Randolph
RND-1832-001-TN – Chisum Randolph
RND-1835-001-TN – Mary Ann Randolph
RND-1835-002-TN – Jasper Randolph
RND-1840-001-TN – Elizabeth Randolph
RND-1840-002-TN – Leann Randolph
RND-1842-001-TN – Henry Randolph
RND-1850-001-TN – Margaret Randolph
RND-1853-001-MO – Elijah Randolph
RND-1875-001-IN – Benjamin Franklin Randolph
RND-1900-UNK-OR – Robert Randolph
RND-1909-001-OR – Jack Lindley Randolph
<!-- END GENERATED -->

---

## Rules

- No CID may be reused.
- No CID may be altered once assigned.
- Every CID's namespace must be registered in [`NAMESPACES.md`](NAMESPACES.md) —
  `tools/validate_ledger.py` fails closed on any that isn't.
- A new individual is registered by adding an `Individuals/*.md` file (or a
  confirmed `Claims/` submission — see `Claims/README.md`) and running
  `python3 tools/validate_ledger.py --write`, not by editing the list above
  directly.

---

Ledger Integrity Status: Stable
