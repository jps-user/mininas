# MiniNAS Design Philosophy

> **Modern Linux File Sharing for Webmin**
>
> *The power of Linux. The simplicity of a NAS.*

---

# Philosophy

MiniNAS is a lightweight extension for Webmin that simplifies Linux file sharing administration.

MiniNAS does not replace Linux.

MiniNAS does not replace Samba.

MiniNAS does not replace Webmin.

MiniNAS builds upon them.

Its purpose is simple:

> **Reduce administrative complexity without reducing Linux transparency.**

MiniNAS respects the Unix philosophy:

> **Use existing tools. Connect them through better workflows.**

---

# Why MiniNAS Exists

Linux file sharing is built from many small, independent components.

Each component has a clear responsibility.

Together they provide a powerful and flexible file server.

However, the administrator is responsible for connecting those components correctly.

Creating a single file share may involve:

- creating a Linux user
- creating a Samba user
- creating a directory
- assigning ownership
- assigning filesystem permissions
- configuring Samba permissions
- editing the Samba configuration
- validating the configuration
- reloading the Samba service

Every individual step is simple.

The workflow is not.

MiniNAS does not simplify Linux.

MiniNAS simplifies Linux file sharing administration.

---

# Design Goals

## One Administrative Task → One Workflow

MiniNAS is designed around administrative tasks.

Administrators think in tasks.

Linux works in components.

MiniNAS connects both worlds.

Creating a new share should require one workflow.

Not multiple administration modules.

---

## Reduce Context Switching

Common administration tasks should never require jumping between multiple Webmin modules.

MiniNAS groups related actions into one coherent workflow.

The administrator should not need to remember:

- where Linux users are managed
- where Samba users are created
- where directories are created
- where permissions are assigned
- where shares are configured
- when services must be reloaded

MiniNAS understands the workflow.

Linux remains transparent.

---

## Reduce Complexity

MiniNAS reduces administrative complexity.

It never reduces Linux functionality.

Every advanced capability remains available through:

- Webmin
- Terminal
- Standard Linux tools
- Samba configuration

MiniNAS removes repetitive work.

It never hides the system.

---

# Core Principles

## 1. Linux First

Linux remains the foundation.

MiniNAS builds upon standard Linux tools and services.

It never replaces them.

It never hides them.

The operating system always remains fully accessible.

---

## 2. Webmin First

Webmin remains the primary administration platform.

MiniNAS extends Webmin by simplifying common workflows.

Everything outside the scope of MiniNAS remains available through existing Webmin modules.

---

## 3. Build, Don't Replace

MiniNAS builds upon existing Linux tools and existing Webmin functionality.

Whenever possible, MiniNAS orchestrates existing components instead of creating new implementations.

MiniNAS is an orchestration layer.

Not a replacement layer.

---

## 4. Single Source of Truth

The Samba configuration remains the only source of truth.

MiniNAS never creates:

- proprietary configuration files
- databases
- hidden metadata

Everything remains standard Linux.

---

## 5. Preserve Administrator Changes

MiniNAS never rewrites the complete Samba configuration.

Only the selected configuration section is modified.

Everything else remains untouched.

Including:

- comments
- formatting
- blank lines
- unknown Samba parameters
- administrator customizations

The administrator always owns the configuration.

---

## 6. No Vendor Lock-in

Everything created by MiniNAS remains standard Linux.

MiniNAS can be removed at any time.

The server continues operating normally using standard Linux tools.

---

## 7. Workflow over Components

MiniNAS is designed around workflows.

Not around Linux components.

The administrator performs one logical task.

MiniNAS performs the required system operations.

**Test:** if completing a task requires the administrator to remember an extra manual step — choosing a filesystem action, running a separate command, switching to another tool — the workflow is incomplete. A workflow is only finished when the predictable consequences of an action happen automatically, not when they are offered as an option the administrator must remember to select.

---

## 8. Modern User Experience

Modern does not mean heavy.

MiniNAS favors:

- dashboards
- cards
- clear typography
- icons
- visual hierarchy
- concise dialogs
- consistent spacing

The interface should simplify administration.

Not distract from it.

The purpose of this effort is not decoration. It exists so the administrator can find what they need without thinking about it, recognize state at a glance, and feel immediately at home in the interface — even after time away from it. A well-designed dashboard reduces cognitive load the same way a well-designed workflow reduces manual steps. Visual clarity is a form of simplicity, not an exception to it.

---

## 9. Boring Technology

MiniNAS intentionally uses proven technology.

- Perl
- CGI
- HTML
- CSS
- Vanilla JavaScript

No unnecessary frameworks.

No unnecessary dependencies.

Long-term maintainability is preferred over fashionable technology.

---

## 10. Zero Additional Infrastructure

MiniNAS introduces:

- no daemon
- no scheduler
- no database
- no background services

Every request is processed on demand.

Nothing runs permanently.

---

## 11. Lightweight by Design

MiniNAS should remain as lightweight as Webmin itself.

Additional usability should require minimal additional resources.

---

## 12. Respect Sleeping Disks

MiniNAS avoids unnecessary filesystem activity.

Storage devices should remain in standby whenever possible.

Operations that may wake storage devices should only be executed when explicitly requested by the administrator.

---

## 13. Security First

Every modification must:

- validate user input
- create a backup
- write atomically
- validate the configuration
- rollback on failure

Configuration integrity always comes first.

Every rollback must state clearly what failed and why — not just that it failed. A silent or generic rollback erodes trust in the exact moment the safeguard is protecting the administrator.

---

## 14. Human Readable Errors

MiniNAS explains problems.

It never exposes meaningless error codes.

Errors should help administrators understand and resolve the issue.

---

## 15. Predictable Behaviour

MiniNAS should never surprise administrators.

Every action must be:

- visible
- understandable
- predictable
- reversible

Trust is built through consistency.

---

## 16. Small Scope

MiniNAS has a clearly defined responsibility.

MiniNAS simplifies Linux file sharing administration.

Nothing more.

Focused software remains maintainable.

---

## 17. Separation of Responsibilities

MiniNAS is responsible for:

- Linux file sharing workflows
- Samba administration
- Linux users required for file sharing
- Samba users
- Shares
- Filesystem permissions
- Samba permissions

MiniNAS is not responsible for unrelated services or applications.

It prepares storage.

Other software consumes storage.

A clear separation of responsibilities keeps MiniNAS simple, maintainable and predictable.

---

## 18. Unix Philosophy

Do one thing.

Do it well.

MiniNAS exists to simplify Linux file sharing administration.

Nothing else.

---

## 19. Keep It Simple

Every new feature should answer one question:

> **Does this simplify administration?**

If the answer is no,

it probably does not belong in MiniNAS.

This test applies to backend behavior and workflow decisions — what the system does, and what it asks of the administrator. It does not govern visual styling explored while finding the right look. Trying, comparing, and discarding interface ideas is part of building good software, not a violation of simplicity.

---

## 20. Stability over Features

Reliability is always more valuable than feature count.

A smaller, stable release is preferable to a larger, unstable one.

Quality always comes before quantity.

---

## 21. Iteration Before Architecture

MiniNAS is built through iteration, not upfront design.

Features are explored, tested, and refined in conversation before becoming permanent.

Early experimentation — including visual experiments that are later discarded — is part of the process, not a deviation from it.

The manifest guides direction. It does not replace discovery.

A project drifts when its *scope* quietly expands beyond file sharing administration — not when its *appearance* changes while searching for clarity.

---

# Project Values

MiniNAS values:

- Simplicity
- Transparency
- Predictability
- Maintainability
- Standards
- Performance
- Administrator Freedom

These values should guide every architectural decision and every line of code.

---

# Final Principle

> **Administrators think in tasks.**
>
> **Linux works in components.**
>
> **MiniNAS connects both worlds.**

MiniNAS does not hide Linux.

MiniNAS makes Linux file sharing easier to administer.
