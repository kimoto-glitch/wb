# 웨이보 셀러 소식 (Weibo Seller Journal)

웨이보에서 팔로우한 셀러들이 최근 24시간 동안 올린 **발매·예약·제작 진행·발송** 소식을
한국어로 정리한 정적 웹 보고서입니다. 참고 사이트(`weibo-seller-digest-…chatgpt.site`)와 같은
구성·스타일로 만들었습니다.

- 사진은 원문 첨부 이미지를 내려받아 줄인 것이고, 클릭하면 라이트박스로 크게 볼 수 있습니다.
- 게시 시각은 **한국 시간(KST)** 입니다. 웨이보 표시 시각(베이징)에 1시간을 더했습니다.
- 셀러가 밝힌 주장(예: "국내 유일 원본")은 그 사실을 함께 적었고, 커뮤니티 계정(검수·제보)은
  셀러 발표와 구분해 표시했습니다.

## 구조

```
index.html                     가장 최근 보고서로 이동하는 페이지
reports/{YYYY-MM-DD}/index.html  보고서 한 장 (날짜별)
assets/site.css                공통 스타일
assets/report.js               검색 · 셀러 필터 · 라이트박스 · 날짜 이동
assets/{YYYY-MM-DD}/           사진 원본(긴 변 그대로) + thumbs/ 썸네일 + manifest.json
content/{YYYY-MM-DD}.json      한국어 제목·요약·불릿 (사람이 쓰는 원고)
build.py                       items.json + content + manifest → 보고서 HTML
stage.py                       downloads/weibo-{date}/ → assets/{date}/ (사진·썸네일·manifest)
.nojekyll                      GitHub Pages 에서 Jekyll 처리 없이 그대로 서빙
```

모든 경로는 상대 경로라서 GitHub Pages 의 하위 경로(`/저장소이름/`)에서도 그대로 동작합니다.

## 다음 날 보고서를 추가하는 순서

1. 수집 데이터가 있는지 확인 — `scheduled-actions/📰-웨이보-팔로우-아침-카드뉴스/work/{date}/items.json`
2. 사진 준비 — `python3 stage.py --date {date}` (원본: `downloads/weibo-{date}/`)
3. 원고 작성 — `content/{date}.json`
   - `posts.{post_id}` 에 `tag`, `title`, `bullets` 를 적습니다. `items.json` 의 모든 글 id 가 있어야 빌드가 됩니다.
   - `sellers.{handle}` 에 `ko`(화면에 보일 이름), `tab`(탭 짧은 이름), `kind`(`seller`|`community`), `desc`.
   - `summary` 에 오늘의 헤드라인과 불릿을 적습니다.
4. 빌드 — `python3 build.py --date {date}` → `reports/{date}/index.html` 생성, `index.html` 은 최신 호를 가리킵니다.
5. 확인 — `python3 -m http.server 8000` 후 `http://localhost:8000/` 에서
   검색·탭 필터·라이트박스·사진 로딩·모바일 폭(390px)을 확인합니다.

`content` 의 `window` 값은 쓰지 않습니다. 대상 기간은 `items.json` 의 실제 글 시각에서 자동 계산합니다.

## 배포

아직 배포하지 않았습니다. 공개할 경우 이 폴더를 그대로 GitHub 저장소 루트에 올리고
Settings → Pages 에서 브랜치 루트를 지정하면 됩니다(`index.html` 이 최신 보고서로 이동).
