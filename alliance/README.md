# Alliance

This directory documents how local, sensitive repositories connect to Konoha Agentic Academy.

Public files in this directory should only contain templates, examples, and non-sensitive guidance.

Private villages must stay outside the public repository history. The first planned local village is `kirigakure`, which is already ignored by `.gitignore`.

Recommended pattern:

```text
alliance/
  README.md
  templates/
    village/
  kirigakure/              # ignored, private, local only
    .konoha.local/
    village.md
    local-kage.md
    mission-rules.md
    private-context.md
```

Before adding a new local village, add its folder to `.gitignore` unless it only contains sanitized examples.
