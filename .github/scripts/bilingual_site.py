"""Publish English pages at existing URLs and their Chinese originals under /zh/."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup, Comment, Doctype, NavigableString

CHINESE = re.compile(r"[\u3400-\u9fff]")
SKIP = {"script", "style", "code", "pre", "svg", "math", "textarea"}
ATTRIBUTES = ("title", "aria-label", "placeholder", "alt")
NAV = {"Home": "首页", "Writing": "文章", "Study": "学习", "Projects": "项目",
       "Footprints": "足迹", "Links": "友链", "About": "关于", "Search": "搜索"}


def fields(soup):
    for node in soup.find_all(string=True):
        if isinstance(node, (Comment, Doctype)) or node.find_parent(SKIP):
            continue
        if node.strip():
            yield node, None, str(node)
    for tag in soup.find_all(True):
        for attr in ATTRIBUTES:
            if tag.get(attr):
                yield tag, attr, tag[attr]
        if tag.name == "meta" and (tag.get("name") == "description" or
                tag.get("property") in {"og:title", "og:description", "og:image:alt"}):
            if tag.get("content"):
                yield tag, "content", tag["content"]


def translate(strings, cache, model, cache_file=None):
    import ctranslate2
    import sentencepiece
    tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(next(model.rglob("sentencepiece.model"))))
    engine = ctranslate2.Translator(str(next(model.rglob("model.bin")).parent), compute_type="int8")
    pending = sorted(strings - cache.keys())
    for start in range(0, len(pending), 32):
        keys = pending[start:start + 32]
        # Split long text at sentence boundaries before tokenizing to avoid truncation.
        chunks, owners = [], []
        for i, key in enumerate(keys):
            for sentence in re.split(r"(?<=[。！？])", key):
                tokens = tokenizer.encode(sentence, out_type=str)
                for offset in range(0, len(tokens), 180):
                    chunks.append(tokens[offset:offset + 180])
                    owners.append(i)
        results = engine.translate_batch(chunks, beam_size=2, max_decoding_length=384)
        outputs = [[] for _ in keys]
        for i, result in zip(owners, results):
            outputs[i].append("".join(result.hypotheses[0]).replace("\u2581", " ").strip())
        for key, parts in zip(keys, outputs):
            value = " ".join(parts).strip()
            if not value:
                raise ValueError(f"Empty translation for {key[:40]}")
            cache[key] = value
        if cache_file and (start % 512 == 0 or start + 32 >= len(pending)):
            temporary = cache_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf8")
            temporary.replace(cache_file)
            print(f"Translated {min(start+32, len(pending))}/{len(pending)} segments", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("cache", type=Path)
    args = parser.parse_args()
    site = args.site
    pages = sorted(site.rglob("*.html"))
    if not pages or (site / "zh").exists():
        raise ValueError("Expected a fresh rendered site")
    routes = {}
    for page in pages:
        path = "/" + page.relative_to(site).as_posix()
        routes[path] = path
        if path.endswith("/index.html"):
            routes[path[:-10]] = path
            routes[path[:-11]] = path

    def localized(url):
        link = urlsplit(url)
        if link.netloc and link.hostname != "determine123.github.io":
            return url
        if link.path.startswith("/") and link.path in routes:
            return urlunsplit((link.scheme, link.netloc, "/zh" + link.path, link.query, link.fragment))
        return url

    cache = json.loads(args.cache.read_text(encoding="utf8")) if args.cache.exists() else {}
    strings = set()
    for page in pages:
        soup = BeautifulSoup(page.read_bytes(), "html.parser", from_encoding="utf-8")
        strings.update(s.strip() for _, _, s in fields(soup) if CHINESE.search(s))
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    translate(strings, cache, args.model, args.cache)
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    args.cache.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf8")
    for page in pages:
        original = page.read_text(encoding="utf8")
        path = "/" + page.relative_to(site).as_posix()
        url = path[:-10] if path.endswith("/index.html") else path
        for english in (True, False):
            soup = BeautifulSoup(original, "html.parser")
            if not soup.html or not soup.body:
                raise ValueError(f"Missing page layout: {path}")
            soup.html["lang"] = "en" if english else "zh-CN"
            for node, attr, value in list(fields(soup)):
                replacement = (cache if english else NAV).get(value.strip())
                if replacement:
                    result = value.replace(value.strip(), replacement, 1)
                    if attr:
                        node[attr] = result
                    else:
                        node.replace_with(NavigableString(result))
            if not english:
                for tag in soup.select("a[href], link[rel=canonical]"):
                    tag["href"] = localized(tag["href"])
                for tag in soup.select('meta[http-equiv="refresh" i]'):
                    tag["content"] = re.sub(r"(?i)(url=)(.+)", lambda m: m[1]+localized(m[2]), tag["content"])
            for old in soup.select("link[hreflang]"):
                old.decompose()
            for lang, href in (("en", url), ("zh-CN", "/zh"+url)):
                soup.head.append(soup.new_tag("link", rel="alternate", hreflang=lang, href=href))
            switch = soup.new_tag("a", href="/zh"+url if english else url,
                                  hreflang="zh-CN" if english else "en")
            switch.string = "简体中文" if english else "English"
            switch["data-no-swup"] = ""
            header = soup.find("header")
            (header or soup.body).insert(0, switch)
            dest = page if english else site / "zh" / page.relative_to(site)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(str(soup), encoding="utf8")


if __name__ == "__main__":
    main()
