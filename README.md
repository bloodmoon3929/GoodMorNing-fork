# GoodMorNing ☀️

사진 속 굿즈를 모으고, 볼록 스티커로 만들어 다이어리를 꾸미는 **Flutter Web + 로컬 GPU 서버** 앱입니다.

프론트는 **[GitHub Pages](https://niraaah.github.io/GoodMorNing/)**, GPU API와 데이터 저장소는 **사용자 Windows PC**에서 실행합니다. GitHub Actions는 main에 push할 때 Flutter 웹을 빌드해서 Pages에 배포하며, GPU 작업을 실행하는 서버는 아닙니다.

원본 [프로토타입](https://github.com/mokma18/goodmorning-prototype-demo)의 `?home` 소스를 기준으로 금고, 토끼, 로고, 글꼴, 색상, 입체 효과, 하단 메뉴를 재사용합니다. **Flutter 앱의 HtmlElementView 안에 원본 HTML/CSS 홈을 넣은 혼합 구조**이며, 모든 UI를 네이티브 Flutter 위젯으로 다시 그린 구현은 아닙니다. 에셋함과 다이어리 도구는 Flutter이고, 입체 다이어리는 Three.js입니다. 에셋함은 원본처럼 중앙의 좁은 화면과 3열 그리드를 사용합니다. 다이어리 편집 화면은 기존 기능을 유지하며 원본의 전체 다이어리 연출과 동일하지 않습니다.

스티커의 테두리·볼록 메시·유광 GLB 생성 함수는 [goodmorning-3d](https://github.com/bloodmoon3929/goodmorning-3d)의 `pipeline/sticker.py`에서 재사용합니다. 홈의 기존 샘플 배치는 원본 방식대로 브라우저에 보관하고, 생성한 에셋과 앱 다이어리는 PC의 DB에 저장합니다.

## 구현된 기능

- 원본 **훔쳐보기** 탭: 포치타·디무 다이어리 카드, 원본 샘플 다이어리 열람과 목록 복귀. [직접 열기](https://niraaah.github.io/GoodMorNing/?browse). GPU 연결 없이 열람 가능하며, 실제 이용자의 비공개 다이어리를 공개하는 기능은 아닙니다.
- 사진 업로드 후 사각형으로 굿즈 영역 선택
- **SAM 2.1**로 누끼 분리: Windows의 ONNX Runtime DirectML로 로컬 AMD GPU 사용
- 누끼 이미지로 가우시안 입자와 볼록한 표면을 만들고 `.ply`, `.splat`, `.glb`, PNG 저장
- 생성 작업의 대기·진행률·실패 표시, 완료된 스티커를 에셋 보관함에 추가
- 다이어리에 스티커와 폴라로이드 추가, 끌어서 이동, 크기·회전·순서 조절, 선택 항목 제거
- 다이어리 제목·메모·종이 색 편집, 입체 기울이기, PNG 내보내기
- SQLite에 에셋·생성 작업·다이어리 저장. 새로고침 후 다시 불러오기
- GitHub Pages 정적 프론트 + 접근 키로 보호된 로컬 GPU API. 같은 PC에서 앱/API를 함께 제공하는 방식도 유지

## GitHub Pages + 로컬 GPU 연결

1. [앱 주소](https://niraaah.github.io/GoodMorNing/)를 엽니다. 홈은 PC가 꺼져 있어도 열립니다.
2. PC에서 `scripts/start.ps1`, `scripts/tunnel.ps1`을 실행합니다.
3. **기본 앱 주소만 열면 이 PC의 GPU 서버에 자동 연결됩니다.** 별도 링크, 서버 주소 입력, 접근 키 입력은 필요하지 않습니다.
4. 사진 업로드·생성·에셋·다이어리는 연결된 PC에서 처리합니다. PC, API, 터널이 모두 켜져 있어야 합니다.

공개 서버 주소는 GitHub Actions 변수 `GPU_API_URL` → `runtime-config.json`으로 전달합니다. 앱이 `/auth/guest`에서 브라우저별 연결 토큰을 자동 발급받아 localStorage에 보관합니다. 사진·작업·다이어리는 토큰별로 분리하고 기본 샘플만 공유합니다. 다른 브라우저나 기기에서는 별도 보관함이 열리며, 브라우저 저장소를 지우면 기존 자동 연결 보관함을 다시 열 수 없습니다.

기존 소유자의 데이터와 접근 키는 그대로 유지하며, 기존 비공개 연결 링크 또는 수동 설정으로 접근할 수 있습니다. 소유자 키는 공개 코드·Actions 변수·배포 파일에 넣지 않습니다. 이 구성은 로그인 없는 공개 방문자가 자신의 보관함에서 로컬 GPU로 스티커를 생성할 수 있는 데모입니다.

CORS 기본 허용 출처는 `https://niraaah.github.io`입니다. 다른 프론트 도메인을 쓰려면 서버 실행 전 `GOODMORNING_FRONTEND_ORIGINS`를 쉼표로 구분해 설정하세요. `tunnel.ps1`은 새 터널 주소를 GitHub 변수에 반영하고 Pages를 재배포합니다. PC의 `gh`에 해당 저장소 권한이 있어야 합니다. 배포 후 앱을 새로고침하면 새 서버 주소를 자동으로 사용하며 Pages 주소는 유지됩니다. 재부팅 후 서버·터널을 자동 실행하는 Windows 시작 프로그램 등록은 포함하지 않습니다.

`.github/workflows/pages.yml`은 고정 Flutter 버전과 고정 submodule을 사용해 정적 파일을 만들고 Pages에 배포합니다. GitHub 저장소 Settings → Pages → Source는 GitHub Actions로 설정합니다. 별도 Node 서버나 프론트 실행 파일을 받을 필요가 없습니다.

## 스티커 처리 흐름

```mermaid
flowchart LR
  A[사진 + 선택 영역] --> B[SAM 2.1 / AMD DirectML]
  B --> C[누끼 이미지]
  C --> D[윤곽 기반 볼록 높이 + Gaussian 표면]
  D --> E[Gaussian PLY / SPLAT]
  D --> F[유광 GLB + PNG]
  F --> G[에셋 보관함]
  G --> H[Flutter 입체 다이어리]
  H --> I[SQLite 자동 저장]
```

**SAM 3D는 새 스티커 생성에 사용하지 않습니다.** 현재 사진 한 장의 보이는 면과 윤곽에서 높이를 만드는 **2.5D Gaussian relief** 구현입니다. 여러 시점의 사진으로 최적화하는 3D Gaussian Splatting 학습이나 보이지 않는 뒷면의 3D 복원은 포함하지 않습니다. 가우시안 표현은 PLY/SPLAT로 저장하며, 다이어리에서는 같은 표면을 GLB 메시로 베이크해 유광 반사를 표시합니다. 원본 저장소에서 가져온 기본 스티커 3개는 미리 생성된 샘플이며 출처는 메타데이터에 구분됩니다.

배경을 지우려면 사진에서 **굿즈를 감싸는 사각형을 직접 그려 주세요.** 전체 사진에 손이나 여러 물체가 함께 있으면 선택 영역에 따라 누끼 결과가 달라집니다. 이미 투명한 PNG는 알파를 사용합니다. ‘배경 포함’ 선택 시 사진 전체를 스티커로 만듭니다.

## 파일 구조

```text
GoodMorNing/
├─ .github/workflows/pages.yml  main push → Flutter 빌드 → Pages 배포
├─ app/                         Flutter Web 앱
│  ├─ lib/
│  │  ├─ main.dart             홈·에셋함·다이어리·사진 선택 화면
│  │  ├─ api.dart              API 요청과 업로드
│  │  ├─ diary_scene.dart      Flutter ↔ Three.js 메시지 연결
│  │  └─ reference_view.dart   원본 홈·훔쳐보기·메뉴 ↔ Flutter 탭 연결
│  ├─ assets/wordmark.png      원본 프로토타입 워드마크
│  ├─ web/                    웹 진입점·아이콘·manifest
│  │  ├─ reference/           빌드 때 원본 소스·폰트·샘플 복사 (Git 제외)
│  │  └─ scene/               빌드 때 입체 렌더러 복사 (Git 제외)
│  ├─ test/                   API 응답 처리 테스트
│  └─ pubspec.yaml
├─ server/
│  ├─ app.py                  FastAPI, 작업 큐, SQLite, 파일 제공
│  ├─ gpu.py                  GPU 선택·SAM 2 encoder/decoder 추론
│  ├─ stickers.py             누끼 → 볼록 스티커 생성
│  ├─ gaussian.py             Gaussian 표면·PLY/SPLAT 내보내기
│  ├─ access.py               외부 접속 키·세션 쿠키
│  ├─ vendor/sticker_geometry.py  원본 스티커 함수 재사용
│  ├─ scene/                  Three.js 입체 다이어리와 로컬 라이브러리
│  ├─ test_app.py             생성·저장·입력·접근 제어 테스트
│  └─ requirements-windows-lock.txt
├─ scripts/
│  ├─ setup.ps1               새 PC에서 환경 구성
│  ├─ setup_models.py         고정 버전 SAM 2 ONNX 모델 다운로드
│  ├─ build.ps1               Flutter 웹 빌드
│  ├─ prepare_frontend.py      원본 홈·메뉴·정적 3D 파일 준비
│  ├─ write_connection.py      공개 GPU 주소를 웹 런타임 설정에 기록
│  ├─ publish_connection.ps1   터널 주소 변경 → Pages 자동 재배포
│  ├─ start.ps1               앱/API 백그라운드 실행
│  ├─ tunnel.ps1              외부 접속 링크 생성
│  ├─ stop.ps1                이 프로젝트의 서버·터널 종료
│  ├─ browser_check.py        수동 실행 가능한 브라우저 확인 도구
│  └─ smoke_generate.py       샘플 생성 확인 도구
├─ prototype/                 프로토타입 Git submodule
├─ sticker-engine/            goodmorning-3d Git submodule
├─ data/                      로컬 전용, Git 제외
│  ├─ goodmorning.sqlite3      에셋·작업·다이어리 DB
│  ├─ assets/<id>/             원본 사진, 스티커, 메타데이터
│  ├─ models/sam2/             SAM 2 ONNX 모델 약 155MB
│  ├─ access.key              외부 접속 키
│  └─ verification/           로컬 검증 기록
├─ tools/                     로컬 Flutter SDK·cloudflared, Git 제외
├─ .venv/                     프로젝트 Python 환경, Git 제외
├─ logs/                      서버 로그·PID·접속 링크, Git 제외
├─ THIRD_PARTY.md              재사용 코드·모델 출처
└─ README.md
```

## 현재 PC에서 실행

프로젝트 위치: `C:\Users\meer\Downloads\goodmorning`

```powershell
cd C:\Users\meer\Downloads\goodmorning
.\scripts\start.ps1
```

PC 안에서: **http://127.0.0.1:8787**

코드를 수정했다면 Flutter 앱을 다시 빌드합니다. 서버 Python 코드 수정 후에는 서버를 재시작합니다.

```powershell
.\scripts\build.ps1
.\scripts\stop.ps1
.\scripts\start.ps1
```

현재 구성은 Windows / Python 3.12 / Flutter stable / AMD Radeon RX 9070 XT입니다. 시스템 전역 Flutter PATH는 변경하지 않았습니다.

## 새 PC에서 설치

Git과 Python 3.12가 필요합니다. Windows DirectX 12 GPU에서는 DirectML을 사용하며, DirectML이 없는 환경에서는 CPU provider를 사용할 수 있습니다. 기본 설치 스크립트와 lock 파일은 Windows용입니다.

```powershell
git clone --recurse-submodules https://github.com/niraaah/GoodMorNing.git
cd GoodMorNing
.\scripts\setup.ps1
.\scripts\start.ps1
```

원본 저장소는 submodule로 고정되어 있습니다. 모델·SDK·사용자 사진·DB는 GitHub에 올리지 않으며, setup 과정에서 필요한 SDK와 모델을 받습니다. 모델 버전과 다운로드 파일의 해시는 `data/models/sam2/manifest.json`에 기록됩니다.

## 휴대폰·외부에서 접속

```powershell
.\scripts\tunnel.ps1
```

출력된 **`https://…trycloudflare.com/connect#…` 전체 링크**로 접속합니다. 접근 키는 URL fragment에서 읽은 뒤 주소창에서 제거하고 HttpOnly 세션 쿠키로 전환합니다. 같은 링크는 `logs/access-link.txt`에도 저장됩니다. 키 없는 외부 요청은 사진·API에 접근할 수 없습니다.

- 이 PC와 서버·터널 프로세스가 켜져 있어야 합니다.
- 임시 터널을 새로 시작하면 주소가 바뀝니다. 운영용 고정 도메인은 별도 설정이 필요합니다.
- 사진 처리는 이 PC에서 실행됩니다. 외부 접속의 HTTPS 트래픽은 Cloudflare Tunnel을 경유합니다.
- 소유자용 전체 접속 링크는 기존 비공개 데이터에 접근합니다. 기본 Pages 주소의 자동 방문자 연결은 브라우저별로 데이터를 분리합니다.

```powershell
.\scripts\stop.ps1 -TunnelOnly  # 외부 접속만 종료
.\scripts\stop.ps1              # 서버와 터널 종료
```

## 주요 API

| 경로 | 역할 |
| --- | --- |
| `GET /api/health` | 서버·SAM 2 모델·GPU provider 상태 |
| `GET /api/assets` | 에셋 목록 |
| `POST /api/stickers` | multipart `photo`, `name`, `box` → 비동기 스티커 생성 |
| `GET /api/jobs/{id}` | 생성 상태와 진행률 |
| `POST /api/photos` | 폴라로이드 사진 저장 |
| `GET /api/diaries` | 저장된 다이어리 |
| `PUT /api/diaries/{id}` | 다이어리와 배치 저장 |
| `GET /files/{id}/sticker.glb` | 입체 스티커 |
| `GET /files/{id}/sticker.ply` | Gaussian PLY |

`box`는 `[left, top, right, bottom]` JSON 문자열이며 각 좌표는 0~1입니다. 사진 크기는 최대 16MB, 2,400만 화소이고 처리용으로 축소됩니다. 생성은 GPU 작업 한 개씩 순차 처리합니다.

## 확인된 범위와 남은 확인

- SAM 2.1이 RX 9070 XT의 DirectML provider에서 실제 실행됨을 프로파일로 확인했습니다. 일부 연산은 CPU provider가 처리합니다.
- 저장소 샘플의 선택 영역으로 GPU/CPU 결과를 비교했으며, 제공된 참조 마스크와의 IoU는 약 0.971입니다. 전체 사진을 선택하는 경우 같은 품질을 보장하지 않습니다.
- 최초 구현 당시 서버 자동 테스트 4개와 Dart 응답 처리 테스트 2개가 통과했습니다. 이후 Pages/CORS/외형 변경에는 이 결과를 적용하지 않습니다.
- 최신 외형 수정은 사용자 요청에 따라 **캡처 없이 원본 소스 기준**으로 진행했습니다. 브라우저 시각 비교와 기능 테스트는 수행하지 않았습니다. 빌드·배포 성공은 실제 브라우저 동작 검증을 뜻하지 않습니다.
- Flutter 분석에는 스타일 관련 info가 남아 있습니다. 웹 브라우저에서의 최종 조작·시각 검증은 사용자가 직접 진행할 예정이며 완료로 표시하지 않습니다.
- 사용자 요청에 따라 추가 자동 테스트는 중단했습니다. 제공한 확인 스크립트는 필요할 때 직접 실행할 수 있습니다.
- 샘플 생성 확인 스크립트는 실제 에셋과 다이어리 데이터를 추가합니다.

```powershell
.\.venv\Scripts\python.exe -m pytest server\test_app.py -q
cd app
..\tools\flutter\bin\flutter.bat test
```
