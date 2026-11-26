# Addendum 2c: single-source terms set aside (decision 57 item 1)

Written 2026-11-26 from 10:55 UTC (from `date -u`) by the step-2 cross-reviewer, a model agent working for the project
lead (not a person).

**Written from the literature only, blind to the corpus; no count has been made.**

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The rule

Citations of published works are not creator identifiers. They stay in the register and lists. But a counted term
whose only source is a work by an author or organisation that the project's public site also lists as a channel or
person is **set aside from every count**, because a count of it could approximate one channel's own usage. A term with
at least one independent other source stays counted. A project document cited only for class definitions is not an
independent source.

## What it changes

- **7 counted terms** are set aside (`addendum-2c-register.csv`).
- The affected list files are regenerated as "-a2c" in `lists/`. The crosswalk and the balance file are regenerated
  beside them. Each marks the terms in column `set_aside_a2c`, and column `counted_after_all_set_asides` combines this
  set-aside with the trope set-aside of decision 51 L1.
- No term, form, source or citation is removed from any file.

**Which version binds.** For each list, the "-a2c" file binds if there is one, then the "-a2b" file, then the "-a2"
file, then the original.
