#!/usr/bin/env python3
"""웨이보 셀러 소식 — 정적 보고서 사이트 빌더.

입력
  scheduled-actions/📰-웨이보-팔로우-아침-카드뉴스/work/{date}/items.json  (수집·묶음 데이터)
  content/{date}.json                                                     (한국어 제목·요약·불릿)
  assets/{date}/manifest.json                                             (사진 목록)

출력
  reports/{date}/index.html   보고서 한 장
  index.html                  가장 최근 보고서로 이동

사용: python3 build.py [--date 2026-11-20]
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK_ROOT = os.path.join(
    os.path.dirname(ROOT),
    "scheduled-actions", "📰-웨이보-팔로우-아침-카드뉴스", "work",
)

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def kst_from_beijing(date_str, md_hm, shift_hours=1):
    """items.json 의 'M/D HH:MM'(웨이보 표시 = 베이징) → KST datetime."""
    m = re.match(r"(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})", md_hm.strip())
    if not m:
        return None
    year = int(date_str[:4])
    mo, d, hh, mm = (int(x) for x in m.groups())
    base = dt.datetime(year, mo, d, hh, mm) + dt.timedelta(hours=shift_hours)
    return base


def ex(s):
    from html import escape
    return escape(s, quote=True)


def human_date(date_str):
    d = dt.date.fromisoformat(date_str)
    return f"{d.year}년 {d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"


def build(date_str):
    items = load(os.path.join(WORK_ROOT, date_str, "items.json"))
    content = load(os.path.join(ROOT, "content", f"{date_str}.json"))
    manifest_path = os.path.join(ROOT, "assets", date_str, "manifest.json")
    manifest = load(manifest_path) if os.path.exists(manifest_path) else {}

    # ── 계정·글 정리 ──────────────────────────────
    accounts = []
    for acc in items["accounts"]:
        posts = []
        for p in acc["posts"]:
            t = kst_from_beijing(date_str, p.get("time_kst", ""))
            ko = content["posts"].get(p["id"])
            if ko is None:
                raise SystemExit(f"content/{date_str}.json 에 {p['id']} 항목이 없습니다")
            photos = manifest.get(p["id"], [])
            posts.append({
                "id": p["id"],
                "url": p.get("url") or f"https://m.weibo.cn/status/{p['id']}",
                "time": t,
                "text": (p.get("text") or "").strip(),
                "pic_count_orig": p.get("pic_count", len(photos)),
                "photos": photos,
                "ko": ko,
            })
        posts.sort(key=lambda x: (x["time"] or dt.datetime.min), reverse=True)
        meta = content["sellers"].get(acc["author"], {})
        latest = posts[0]["time"] if posts else None
        accounts.append({
            "handle": acc["author"],
            "uid": acc.get("uid", ""),
            "meta": meta,
            "posts": posts,
            "latest": latest,
            "pic_total": sum(len(p["photos"]) for p in posts),
        })

    accounts.sort(key=lambda a: (a["latest"] or dt.datetime.min), reverse=True)

    all_times = [p["time"] for a in accounts for p in a["posts"] if p["time"]]
    if all_times:
        window_txt = (f"{min(all_times):%Y-%m-%d %H:%M} ~ {max(all_times):%m-%d %H:%M} KST")
    else:
        window_txt = content.get("window", "")

    n_posts = sum(len(a["posts"]) for a in accounts)
    n_pics = sum(a["pic_total"] for a in accounts)
    n_sellers = len(accounts)

    # ── 검색용 문자열 ────────────────────────────
    def search_blob(acc, post):
        parts = [
            acc["handle"], acc["meta"].get("ko", ""), acc["meta"].get("tab", ""),
            post["ko"].get("tag", ""), post["ko"]["title"],
            " ".join(post["ko"].get("bullets", [])), post["text"],
        ]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    # ── 탭 ───────────────────────────────────────
    tab_html = [f'<button type="button" class="tab" data-seller="all" data-label="전체" '
                f'aria-pressed="true">전체<span class="c">{n_posts}</span></button>']
    for acc in accounts:
        kind = acc["meta"].get("kind", "seller")
        cls = "tab community" if kind == "community" else "tab"
        label = acc["meta"].get("tab") or acc["handle"]
        tab_html.append(
            f'<button type="button" class="{cls}" data-seller="{ex(acc["handle"])}" '
            f'data-label="{ex(label)}" aria-pressed="false">{ex(label)}'
            f'<span class="c">{len(acc["posts"])}</span></button>'
        )

    # ── 요약 ─────────────────────────────────────
    s = content["summary"]
    summary_items = "\n".join(
        f'          <li><b>{ex(b["seller"])}</b> — {ex(b["text"])}</li>'
        for b in s["bullets"]
    )

    # ── 섹션 ─────────────────────────────────────
    sections = []
    for si, acc in enumerate(accounts, start=1):
        meta = acc["meta"]
        kind = meta.get("kind", "seller")
        kind_cls = "seller-kind community" if kind == "community" else "seller-kind"
        kind_txt = "커뮤니티" if kind == "community" else "셀러"

        cards = []
        for pi, post in enumerate(acc["posts"], start=1):
            ko = post["ko"]
            t = post["time"]
            time_txt = t.strftime("%Y-%m-%d %H:%M") if t else "시각 미상"
            npics = len(post["photos"])
            if npics:
                pic_txt = f"사진 {npics}장"
                if post["pic_count_orig"] and post["pic_count_orig"] > npics:
                    pic_txt = f"사진 {npics}장 (원문 {post['pic_count_orig']}장 중 대표)"
            else:
                pic_txt = "사진 없음" if post["pic_count_orig"] == 0 else "사진 미수집"
            meta_line = (f'게시 {time_txt} <span class="kst">KST</span>'
                         f'  ·  {pic_txt}')

            thumbs = []
            photo_data = []
            if post["photos"]:
                photo_data = [
                    {"f": f"../../assets/{date_str}/{ph['full']}",
                     "a": f'{acc["handle"]} {ko["title"]} 사진 {i + 1}'}
                    for i, ph in enumerate(post["photos"])
                ]
                shown_max = 6
                for i, ph in enumerate(post["photos"][:shown_max]):
                    overlay = ""
                    if i == shown_max - 1 and npics > shown_max:
                        overlay = f'<span class="more">+{npics - shown_max + 1}</span>'
                    thumbs.append(
                        f'<button type="button" class="thumb" data-idx="{i}" '
                        f'aria-label="사진 {i + 1} 확대 보기">'
                        f'<img src="../../assets/{date_str}/thumbs/{ph["full"]}" alt="" '
                        f'width="{ph.get("w", 690)}" height="{ph.get("h", 690)}" loading="lazy" decoding="async">'
                        f'{overlay}</button>'
                    )
            thumbs_html = f'\n            <div class="thumbs">{"".join(thumbs)}</div>' if thumbs else ""
            photos_attr = (f' data-photos="{ex(json.dumps(photo_data, ensure_ascii=False))}"'
                           if photo_data else "")
            photos_attr += (f' data-post-title="{ex(acc["handle"] + " · " + ko["title"])}"')

            points = "\n".join(f'              <li>{ex(b)}</li>' for b in ko.get("bullets", []))
            raw = ex(post["text"]) if post["text"] else ""
            raw_html = (f'\n          <details class="raw"><summary>원문 중국어</summary>'
                        f'<p>{raw}</p></details>') if raw else ""

            cards.append(f'''        <article class="post" data-search="{ex(search_blob(acc, post))}"{photos_attr}>
          <div class="post-head">
            <span class="post-no">{pi:02d}</span>
            <div class="post-body">
              <div class="post-tags"><span class="tag">{ex(ko.get("tag", "소식"))}</span></div>
              <h3 class="post-title">{ex(ko["title"])}</h3>
              <p class="post-meta">{meta_line}</p>
            </div>
          </div>{thumbs_html}
          <ul class="points">
{points}
          </ul>
          <div class="post-foot">
            <a class="orig" href="{ex(post["url"])}" target="_blank" rel="noopener">웨이보 원문 ↗</a>{raw_html}
          </div>
        </article>''')

        latest_txt = acc["latest"].strftime("%H:%M") if acc["latest"] else "—"
        sections.append(f'''      <section class="seller-section" data-seller="{ex(acc["handle"])}">
        <div class="seller-head">
          <div>
            <div class="seller-id">
              <span class="seller-idx">{si:02d}</span>
              <h2 class="seller-name">{ex(meta.get("ko") or acc["handle"])}</h2>
              <span class="seller-handle">{ex(acc["handle"])}</span>
              <span class="{kind_cls}">{kind_txt}</span>
            </div>
            <p class="seller-sub">{ex(meta.get("desc", ""))} · 최근 {latest_txt} KST · <span class="seller-count">{len(acc["posts"])}건</span></p>
          </div>
        </div>
{chr(10).join(cards)}
      </section>''')

    # ── 날짜 목록 ────────────────────────────────
    reports_dir = os.path.join(ROOT, "reports")
    dates = sorted([d for d in os.listdir(reports_dir)
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)], reverse=True)
    if date_str not in dates:
        dates = sorted(dates + [date_str], reverse=True)
    options = "\n".join(
        f'          <option value="{d}"{" selected" if d == date_str else ""}>{d.replace("-", ".")}'
        f'{" (최신)" if i == 0 else ""}</option>'
        for i, d in enumerate(dates)
    )

    collected = content.get("collected_at", "")
    collected_txt = collected.replace("T", " ")[:16] + " KST" if collected else ""

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>웨이보 셀러 소식 {content.get("date_label", date_str)}</title>
<meta name="description" content="웨이보에서 팔로우한 셀러들이 최근 24시간 동안 올린 발매·제작 소식을 한국어로 정리한 보고서입니다.">
<meta name="color-scheme" content="light">
<meta property="og:title" content="웨이보 셀러 소식 {content.get("date_label", date_str)}">
<meta property="og:description" content="{ex(s["headline"])}">
<link rel="stylesheet" href="../../assets/site.css">
</head>
<body>

<header class="topbar">
  <div class="topbar-in">
    <a class="brand" href="../../index.html"><b>WB</b><span>Seller Journal</span></a>
    <div class="topbar-meta">DAILY REPORT · {content.get("date_label", date_str)}</div>
  </div>
</header>

<main class="wrap">
  <p class="eyebrow">WEIBO ORIGINAL FEED <em>/</em> 한국어 보고서</p>
  <h1 class="headline">웨이보 셀러 소식 <span class="d">{content.get("date_label", date_str)}</span></h1>
  <p class="lead">{ex(content.get("subtitle", ""))}</p>

  <div class="controls">
    <label for="datepick">보고 날짜</label>
    <select id="datepick" class="datepick" data-current="{date_str}">
{options}
    </select>
    <a class="link" href="../../index.html">최신 보고서 ↗</a>
  </div>

  <div class="meta-strip">
    <span><b>{ex(human_date(date_str))}</b></span>
    <span>수집 {ex(collected_txt)}</span>
    <span>대상 기간 {ex(window_txt)}</span>
    <span>팔로우 {content.get("follow_total", "")}개 계정 중 <b>{n_sellers}개</b> 계정에 새 글</span>
  </div>

  <div class="stats">
    <div class="stat"><div class="n">{n_posts}</div><div class="k">게시물</div></div>
    <div class="stat"><div class="n">{n_pics}</div><div class="k">사진</div></div>
    <div class="stat"><div class="n">{n_sellers}</div><div class="k">소식이 있는 셀러</div></div>
  </div>

  <div class="summary">
    <div class="tagline"><span class="dot"></span>오늘의 셀러 소식</div>
    <h2>{ex(s["headline"])}</h2>
    <ul>
{summary_items}
    </ul>
  </div>

  <div class="toolbar">
    <div class="searchbox">
      <svg width="15" height="15" viewBox="0 0 15 15" aria-hidden="true"><circle cx="6.2" cy="6.2" r="4.6" fill="none" stroke="#6f6c5b" stroke-width="1.5"/><path d="M9.7 9.7L14 14" stroke="#6f6c5b" stroke-width="1.5"/></svg>
      <input id="search" type="search" placeholder="보고서 검색 — 품목·셀러·키워드" autocomplete="off" aria-label="보고서 검색">
      <button type="button" class="clear" id="search-clear" hidden aria-label="검색어 지우기">×</button>
    </div>
    <div class="tabs" role="group" aria-label="셀러 필터">
{chr(10).join("      " + t for t in tab_html)}
    </div>
    <p class="count-line" id="count-line">전체 {n_posts}건</p>
  </div>

  <div id="posts">
{chr(10).join(sections)}
  </div>

  <div class="empty" id="empty"><b>조건에 맞는 소식이 없습니다</b>검색어를 줄이거나 다른 셀러 탭을 선택해 보세요.</div>

  <footer>
    <p class="note">웨이보에서 팔로우한 계정 <b>{content.get("follow_total", "")}개</b>를 대상으로 최근 24시간 동안 올라온 글을 모아 셀러별로 정리했습니다.
    한국어 제목·요약은 원문을 옮긴 것이며, 가격·일정·소재 표기는 원문에 적힌 내용을 그대로 살렸습니다. 셀러가 밝힌 주장은 그 사실을 함께 적었습니다.
    커뮤니티 계정(검수·제보)은 구매자 제보를 모아 올리는 곳이라 셀러의 발표와 구분해 읽어 주세요.</p>
    <p class="note mono">게시 시각은 한국 시간(KST) 기준입니다. 웨이보 표시 시각(베이징)에서 1시간을 더했습니다.
    사진은 원문 첨부 이미지를 내려받아 줄인 것이며, 클릭하면 크게 볼 수 있습니다.</p>
  </footer>
</main>

<div class="lightbox" id="lightbox" data-open="false" role="dialog" aria-modal="true" aria-label="사진 확대 보기">
  <div class="lb-stage">
    <button type="button" class="lb-close" id="lb-close" aria-label="닫기">✕</button>
    <button type="button" class="lb-prev" id="lb-prev" hidden aria-label="이전 사진">‹</button>
    <img class="lb-img" id="lb-img" alt="">
    <button type="button" class="lb-next" id="lb-next" hidden aria-label="다음 사진">›</button>
    <div class="lb-bar">
      <span id="lb-count">1 / 1</span>
      <span class="lb-title" id="lb-title"></span>
    </div>
  </div>
</div>

<script src="../../assets/report.js" defer></script>
</body>
</html>
'''

    out_dir = os.path.join(reports_dir, date_str)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # ── 루트 index.html (최신 호로 이동) ──────────
    latest = dates[0]
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>웨이보 셀러 소식</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="./reports/{latest}/">
<meta http-equiv="refresh" content="0; url=./reports/{latest}/">
<style>
  body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#f4f1e8;color:#191811;
    font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",system-ui,sans-serif}}
  .box{{text-align:center;padding:24px}}
  .box p{{color:#6f6c5b;font-size:14px;margin:10px 0 0}}
  .box a{{color:#191811}}
</style>
</head>
<body>
<div class="box">
  <p><b>웨이보 셀러 소식</b> — 최신 보고서로 이동합니다.</p>
  <p><a href="./reports/{latest}/">바로 열기 ({latest})</a></p>
</div>
<script>location.replace('./reports/{latest}/');</script>
</body>
</html>
''')

    print(f"reports/{date_str}/index.html — 게시물 {n_posts} · 사진 {n_pics} · 셀러 {n_sellers} · 최신 {latest}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-11-20")
    build(ap.parse_args().date)
