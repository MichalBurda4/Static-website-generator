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
template: post
---
```

| Field | Required | What it becomes / does |
|-------|----------|-------------------------|
| `template` | Yes | Jinja template used to render the page. `post` and `post.html` both load `templates/post.html`. The name must be a single identifier, with no path separators. |
| `title` | No | Page title. If omitted, derived from the file name. |
| `date` | No | Publication date (`YYYY-MM-DD`). Used to sort pages (newest first). |
| `slug` | No | Short id (for URLs later). If omitted, derived from the file name (`My_File.md` → `my-file`). |

You may add extra YAML fields (e.g. `tags:`). They are stored in `Page.metadata`. The generator uses `title`, `date`, `slug`, and `template` when building the page.

Every page needs front matter with `template`. A file that has no front matter fails the build.

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
template: post
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
| `content/hello.md` | Site page. Written to `output/{slug}.html`. Add a link in `templates/base.html` when it should appear in the header. |
| `content/posts/my-post.md` | Member of the `posts` collection. The homepage lists it because `templates/index.html` loops `posts`. Written to `output/posts/{slug}.html`. |
| `content/notes/extra.md` | Member of the `notes` collection. A template can loop `notes` the same way the homepage loops `posts`. Written to `output/notes/{slug}.html`. |

The output directory keeps the same folders as `content/`. Each directory placed directly inside `content/` becomes a template variable of the same name, holding the pages inside that directory (including pages in nested folders). Files placed directly in `content/` are rendered and left out of those lists.

The directory name has to be a valid identifier, and it cannot be `site`, `page`, `home_url`, `static_url`, or `root_prefix`.

Header links are written explicitly in `templates/base.html`. They use `root_prefix` so the same link works from nested pages:

```html
<a href="{{ root_prefix }}witaj.html">Witaj w SSG</a>
```

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
- CLI: `src/ssg/cli.py` (`ssg parse`, `ssg build`)
- Sample content: `content/hello.md`, `content/posts/drugi-wpis.md`
