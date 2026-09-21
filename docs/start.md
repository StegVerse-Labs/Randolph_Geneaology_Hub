---
layout: default
title: Start Your Own Genealogy Hub
---

# Start Your Own Genealogy Hub

This project is a template, not a Randolph-only tool. The Canonical Identity
(CID) format, evidence grading, schema, and privacy rules in `Standards/`
are family-agnostic — the `RND`/`LND` namespaces are just this family's.

## Quick start

1. **Fork this repository.**
2. Pick a namespace for your family (three letters, e.g. `SMT` for Smith).
   Register it at the top of your own `CID_Index_Master.md`.
3. Read `Standards/Schema_v1.md` and `Standards/Evidence_Grading.md` before
   adding anyone — every lineage link needs a `Source_ID` and an evidence
   grade of A–C (never D alone).
4. Add your first Individual under `Individuals/<NS>-<BirthYear>-<Sequence>-<BirthState>__Name.md`,
   following the structure in an existing file (e.g. `Individuals/RND-1796-001-TN__Ruben_Randolph.md`).
5. Register the CID in `CID_Index_Master.md` before referencing it anywhere
   else — this is what keeps every parent/child link resolvable.
6. Read `Standards/Living_Persons_Privacy_Protocol.md` before adding anyone
   who might still be alive.

## Longer walkthrough

A printable version of this guide is in
[`assets/Start_Your_Own_Family_Hub.pdf`](assets/Start_Your_Own_Family_Hub.pdf).

## Where this is headed

See [`MYKV_SERVICE_DESIGN.md`](MYKV_SERVICE_DESIGN.md) for the plan to make
multi-family use and corroboration-based confirmation a first-class part of
this project instead of something you have to reinvent per fork.
