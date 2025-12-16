from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import qrcode
import segno
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "recipients.csv"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"

DOCS = ROOT / "docs"          # GitHub Pages отдаёт отсюда
OUT_QR = ROOT / "out" / "qr"  # QR сюда (не коммитим)

SITE_BASE_URL = "https://valkafea.github.io/qr-gifts"


@dataclass
class Recipient:
    slug: str
    title: str
    to_name: str
    message: str
    from_name: str
    hero_image_url: str
    gallery_urls: List[str]
    video_url: str
    video_type: str
    music_url: str
    theme: str


def _slug_ok(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "page"


def _youtube_embed(url: str) -> str:
    url = url.strip()
    vid = ""
    m = re.search(r"youtu\.be/([A-Za-z0-9_\-]+)", url)
    if m:
        vid = m.group(1)
    m = re.search(r"[?&]v=([A-Za-z0-9_\-]+)", url)
    if m:
        vid = m.group(1)
    if not vid:
        return url
    return f"https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1"


def load_recipients(path: Path) -> List[Recipient]:
    items: List[Recipient] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gallery_raw = (row.get("gallery_urls") or "").strip()
            gallery = [u.strip() for u in gallery_raw.split("|") if u.strip()] if gallery_raw else []

            items.append(
                Recipient(
                    slug=_slug_ok(row.get("slug") or ""),
                    title=(row.get("title") or "С Новым годом!").strip(),
                    to_name=(row.get("to_name") or "").strip(),
                    message=(row.get("message") or "").strip(),
                    from_name=(row.get("from_name") or "").strip(),
                    hero_image_url=(row.get("hero_image_url") or "").strip(),
                    gallery_urls=gallery,
                    video_url=(row.get("video_url") or "").strip(),
                    video_type=((row.get("video_type") or "").strip().lower() or "youtube"),
                    music_url=(row.get("music_url") or "").strip(),
                    theme=((row.get("theme") or "snow").strip().lower()),
                )
            )
    return items


def copy_static():
    (DOCS / "static").mkdir(parents=True, exist_ok=True)
    for p in STATIC.glob("*"):
        if p.is_file():
            (DOCS / "static" / p.name).write_bytes(p.read_bytes())


def clean_generated_pages():
    # чистим только то, что генерим
    gen_dir = DOCS / "p"
    if gen_dir.exists():
        for p in gen_dir.rglob("*"):
            if p.is_file():
                p.unlink()
        for p in sorted(gen_dir.glob("**/*"), reverse=True):
            if p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass
        try:
            gen_dir.rmdir()
        except OSError:
            pass


def make_qr(slug: str, url: str):
    OUT_QR.mkdir(parents=True, exist_ok=True)

    img = qrcode.make(url)
    img.save(OUT_QR / f"{slug}.png")

    qr = segno.make(url, error="M")
    qr.save(str(OUT_QR / f"{slug}.svg"), scale=8)


def render_pages(items: List[Recipient]):
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("page.html.j2")

    for it in items:
        page_dir = DOCS / "p" / it.slug
        page_dir.mkdir(parents=True, exist_ok=True)

        page_url = f"{SITE_BASE_URL}/p/{it.slug}/"
        youtube_embed_url = _youtube_embed(it.video_url) if (it.video_url and it.video_type == "youtube") else ""

        html = tpl.render(
            base_url="",
            title=it.title,
            to_name=it.to_name,
            message=it.message,
            from_name=it.from_name,
            hero_image_url=it.hero_image_url,
            gallery_urls=it.gallery_urls,
            video_url=it.video_url,
            video_type=it.video_type,
            youtube_embed_url=youtube_embed_url,
            music_url=it.music_url,
            theme=it.theme,
        )
        (page_dir / "index.html").write_text(html, encoding="utf-8")
        make_qr(it.slug, page_url)


def make_index(items: List[Recipient]):
    lines = [
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>QR Gifts</title>"
        "<link rel='stylesheet' href='static/style.css'>"
        "</head><body><div class='wrap'>"
        "<div class='card'><h1>QR Gifts</h1>"
        "<p class='small'>Тестовые страницы:</p></div>"
        "<div class='card'><ul>"
    ]
    for it in items:
        lines.append(f"<li><a href='p/{it.slug}/'>{it.slug}</a> — {it.to_name}</li>")
    lines.append("</ul></div></div></body></html>")
    (DOCS / "index.html").write_text("\n".join(lines), encoding="utf-8")


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    clean_generated_pages()

    items = load_recipients(DATA)
    copy_static()
    render_pages(items)
    make_index(items)

    print(f"OK: generated pages in {DOCS}")
    print(f"OK: qr codes in {OUT_QR} (not committed)")


if __name__ == "__main__":
    main()
