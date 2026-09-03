# svpsouthruislip.org.uk

Website for the Saint Vincent de Paul Society at St. Gregory the Great Parish in South Ruislip, UK. It is generated with [Hugo](https://gohugo.io/) and deployed to AWS S3.

## Prerequisites

Install Hugo Extended 0.165.0 or newer. On macOS with Homebrew:

```bash
brew install hugo
hugo version
```

No theme, JavaScript package, Clojure runtime, or other build dependency is required.

## Development

Start Hugo's development server, including future-dated posts:

```bash
hugo server --buildFuture
```

Open <http://localhost:1313/>. Hugo watches content, templates, configuration, and static assets and reloads the browser after changes.

Create a production build in `public/`:

```bash
hugo --gc --minify
```

## Content

- Posts live in `content/posts/`. Keep the date at the start of each filename and set explicit `date`, `url`, `author`, and `tags` front matter.
- Pages live in `content/pages/` and retain their legacy `url` values. Homepage content lives in `content/_index.md`.
- Global files such as icons and logos live in `static/img/`.
- Assets belonging to nested posts live in `static/posts/<bundle>/`. Link to them with root-relative URLs such as `/posts/sleep-out/around_table.jpg`.
- Page downloads and images live in `static/pages/<bundle>/`.
- Local templates live in `layouts/`; site CSS lives in `static/css/site.css`. Site intentionally has no remote Hugo theme dependency.

Example post front matter:

```yaml
---
title: "Post title"
date: "2026-01-15T00:00:00+00:00"
url: "/posts-output/2026-01-15-post-title/"
author: "Author name"
tags: ["example"]
---
```

## Workflow

Create branch before changing content. Preview locally, check links, push branch, and create pull request. After merge, GitHub Actions builds and deploys site to AWS.

## Migration note

Repository migrated from Cryogen to Hugo. Cryogen's Clojure source, EDN configuration, generated output, and bundled themes were removed. Source posts, pages, authors, tags, global images, post assets, downloads, feed URL, and practical legacy content URLs are preserved.
