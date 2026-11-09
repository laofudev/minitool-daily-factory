#!/usr/bin/env python3
"""validate_tool.py — validate a Minitool tool zip package.

Usage:
    python3 validate_tool.py <tool.zip> [--fix]

Exit codes:
    0  all checks passed
    1  one or more checks failed
    2  usage error / zip unreadable

--fix auto-repairs structural problems (flattens a single wrapping directory,
removes junk files) and rewrites the zip in place. Content problems (external
URLs, inline scripts, manifest errors) are reported but never auto-fixed.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

WHITELIST_EXT = {
    ".html", ".css", ".js",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".woff", ".woff2", ".json",
}
CATEGORIES = ("text-tools", "developer-tools", "calculators")
ICONS = ("code", "link", "key", "text", "calc", "swap")
MANIFEST_FIELDS = (
    "name", "file", "category", "desc", "metaDescription",
    "keywords", "icon", "faq", "toolPurpose",
)
STRICT_FIELDS = (
    "useCases", "howToSteps", "audience",
    "pageTitle", "shortBlurb", "whyUse",
)
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)
XMLNS_RE = re.compile(r"xmlns(:\w+)?=\"http://www\.w3\.org/[^\"]*\"")
INLINE_EVENT_RE = re.compile(r"\son[a-zA-Z]+\s*=")
SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
IMPORT_EXPORT_RE = re.compile(r"^\s*(import\s+[\w*{]|import\s*\(|export\s+)")

results = []  # list of (ok: bool, label: str, details: list[str])


def report(ok, label, details=None):
    results.append((bool(ok), label, details or []))


def is_junk(name):
    parts = name.split("/")
    if any(p in ("__MACOSX", "node_modules") for p in parts):
        return True
    base = parts[-1]
    if base == ".DS_Store" or base.endswith(".map"):
        return True
    return False


def fix_zip(zip_path, notes):
    """Remove junk entries and flatten a single wrapping directory.

    Returns True if the zip was rewritten.
    """
    changed = False
    with zipfile.ZipFile(zip_path) as zf:
        entries = [i for i in zf.infolist() if not i.is_dir()]
        names = [i.filename for i in entries]

        kept = [(i, n) for i, n in zip(entries, names) if not is_junk(n)]
        if len(kept) != len(names):
            removed = sorted(set(names) - {n for _, n in kept})
            notes.append("removed junk: " + ", ".join(removed))
            changed = True

        names2 = [n for _, n in kept]
        if "index.html" not in names2 and names2:
            tops = {n.split("/")[0] for n in names2}
            if len(tops) == 1:
                top = tops.pop()
                if top + "/index.html" in names2:
                    kept = [(i, n[len(top) + 1:]) for i, n in kept]
                    notes.append("flattened wrapping directory: %s/" % top)
                    changed = True

        if not changed:
            return False

        fd, tmp_path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as out:
                for info, new_name in kept:
                    out.writestr(new_name, zf.read(info.filename))
            shutil.move(tmp_path, zip_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    return True


def read_text(zf, name):
    try:
        return zf.read(name).decode("utf-8", errors="replace")
    except KeyError:
        return ""


def check(zip_path):
    try:
        zf = zipfile.ZipFile(zip_path)
    except (zipfile.BadZipFile, OSError) as e:
        print("error: cannot read zip: %s" % e, file=sys.stderr)
        return 2

    with zf:
        names = [i.filename for i in zf.infolist() if not i.is_dir()]
        lower = [n.lower() for n in names]

        # 1. index.html at root
        report("index.html" in names, "index.html at zip root",
               [] if "index.html" in names
               else ["index.html not found at zip root (--fix can flatten one wrapping directory)"])

        # 2. no junk files
        junk = [n for n in names if is_junk(n)]
        report(not junk, "no junk files (.DS_Store/__MACOSX/node_modules/*.map)",
               ["junk: %s" % n for n in junk])

        # 3. whitelist file types
        bad_ext = [n for n in names
                   if os.path.splitext(n)[1].lower() not in WHITELIST_EXT]
        report(not bad_ext, "only whitelisted file types",
               ["not allowed: %s" % n for n in bad_ext])

        html_names = [n for n in names if n.lower().endswith(".html")]
        js_names = [n for n in names if n.lower().endswith(".js")]
        css_names = [n for n in names if n.lower().endswith(".css")]
        scannable = html_names + js_names + css_names

        # 4. no external URLs
        ext_hits = []
        for n in scannable:
            text = XMLNS_RE.sub("", read_text(zf, n))
            for m in EXTERNAL_URL_RE.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                ext_hits.append("%s:%d" % (n, line))
        report(not ext_hits, "no external http(s):// references",
               ["external URL at %s (download it into the zip and use a relative path)"
                % h for h in ext_hits])

        # 5. no inline <script>, no inline events, no type="module"
        inline_hits = []
        for n in html_names:
            text = read_text(zf, n)
            for m in SCRIPT_TAG_RE.finditer(text):
                tag = m.group(0)
                line = text.count("\n", 0, m.start()) + 1
                if "src" not in tag.lower():
                    inline_hits.append("%s:%d inline <script>" % (n, line))
                if re.search(r"type\s*=\s*['\"]module['\"]", tag, re.IGNORECASE):
                    inline_hits.append("%s:%d type=\"module\"" % (n, line))
            for m in INLINE_EVENT_RE.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                inline_hits.append("%s:%d inline event %s" % (n, line, m.group(0).strip()))
        report(not inline_hits, "no inline <script> / inline events / type=\"module\"",
               inline_hits)

        # 6. no import/export in js (classic scripts only)
        module_hits = []
        for n in js_names:
            text = read_text(zf, n)
            for m in IMPORT_EXPORT_RE.finditer(text, re.MULTILINE):
                line = text.count("\n", 0, m.start()) + 1
                module_hits.append("%s:%d %s" % (n, line, m.group(0).strip()))
        report(not module_hits, "no import/export (classic scripts only)", module_hits)

        # 7. no <base>, <iframe>, <object>
        tag_hits = []
        for n in html_names:
            text = read_text(zf, n)
            for pat, label in ((r"<base\b", "<base>"),
                               (r"<iframe\b", "<iframe>"),
                               (r"<object\b", "<object>")):
                if re.search(pat, text, re.IGNORECASE):
                    tag_hits.append("%s contains %s" % (n, label))
        report(not tag_hits, "no <base> / <iframe> / <object>", tag_hits)

        # 8. manifest.json
        manifest_problems = validate_manifest(zf, names)
        # 9. strict SEO/content fields for new tools
        try:
            data = json.loads(zf.read("manifest.json").decode("utf-8"))
        except (ValueError, UnicodeDecodeError, KeyError):
            data = None
        if isinstance(data, dict):
            manifest_problems.extend(validate_strict_fields(data))
        report(not manifest_problems, "manifest.json complete and valid", manifest_problems)

    # output
    print("Validating: %s\n" % zip_path)
    passed = 0
    for ok, label, details in results:
        print(("  ✓ " if ok else "  ✗ ") + label)
        for d in details:
            print("      - %s" % d)
        if ok:
            passed += 1
    print("\n%d/%d checks passed" % (passed, len(results)))
    if passed == len(results):
        print("PASS")
        return 0
    print("FAIL")
    return 1


def validate_manifest(zf, names):
    problems = []
    if "manifest.json" not in names:
        return ["manifest.json not found at zip root"]
    try:
        data = json.loads(zf.read("manifest.json").decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return ["manifest.json is not valid JSON: %s" % e]
    if not isinstance(data, dict):
        return ["manifest.json root must be an object"]

    for field in MANIFEST_FIELDS:
        if field not in data:
            problems.append("missing field: %s" % field)
    if problems:
        return problems

    if not isinstance(data["name"], str) or not data["name"].strip():
        problems.append("name must be a non-empty string")

    if not isinstance(data["file"], str) or not KEBAB_RE.match(data["file"]):
        problems.append("file must be kebab-case (e.g. case-converter), got: %r" % data["file"])

    if not isinstance(data["category"], str) or not KEBAB_RE.match(data["category"]):
        problems.append("category must be kebab-case (e.g. text-tools), got: %r" % data["category"])
    elif data["category"] not in CATEGORIES:
        # 非错误：未知分类会自动在首页创建新 section
        print("note: new category %r will auto-create a homepage section" % data["category"])

    if not isinstance(data["desc"], str) or not data["desc"].strip():
        problems.append("desc must be a non-empty string")
    elif len(data["desc"]) > 60:
        problems.append("desc must be <= 60 chars, got %d" % len(data["desc"]))

    if not isinstance(data["metaDescription"], str) or not data["metaDescription"].strip():
        problems.append("metaDescription must be a non-empty string")
    elif len(data["metaDescription"]) > 155:
        problems.append("metaDescription must be <= 155 chars, got %d" % len(data["metaDescription"]))

    kw = data["keywords"]
    if not isinstance(kw, list) or not kw or not all(isinstance(k, str) and k.strip() for k in kw):
        problems.append("keywords must be a non-empty array of strings")

    if data["icon"] not in ICONS:
        problems.append("icon must be one of %s, got: %r" % (list(ICONS), data["icon"]))

    faq = data["faq"]
    if not isinstance(faq, list) or len(faq) != 3:
        problems.append("faq must contain exactly 3 items, got %s"
                        % (len(faq) if isinstance(faq, list) else type(faq).__name__))
    else:
        for i, item in enumerate(faq):
            if (not isinstance(item, dict)
                    or not isinstance(item.get("q"), str) or not item.get("q", "").strip()
                    or not isinstance(item.get("a"), str) or not item.get("a", "").strip()):
                problems.append("faq[%d] must be {\"q\": ..., \"a\": ...} with non-empty strings" % i)

    if not isinstance(data["toolPurpose"], str) or not data["toolPurpose"].strip():
        problems.append("toolPurpose must be a non-empty string")
    else:
        tp_lower = data["toolPurpose"].lower()
        generic_phrases = [
            "small, focused utility",
            "there is nothing to install",
            "type or paste your input",
            "adjust any available options",
            "run the tool and review the result",
            "use the copy button",
            "open the page, do your work",
        ]
        for ph in generic_phrases:
            if ph in tp_lower:
                problems.append("toolPurpose contains generic filler: %r" % ph)
                break

    return problems


def validate_strict_fields(data):
    """Check SEO/content fields required for new tools."""
    problems = []
    for field in STRICT_FIELDS:
        if field not in data:
            problems.append("missing field: %s (required for new tools)" % field)
            continue

        value = data[field]
        if field == "pageTitle":
            if not isinstance(value, str) or not value.strip():
                problems.append("pageTitle must be a non-empty string")
            elif not (25 <= len(value) <= 70):
                problems.append("pageTitle should be 25-70 chars, got %d" % len(value))
        elif field == "shortBlurb":
            if not isinstance(value, str) or not value.strip():
                problems.append("shortBlurb must be a non-empty string")
            elif len(value) > 100:
                problems.append("shortBlurb must be <= 100 chars, got %d" % len(value))
        elif field == "whyUse":
            if not isinstance(value, list) or len(value) < 2:
                problems.append("whyUse must be a list with at least 2 items")
            else:
                for i, item in enumerate(value):
                    if not isinstance(item, str) or not item.strip():
                        problems.append("whyUse[%d] must be a non-empty string" % i)
        elif field in ("useCases", "howToSteps"):
            if not isinstance(value, list) or len(value) < 2:
                problems.append("%s must be a list with at least 2 items" % field)
            else:
                for i, item in enumerate(value):
                    if not isinstance(item, str) or not item.strip():
                        problems.append("%s[%d] must be a non-empty string" % (field, i))
        elif field == "audience":
            if not isinstance(value, str) or not value.strip():
                problems.append("audience must be a non-empty string")
            elif "anyone who needs" in value.lower():
                problems.append("audience is too generic: avoid 'anyone who needs ...'")
    return problems


def main(argv):
    args = [a for a in argv[1:] if a not in ("--fix", "--legacy")]
    fix = "--fix" in argv[1:]
    if len(args) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    zip_path = args[0]
    if not os.path.isfile(zip_path):
        print("error: file not found: %s" % zip_path, file=sys.stderr)
        return 2

    if fix:
        notes = []
        try:
            if fix_zip(zip_path, notes):
                print("Auto-fix applied to %s:" % zip_path)
                for n in notes:
                    print("  ~ %s" % n)
                print()
        except (zipfile.BadZipFile, OSError) as e:
            print("error: cannot read zip: %s" % e, file=sys.stderr)
            return 2

    return check(zip_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
