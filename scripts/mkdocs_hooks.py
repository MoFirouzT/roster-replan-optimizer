"""Make the documentation's source citations work on the site.

The docs cite code constantly, because that is what `CLAUDE.md`'s citation rule asks for:
**85 links to 31 targets outside `docs/`**, naming `roster_replan/model.py`,
`scripts/figures.toml`, `CLAUDE.md` and the rest. Written relative, they resolve when
GitHub renders the file and `scripts/lint_docs.py` checks them there. On a site built from
`docs/` alone they resolve to nothing, and MkDocs reports each one as a warning, which is
85 warnings hiding whichever one is real.

So this rewrites them at build time, and only them: a link whose target lands outside
`docs_dir` becomes a `blob` URL on the repository. The Markdown on disk keeps the relative
form, so GitHub and the linter are untouched, and the same line works in both renderings.

The second case is a link to a **directory**, which GitHub serves as a listing and a site
cannot serve at all: `[guide](guide)` and the eight others like it. Where the directory has
an index page the link goes there, and where it has none it goes to the repository tree,
which is the only honest target left.

Registered as `hooks:` in `mkdocs.yml`; nothing imports it.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

# Markdown links, minus images: `[text](target#anchor)`. The negative lookbehind drops
# `![alt](...)`, whose target must stay a file the site actually serves.
LINK = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)#\s]+)(#[^)\s]*)?\)")

SKIP = ("http://", "https://", "mailto:", "//")


INDEX_NAMES = ("README.md", "index.md")


def _under(path: Path, base: Path) -> str:
    """`path` relative to `base`, with forward slashes. Empty when they are the same."""
    return "/".join(path.relative_to(base).parts)


def _repo_base(config) -> str | None:
    return (config.get("repo_url") or "").rstrip("/") or None


def on_page_markdown(markdown: str, *, page, config, files) -> str:
    repo = _repo_base(config)
    if repo is None:
        return markdown

    docs_dir = Path(config["docs_dir"]).resolve()
    root = docs_dir.parent
    page_dir = (docs_dir / page.file.src_uri).parent

    def rewrite(match: re.Match[str]) -> str:
        text, target, anchor = match.group(1), match.group(2), match.group(3) or ""
        if target.startswith(SKIP):
            return match.group(0)

        landing = (page_dir / target).resolve()
        if not landing.is_relative_to(root):
            # Escapes the repository altogether. Leave it: MkDocs should say so.
            return match.group(0)

        if landing.is_dir():
            for name in INDEX_NAMES:
                if (landing / name).exists():
                    here = _under(page_dir, docs_dir) or "."
                    there = _under(landing / name, docs_dir)
                    return f"[{text}]({posixpath.relpath(there, here)}{anchor})"
            kind = "tree"
        elif landing.is_relative_to(docs_dir):
            return match.group(0)
        else:
            kind = "blob"

        return f"[{text}]({repo}/{kind}/main/{_under(landing, root)}{anchor})"

    return LINK.sub(rewrite, markdown)
