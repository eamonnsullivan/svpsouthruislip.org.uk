"""Clean-URL regression checks; run after `hugo --cleanDestinationDir`.

Run with `python3 -m unittest discover -s tests -p test_urls.py`.
Only Python's standard library is needed. No network requests are made.
"""

from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
LEGACY_SECTIONS = {"posts-output", "pages-output", "tags-output"}
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                 "link", "meta", "param", "source", "track", "wbr"}


class Document(HTMLParser):
    """Collect decoded attributes, visible headings, and scoped anchors."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.references = []
        self.anchors = []
        self.canonicals = []
        self.refreshes = []
        self.headings = []
        self.base_urls = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        context = self.stack + [(tag, attrs)]
        for attribute in ("href", "src", "poster"):
            if attribute in attrs:
                self.references.append((tag, attribute, attrs[attribute]))
        if tag == "base" and "href" in attrs:
            self.base_urls.append(attrs["href"])
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.refreshes.append(attrs.get("content", ""))
        if tag == "a":
            self.anchors.append({"attrs": attrs, "context": context, "text": []})
        if tag == "h1":
            self.headings.append([])
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.anchors and any(tag == "a" for tag, _ in self.stack):
            self.anchors[-1]["text"].append(data)
        if self.headings and any(tag == "h1" for tag, _ in self.stack):
            self.headings[-1].append(data)

    @property
    def redirect(self):
        return bool(self.refreshes)


def page_path(file):
    relative = file.relative_to(PUBLIC).as_posix()
    return "/" + (relative[:-10] if relative.endswith("index.html") else relative)


def external_url(value, origin):
    parsed = urlsplit(value)
    return (parsed.scheme.lower() in {"http", "https"} or value.startswith("//")) and (
        urlsplit(urljoin(origin, value)).netloc.lower() != urlsplit(origin).netloc.lower()
    )


def source_external_references(text, origin):
    """Read ordinary Markdown destinations and raw HTML without a Markdown dependency."""
    references = Counter()
    # Balanced parentheses in destinations are common in external article URLs.
    pattern = r'!?\[[^\]\n]*\]\(\s*(https?://(?:[^\s()]+|\([^()]*\))+)(?:\s+[^\n]*?)?\)'
    for match in re.finditer(pattern, text):
        value = unescape(re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~])", r"\1", match[1]))
        if external_url(value, origin):
            references[value] += 1
    for _, _, value in Document(text).references:
        if external_url(value, origin):
            references[value] += 1
    return references


class CleanURLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PUBLIC / "index.html").is_file():
            raise AssertionError("Missing Hugo build: run `hugo --cleanDestinationDir` first (public/index.html absent).")
        inventory = ROOT / "tests" / "legacy_urls.json"
        if not inventory.is_file():
            raise AssertionError("Missing tests/legacy_urls.json: provide the original URL mapping before running migration tests.")
        cls.inventory = json.loads(inventory.read_text(encoding="utf-8"))
        if not isinstance(cls.inventory, dict) or not cls.inventory:
            raise AssertionError("legacy_urls.json must be a nonempty object mapping old paths to new paths.")
        config = (ROOT / "hugo.toml").read_text(encoding="utf-8")
        base = re.search(r'^baseURL\s*=\s*[\"\']([^\"\']+)[\"\']', config, re.MULTILINE)
        if not base:
            raise AssertionError("Cannot find baseURL in hugo.toml.")
        cls.origin = base[1]
        cls.documents = {
            page_path(file): Document(file.read_text(encoding="utf-8"))
            for file in sorted(PUBLIC.rglob("*.html"))
        }

    def internal_path(self, value, context):
        """Resolve URL references before decoding; encoded #/? are filename characters."""
        resolved = urlsplit(urljoin(urljoin(self.origin, context), value))
        origin = urlsplit(self.origin)
        if resolved.scheme.lower() not in {"http", "https"}:
            return None
        if resolved.netloc.lower() != origin.netloc.lower():
            return None
        return unquote(resolved.path or "/")

    def assert_clean(self, path, context):
        self.assertFalse(LEGACY_SECTIONS.intersection(path.split("/")),
                         f"{context}: legacy URL path {path!r}")

    def assert_exists(self, path, context):
        candidate = (PUBLIC / path.lstrip("/")).resolve()
        self.assertTrue(candidate.is_relative_to(PUBLIC.resolve()),
                        f"{context}: URL escapes public: {path!r}")
        if path.endswith("/") or candidate.is_dir():
            candidate /= "index.html"
        self.assertTrue(candidate.is_file(), f"{context}: missing internal target {path!r} ({candidate})")
        return candidate

    def assert_reference(self, value, context):
        path = self.internal_path(value, context)
        if path is not None:
            self.assert_clean(path, context)
            self.assert_exists(path, context)
        return path

    def assert_destination(self, value, expected, context):
        parsed = urlsplit(value)
        self.assertEqual(self.internal_path(value, context), unquote(expected),
                         f"{context}: wrong destination {value!r}; expected {expected!r}")
        self.assertFalse(parsed.query or parsed.fragment,
                         f"{context}: destination must not have query or fragment: {value!r}")

    def test_inventory_redirects_and_real_targets(self):
        self.assertIn("/tags-output/", self.inventory, "Inventory must include the tags index.")
        seen = set()
        for old, new in self.inventory.items():
            with self.subTest(old=old, new=new):
                for path in (old, new):
                    self.assertIsInstance(path, str)
                    parsed = urlsplit(path)
                    self.assertTrue(path.startswith("/") and not path.startswith("//"))
                    self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
                self.assertIn(old.split("/")[1], LEGACY_SECTIONS)
                self.assertNotRegex(old, r"/page/\d+/", "Inventory must not include pagination.")
                prefix, remainder = old.lstrip("/").split("/", 1)
                expected = {"posts-output": "/posts/", "pages-output": "/", "tags-output": "/tags/"}[prefix] + remainder
                self.assertEqual(new, expected, "Mapping must preserve the original URL suffix.")
                self.assertNotIn(new, seen, "Two legacy pages must not collide at one destination.")
                seen.add(new)
                self.assert_clean(unquote(new), old)
                self.assert_exists(unquote(old), old)
                redirect = self.documents.get(unquote(old))
                self.assertIsNotNone(redirect, f"{old}: missing HTML alias document")
                self.assertEqual(len(redirect.canonicals), 1, f"{old}: alias needs one canonical")
                self.assert_destination(redirect.canonicals[0], new, old)
                self.assertEqual(len(redirect.refreshes), 1, f"{old}: alias needs one meta refresh")
                refresh = re.fullmatch(r'\s*0\s*;\s*url\s*=\s*(.*?)\s*', redirect.refreshes[0], re.IGNORECASE)
                self.assertIsNotNone(refresh, f"{old}: expected immediate refresh, got {redirect.refreshes!r}")
                self.assert_destination(refresh[1].strip("\"'"), new, old)
                self.assert_exists(unquote(new), old)
                target = self.documents.get(unquote(new))
                self.assertIsNotNone(target, f"{old}: target must be an HTML page: {new}")
                self.assertFalse(target.redirect, f"{old}: redirect chain to {new}")
                self.assertEqual(len(target.canonicals), 1, f"{new}: missing/duplicate canonical")
                self.assert_destination(target.canonicals[0], new, new)

    def test_internal_html_references(self):
        for path, document in self.documents.items():
            # Hugo alias bodies intentionally link to their new destination too.
            self.assertFalse(document.base_urls, f"{path}: unexpected <base>; relative-URL resolution would change")
            for tag, attribute, value in document.references:
                with self.subTest(page=path, tag=tag, attribute=attribute, url=value):
                    self.assert_reference(value, path)

    def test_page_canonicals(self):
        for path, document in self.documents.items():
            if document.redirect:
                continue
            with self.subTest(page=path):
                self.assertEqual(len(document.canonicals), 1, f"{path}: expected exactly one canonical")
                canonical = document.canonicals[0]
                self.assertTrue(urlsplit(canonical).scheme in {"http", "https"},
                                f"{path}: canonical must be absolute")
                # Paginated lists intentionally canonicalize to the list root.
                expected = re.sub(r"/page/\d+/$", "/", path)
                self.assert_destination(canonical, expected, path)
                self.assert_reference(canonical, path)

    def test_feed_and_sitemap(self):
        for name in ("feed.xml", "sitemap.xml"):
            with self.subTest(xml=name):
                file = PUBLIC / name
                self.assertTrue(file.is_file(), f"Missing public/{name}; rebuild Hugo outputs.")
                tree = ET.fromstring(file.read_text(encoding="utf-8"))
                urls = []
                for element in tree.iter():
                    local = element.tag.rsplit("}", 1)[-1]
                    if local in {"loc", "link", "guid"} and element.text and element.text.strip():
                        urls.append(element.text.strip())
                    if local == "link" and "href" in element.attrib:
                        urls.append(element.attrib["href"])
                self.assertTrue(urls, f"{name}: no URL entries found")
                for value in urls:
                    with self.subTest(xml=name, url=value):
                        self.assertIsNotNone(self.internal_path(value, "/" + name),
                                             f"{name}: URL should use site origin: {value!r}")
                        self.assert_reference(value, "/" + name)
                if name == "feed.xml":
                    self.assertTrue(tree.findall("./channel/item"), "RSS feed has no items")
                    for item in tree.findall("./channel/item"):
                        context = item.findtext("link") or "/feed.xml"
                        description = Document(item.findtext("description") or "")
                        for _, _, value in description.references:
                            with self.subTest(feed_item=context, url=value):
                                self.assert_reference(value, context)

    def test_navigation_and_active_contact(self):
        activities = {
            "Foodbank": "/foodbank/",
            "Home visits": "/home-visits/",
            "Bereavement Care": "/bereavement/",
            "Support for young people and mentoring": "/mentoring/",
            "Immigration Detainee Support": "/refugee/",
            "Care home visits": "/care-home-visits/",
            "Prayer Activities": "/prayer-activities/",
        }
        for path, document in self.documents.items():
            if document.redirect:
                continue
            with self.subTest(page=path):
                contact = [a for a in document.anchors
                           if "".join(a["text"]).strip() == "Contact"
                           and any(tag == "nav" for tag, _ in a["context"])]
                self.assertEqual(len(contact), 1, f"{path}: primary navigation needs Contact")
                self.assert_destination(contact[0]["attrs"].get("href", ""), "/contact/", path)
                if path == "/contact/":
                    self.assertEqual(contact[0]["attrs"].get("aria-current"), "page",
                                     "Contact navigation must mark the current page")
                else:
                    self.assertNotEqual(contact[0]["attrs"].get("aria-current"), "page",
                                        f"{path}: Contact incorrectly marked current")
                links = {"".join(a["text"]).strip(): a["attrs"].get("href", "")
                         for a in document.anchors
                         if any(attrs.get("id") == "activities" for _, attrs in a["context"])}
                for label, destination in activities.items():
                    self.assertIn(label, links, f"{path}: missing activity {label!r}")
                    self.assert_destination(links[label], destination, path)
        self.assertIn("/contact/", self.documents, "Clean contact page missing")

    def test_taxonomy_display_labels(self):
        for slug, label in (("jrs", "JRS"), ("social-justice", "Social Justice")):
            old = f"/tags-output/{slug}/"
            if old not in self.inventory:
                continue
            destination = self.inventory[old]
            for path in ("/", "/tags/", destination):
                with self.subTest(page=path, label=label):
                    self.assertIn(path, self.documents)
                    document = self.documents[path]
                    labels = ["".join(a["text"]).strip() for a in document.anchors
                              if self.internal_path(a["attrs"].get("href", ""), path) == destination]
                    self.assertIn(label, labels, f"{path}: taxonomy label must preserve {label!r}")
                    if path == destination:
                        headings = ["".join(parts) for parts in document.headings]
                        self.assertTrue(any(label in heading for heading in headings),
                                        f"{path}: term heading must contain {label!r}, got {headings!r}")

    def test_all_tag_pages_list_posts(self):
        for old, destination in self.inventory.items():
            if not old.startswith("/tags-output/") or old == "/tags-output/":
                continue
            with self.subTest(tag=destination):
                document = self.documents[destination]
                post_links = [
                    anchor for anchor in document.anchors
                    if any(tag == "main" for tag, _ in anchor["context"])
                    and (self.internal_path(anchor["attrs"].get("href", ""), destination) or "").startswith("/posts/")
                ]
                self.assertTrue(post_links, f"{destination}: tag listing has no posts")

    def test_source_external_links_preserved(self):
        # Derive expectations from this repository, never a reference site's charities.
        checked = 0
        for source in sorted((ROOT / "content").rglob("*.md")):
            text = source.read_text(encoding="utf-8")
            expected = source_external_references(text, self.origin)
            if not expected:
                continue
            match = re.search(r'^url:\s*[\"\']([^\"\']+)[\"\']', text, re.MULTILINE)
            if match:
                destination = self.inventory.get(match[1], match[1])
            else:
                relative = source.relative_to(ROOT / "content").with_suffix("")
                if relative.parts[0] in {"posts", "pages"}:
                    prefix = {"posts": "posts-output", "pages": "pages-output"}[relative.parts[0]]
                    suffix = Path(*relative.parts[1:]).as_posix()
                    old = f"/{prefix}/{suffix}/"
                    self.assertIn(old, self.inventory,
                                  f"{source}: cannot identify rendered page for external-link checks")
                    destination = self.inventory[old]
                else:
                    destination = "/" if relative.as_posix() == "_index" else f"/{relative.as_posix()}/"
            with self.subTest(source=str(source.relative_to(ROOT)), page=destination):
                document = self.documents.get(unquote(destination))
                self.assertIsNotNone(document, f"{source}: rendered page missing at {destination}")
                actual = Counter(value for _, _, value in document.references
                                 if external_url(value, self.origin))
                self.assertFalse(expected - actual,
                                 f"{destination}: external URLs changed or removed: {dict(expected - actual)!r}")
                checked += 1
        self.assertGreater(checked, 0, "No source external links were checked")
        layout_links = Counter()
        for source in (ROOT / "layouts").rglob("*.html"):
            for _, _, value in Document(source.read_text(encoding="utf-8")).references:
                if external_url(value, self.origin):
                    layout_links[value] += 1
        homepage_links = Counter(value for _, _, value in self.documents["/"].references
                                 if external_url(value, self.origin))
        self.assertFalse(layout_links - homepage_links,
                         f"External layout links changed or removed: {dict(layout_links - homepage_links)!r}")


if __name__ == "__main__":
    unittest.main()
