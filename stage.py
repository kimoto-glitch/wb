#!/usr/bin/env python3
"""웨이보 셀러 소식 — 사진 준비 단계.

내려받은 원본 사진(`downloads/weibo-{date}/`)을 사이트 자산으로 복사하고,
보고서용 썸네일(폭 480px)을 만들어 `assets/{date}/manifest.json` 을 남긴다.
build.py 는 이 manifest 를 읽어 카드에 사진을 붙인다.

사용: python3 stage.py --date 2026-11-20 [--src /workspace/downloads/weibo-2026-11-20]
"""
import argparse
import json
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK_ROOT = os.path.join(
    os.path.dirname(ROOT),
    "scheduled-actions", "📰-웨이보-팔로우-아침-카드뉴스", "work",
)
THUMB_W = 480


def stage(date_str, src):
    items = json.load(open(os.path.join(WORK_ROOT, date_str, "items.json"), encoding="utf-8"))
    dst = os.path.join(ROOT, "assets", date_str)
    thumbs = os.path.join(dst, "thumbs")
    os.makedirs(thumbs, exist_ok=True)

    manifest, copied, missing = {}, 0, []
    for acc in items["accounts"]:
        author = acc["author"]
        for post in acc["posts"]:
            pid = post["id"]
            files = []
            for i in range(len(post.get("pics", []))):
                name = f"{author}_{pid}_{i}.jpg"
                path = os.path.join(src, name)
                if not os.path.exists(path):
                    missing.append(name)
                    continue
                out = f"{pid}-{i:02d}.jpg"
                shutil.copyfile(path, os.path.join(dst, out))
                im = Image.open(path).convert("RGB")
                w, h = im.size
                im2 = im.resize((THUMB_W, round(h * THUMB_W / w)), Image.LANCZOS) if w > THUMB_W else im
                im2.save(os.path.join(thumbs, out), "JPEG", quality=82, optimize=True, progressive=True)
                files.append({"full": out, "w": w, "h": h})
                copied += 1
            manifest[pid] = files

    with open(os.path.join(dst, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"assets/{date_str}/ — 사진 {copied}장 복사·썸네일 생성")
    if missing:
        print("원본에서 찾지 못한 파일:", ", ".join(missing))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-11-20")
    ap.add_argument("--src", default=None)
    a = ap.parse_args()
    stage(a.date, a.src or os.path.join(os.path.dirname(ROOT), "downloads", f"weibo-{a.date}"))
