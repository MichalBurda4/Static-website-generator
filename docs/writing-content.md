# Writing content for this SSG

Put Markdown files in `content/` (subfolders are allowed).
The generator finds every `*.md` file recursively.

Each file has two parts:

1. **Front matter** (YAML metadata between `---` lines) — for the generator
2. **Body** (Markdown) — converted to HTML

---

## Front matter

```markdown
---
title: My Post Title
date: 2026-10-18
slug: my-post
---
```

| Field | Required | What it becomes / does |
|-------|----------|-------------------------|
| `title` | No | Page title. If omitted, derived from the file name. |
| `date` | No | Publication date (`YYYY-MM-DD`). Used to sort pages (newest first). |
| `slug` | No | Short id (for URLs later). If omitted, derived from the file name (`My_File.md` → `my-file`). |

You may add extra YAML fields (e.g. `tags:`). They are stored in `Page.metadata` but are not used in HTML generation yet.

If there is no front matter, the whole file is treated as the Markdown body.

---

## Markdown body → HTML

After the closing `---`, write normal Markdown. Supported features (via the `markdown` library):

| You write | Meaning | Becomes in HTML |
|-----------|---------|-----------------|
| `# Heading` | Level-1 heading | `<h1>Heading</h1>` |
| `## Heading` | Level-2 heading | `<h2>Heading</h2>` |
| `### Heading` | Level-3 heading | `<h3>Heading</h3>` |
| (more `#` = deeper) | Levels 4–6 | `<h4>` … `<h6>` |
| `**bold**` | Bold text | `<strong>bold</strong>` |
| `*italic*` | Italic text | `<em>italic</em>` |
| `` `inline code` `` | Inline code | `<code>inline code</code>` |
| `- item` or `* item` | Bullet list | `<ul><li>item</li></ul>` |
| `1. item` | Numbered list | `<ol><li>item</li></ol>` |
| blank line between paragraphs | New paragraph | `<p>...</p>` |
| line break inside a paragraph | Soft line break (`nl2br`) | `<br>` |
| ` ``` ` … ` ``` ` | Fenced code block | `<pre><code>...</code></pre>` |
| ` ```python ` … | Code block with language hint | same, with language class when applicable |
| Markdown tables | Tables | `<table>`, `<tr>`, `<td>`, … |

### Example

````markdown
---
title: Hello SSG
date: 2026-03-20
slug: hello
---

# Welcome

This is a paragraph with **bold** and `code`.

- one
- two

```python
print("Hello, SSG!")
```
````

Notes:

- `# Welcome` in the body is a heading **inside the article**.
- `title:` in front matter is metadata for the site (listing, templates later). They are independent.

---

## Where to put files

| Path | Role |
|------|------|
| `content/hello.md` | Page at the content root |
| `content/posts/my-post.md` | Same parsing; subfolder is only organization for now |

Both are loaded the same way today. Folder layout may matter for URLs in a later stage.

---

## How to check your file

From the project root (with `uv` installed):

```bash
uv run ssg parse
```

You should see your title, date, slug, and a short HTML snippet.

---

## Related code

- Parser: `src/ssg/parser.py`
- CLI: `src/ssg/cli.py` (`ssg parse`)
- Sample content: `content/hello.md`, `content/posts/drugi-wpis.md`
