# MiniNAS Access Panel Concept

Changes agreed:
- Rename "Permissions" to "Access".
- Replace link to File Manager with native Access modal.
- Owner: dropdown of system users.
- Group: dropdown of system groups.
- Permissions: checkboxes (Owner/Group/Others Read/Write/Execute).
- Numeric field editable (two-way sync with checkboxes).
- Show symbolic representation (e.g. rwxr-xr-x).
- Recursive checkbox enabled by default for directories.
- Validate octal input.
- Warn for risky values (0777, 0000), do not block.
- Keep architecture extensible for future ACL support.
