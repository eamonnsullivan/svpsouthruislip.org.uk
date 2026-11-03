# svpsouthruislip.org.uk

Website for the Saint Vincent de Paul Society at St. Gregory the Great Parish in South Ruislip, UK. It is generated with [Hugo](https://gohugo.io/) and deployed to AWS S3.

## Prerequisites

Install Hugo Extended 0.165.0 or newer. On macOS with Homebrew:

```bash
brew install hugo
hugo version
```

## Development

Start Hugo's development server, including future-dated posts:

```bash
hugo server --buildFuture
```

Open <http://localhost:1313/>. Hugo watches content, templates, configuration, and static assets and reloads the browser after changes.

Create a production build in `public/`:

```bash
hugo --gc --minify --cleanDestinationDir
```

## Content

- Posts live in `content/posts/`. Keep the date at the start of each filename and set explicit `date`, `url`, `author`, and `tags` front matter. URLs start with `/posts/`; retain existing dates and nested paths.
- Pages live in `content/pages/` with root-level URLs such as `/foodbank/` or `/contact/`. Homepage content lives in `content/_index.md`.
- Tags use `/tags/` and `/tags/<slug>/`. Files in `content/tags/` preserve display labels and aliases for previously published tags; new tags need no legacy aliases.
- Global files such as icons and logos live in `static/img/`.
- Assets belonging to nested posts live in `static/posts/<bundle>/`. Link to them with root-relative URLs such as `/posts/sleep-out/around_table.jpg`.
- Page downloads and images live in `static/pages/<bundle>/`.
- Local templates live in `layouts/`; site CSS lives in `static/css/site.css`. Site intentionally has no remote Hugo theme dependency.

Example post front matter:

```yaml
---
title: "Post title"
date: "2026-01-15T00:00:00+00:00"
url: "/posts/2026-01-15-post-title/"
author: "Author name"
tags: ["example"]
---
```

## Workflow

Create branch before changing content. Preview locally, check links, push branch, and create pull request. After merge, GitHub Actions builds and deploys site to AWS.

Pull requests and deployments run a clean, strict Hugo production build and URL regression tests (Python 3.10 or newer, standard library only). They check build errors, warnings, duplicate output paths, internal links, canonical URLs, feed/sitemap URLs, navigation, and every migrated legacy redirect. Run the same checks locally before pushing:

```bash
hugo --gc --minify --cleanDestinationDir --panicOnWarning --printPathWarnings
python3 -m unittest discover -s tests -v
```

`tests/legacy_urls.json` records the published URL inventory at migration time. Keep these redirect checks even if content moves again. Always build with `--cleanDestinationDir` to prevent obsolete generated pages from surviving in `public/`.

These checks must pass before any changes can be merged to the main branch for deployment.

## AWS infrastructure adoption

Existing website resources are being adopted **in place**, not recreated. See [infrastructure files and checks](infrastructure/README.md), [verified live inventory](docs/infrastructure/inventory.md), and the [gated import runbook](docs/infrastructure/import-runbook.md).

**Adoption verification is complete: all ten original resources are adopted and fully verified across web (5), DNSSEC-key (2) and DNS (3).** Status: `ADOPTION_COMPLETE_VERIFIED_ALL_TEN_RESOURCES`. See [aggregate completion evidence](infrastructure/verification/adoption-completion.json) and the [web](infrastructure/verification/web-import-completion.json), [key](infrastructure/verification/dnssec-key-import-completion.json) and [DNS](infrastructure/verification/dns-import-completion.json) batch evidence. Original IDs, termination protection, installed-policy readbacks, retained deployed templates, direct configuration and supported native drift checks passed; no physical resources were replaced or deleted. Eight supported resources are `IN_SYNC`; BucketPolicy and KMS Alias are unsupported and were checked directly. Native drift is not exhaustive, and final public checks are point-in-time evidence, not continuous zero-outage proof.

No further AWS writes are required for adoption. All create/import/execution/waiter/policy-install/drift procedures are historical reference only—do not repeat them. All AWS writes were separately approved human actions; the assistant remained read-only. The eleven DNS records, certificate, delegation/parent DS, registrar and shared IAM remain external and untouched. Verification completion does **not** authorize publication, normal updates, commits/pushes, configuration changes or read-supplement removal. The existing freeze remains until an explicit human decision to resume publication/maintenance; future updates and any later supplement removal require separate review/approval.

Every push to `main`, including infrastructure-only changes, triggers website publication. Do not push to `main`, merge, publish or perform normal stack updates during the import baseline/configuration freeze. No automatic infrastructure workflow has been added.

## Migration note

Repository migrated from Cryogen to Hugo. Cryogen's Clojure source, EDN configuration, generated output, and bundled themes were removed. Source posts, pages, authors, tags, global images, post assets, downloads, and the feed URL are preserved.

Canonical URLs now use `/posts/…`, root-level pages, and `/tags/…` instead of `/posts-output/…`, `/pages-output/…`, and `/tags-output/…`. Existing date and nested post suffixes are unchanged. Hugo aliases preserve all previously published post, page, and tag URLs as HTML redirect pages with canonical links to their replacements. These work with the existing S3 deployment, but they are browser redirects, **not HTTP 301 responses**. Permanent HTTP redirects require separate hosting/CDN configuration. External sites' URLs are unchanged.
