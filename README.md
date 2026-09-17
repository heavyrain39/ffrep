# Fruit Fly Re-Embodiment Project

**Same Brain, Different Bodies.**

FFREP의 한국어 소개·FAQ 사이트 초안입니다. 직선 테두리와 얇은 격자를 사용한 가벼운 정적 페이지이며, 프레임워크나 패키지 설치가 필요하지 않습니다.

## 먼저 문장부터 고치기

사이트 문안의 원본은 **`content/ko.json`**입니다. 제목, 설명, FAQ 질문과 답변을 여기서 수정하면 됩니다. FAQ의 `id`와 `category`는 링크·필터에 사용하므로 문장 수정 때는 그대로 둡니다.

GitHub 화면에서 이 JSON만 고쳐 커밋해도 Actions가 새 HTML을 생성합니다. 로컬에서도 아래 빌드를 실행하면 `index.html`과 배포용 `_site/`가 생성됩니다. 생성물은 Git에 별도로 올리지 않습니다.

```sh
python scripts/build.py
python -m unittest discover -s tests -v
python -m http.server 8000 --directory _site
```

브라우저에서 `http://localhost:8000`을 엽니다. Windows에서 Python 명령이 다르면 `py`를 사용하세요. 생성된 HTML에는 한국어 문안이 이미 들어 있어 JavaScript를 끈 상태에서도 본문과 FAQ를 읽을 수 있습니다.

## GitHub Pages 공개

1. 저장소 **Settings → Pages → Build and deployment → Source → GitHub Actions**를 선택합니다.
2. **Actions → Build and deploy FFREP → Run workflow**를 한 번 실행합니다.
3. 이후 `main`에 수정 사항을 올리면 자동으로 빌드·배포합니다.

예상 주소는 `https://heavyrain39.github.io/ffrep/`입니다. Pages 설정 전에는 이 주소가 열리지 않습니다. 최초 실행에서 Pages가 꺼져 있으면 빌드와 검사는 수행하되 배포는 건너뛰고 설정 안내를 남깁니다.

공식 안내: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## 영어판을 나중에 켜기

현재는 **KO만 활성화**, EN은 ‘영어 준비 중’으로 표시합니다. 영어 초안이 존재하는 것처럼 보이게 하지 않았습니다.

1. `content/ko.json`을 복사해 `content/en.json`을 만듭니다.
2. 모든 표시 문장을 번역하고 `meta.lang`을 `en`으로 바꿉니다. `id`·`category`와 배열 순서는 한국어와 동일하게 유지합니다.
3. `content/locales.json`에서 영어의 `enabled`를 `true`로 바꿉니다.
4. 빌드·검사를 통과한 뒤 커밋합니다.

그러면 EN 버튼으로 전체 문안을 한 번에 바꿀 수 있습니다. 선택은 브라우저에만 저장하며 `?lang=en` 링크도 지원합니다. 검색·질문 링크·열린 FAQ를 위해 언어별 ID는 동일하게 유지합니다. 새 질문이나 번역 키를 추가하면 두 언어를 함께 갱신해야 하며, 빌드가 누락을 검사합니다.

## 구성

- `content/ko.json` — 한국어 공개 문안
- `content/locales.json` — 언어 활성화 목록
- `templates/page.html` — 페이지 구조
- `assets/site.css` — 색·간격·직선형 UI
- `assets/site.js` — 검색, 주제 필터, 답변 전체 펼치기, 질문 링크, 언어 전환
- `scripts/build.py` — 의존성 없는 정적 빌드
- `tests/test_site.py` — 문안·구조·공개 범위 검사
- `.github/workflows/pages.yml` — GitHub Pages 배포

## 공개 범위

이 저장소에는 공개 설명과 웹 UI만 담습니다. 학습 코드, 설정 레시피, 원본 실험 로그, 체크포인트, 비공개 문서와 모델 파일은 포함하지 않습니다. 도식은 이 사이트를 위해 만든 개념 그림이며 실제 신경 데이터나 학습된 동작을 시각화한 것이 아닙니다. 실제 영상·아바타 파일도 아직 넣지 않았습니다.

공개 데이터 출처는 [MaleCNS](https://male-cns.janelia.org/)입니다. FFREP는 데이터 제작 기관과 별개의 개인 프로젝트이며, 이 사이트는 원본 데이터 자체를 재배포하지 않습니다.

외부 폰트·분석 도구·추적 코드·외부 실행 라이브러리가 없습니다. 언어 선호를 위한 브라우저 로컬 저장 외에 방문자 정보를 수집하지 않습니다. 문안은 2026-09-17 작성 초안이며, 자동으로 훈련 성과를 반영하는 대시보드가 아닙니다.
