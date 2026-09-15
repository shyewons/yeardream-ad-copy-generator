# AI 광고 카피 생성기

상품명, 특징, 타깃 고객, 광고 채널, 말투를 입력하면 한국어 광고 초안을 생성하는 FastAPI 웹 앱입니다. 로컬 Ollama의 `gemma4:e4b` 모델을 사용하며, 결과를 제목·본문·CTA·해시태그 카드로 나눠 표시하고 복사할 수 있습니다.

하루짜리 LLM 학습 프로젝트로 시작했습니다. 모델 호출뿐 아니라 **입력 검증 → 구조화 출력 → 후처리 → 응답 검증 → 웹 표시**까지 연결하는 것을 목표로 했습니다.

## 구현 범위

- 상품 정보 다섯 항목을 입력하는 폼
- LangChain `ChatPromptTemplate`과 `ChatOllama`를 이용한 광고 생성
- JSON Schema 기반 구조화 출력과 Pydantic 검증
- 일반적인 이모지·마크다운 제거, 공백·해시태그 정리
- 제목·본문·CTA 글자 수 제한
- 결과 카드 및 항목별 클립보드 복사
- 생성 중 로딩 애니메이션, 경과 시간, 중복 요청 방지
- 입력 오류, 모델 연결 실패, 시간 초과, 출력 형식 오류 안내

로그인, DB, RAG, Agent, 결제, 배포는 범위에 포함하지 않습니다. 생성 이력을 저장하는 기능도 없습니다.

## 기술 구성

| 영역 | 사용 기술 |
| --- | --- |
| 서버 | Python, FastAPI, Uvicorn |
| 검증 | Pydantic |
| LLM 연결 | LangChain Core, LangChain Ollama |
| 로컬 추론 | Ollama, `gemma4:e4b` |
| 화면 | HTML, CSS, JavaScript Fetch API |
| 테스트 | unittest, unittest.mock, FastAPI TestClient |

Python **3.14.5** 환경에서 확인했습니다. `requirements.txt`는 현재 확인한 직접 의존성 버전을 명시하며, 전체 전이 의존성을 고정하는 lock 파일은 아닙니다.

## 실행 방법

### 1. Ollama와 모델 준비

[Ollama](https://ollama.com/)를 설치한 뒤 앱을 실행합니다. 모델을 내려받습니다.

```powershell
ollama pull gemma4:e4b
ollama list
```

선택적으로 터미널에서 모델 실행을 먼저 확인할 수 있습니다.

```powershell
ollama run gemma4:e4b
```

기본 로컬 API 주소는 `http://localhost:11434`입니다. Ollama 앱이 이미 서버를 실행 중이면 별도 서버를 중복 실행할 필요가 없습니다. 앱을 사용하지 않는 환경에서는 `ollama serve`로 실행합니다.

### 2. Python 환경 준비

프로젝트 최상위 폴더에서 실행합니다. 다음은 Windows PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

가상환경 활성화가 제한된 환경에서는 활성화 없이 실행 파일을 직접 사용할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. FastAPI 실행

```powershell
python -m uvicorn main:app --reload
```

- 입력 화면: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API 테스트: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

HTML 파일을 직접 여는 대신 FastAPI의 입력 화면 주소로 접속합니다. FastAPI가 화면과 API를 같은 출처에서 제공하므로 현재 구성에서는 별도 CORS 설정이 필요하지 않습니다.

모델명과 통신 대기 시간은 `services/ad_generator.py`에서 설정합니다. 현재 연결 대기는 5초, 응답 읽기 대기는 300초입니다. 읽기 타임아웃은 전체 생성 작업에 대한 절대 시간 제한이 아닙니다.

## 사용 흐름

1. 상품명·특징·타깃 고객·채널·말투를 입력합니다.
2. **광고 생성하기**를 누릅니다.
3. 로딩 애니메이션과 경과 시간을 확인합니다.
4. 결과 카드에서 광고를 확인하고 필요한 항목을 복사합니다.

경과 시간은 브라우저가 요청을 보낸 뒤 기다린 시간입니다. 로딩 바는 대기 표시이며 모델의 실제 완료 퍼센트를 나타내지 않습니다.

## 처리 구조

```text
브라우저 입력 폼
  → POST /ads/generate
  → AdRequest 입력 검증
  → 프롬프트에 상품 정보 반영
  → ChatOllama로 JSON Schema 기반 생성 요청
  → JSON 응답 후처리
  → AdCopy 최종 검증
  → FastAPI JSON 응답
  → 결과 카드 표시 및 복사
```

`with_structured_output()`에는 `AdCopy.model_json_schema()`를 전달합니다. Pydantic 객체로 즉시 검증하기 전에 딕셔너리 형태의 응답을 정리하고, 이후 `AdCopy.model_validate()`로 최종 검증하기 위한 구성입니다.

프런트엔드는 모델 출력을 `textContent`로 표시합니다. 모델이 생성한 문자열을 HTML로 실행하거나 마크다운으로 렌더링하지 않습니다.

## 폴더 구조

```text
.
├── main.py                       # FastAPI 앱, 라우터·정적 파일 연결
├── routers/
│   └── ads.py                    # 광고 API와 HTTP 오류 응답
├── schemas/
│   └── ad.py                     # AdRequest, AdCopy
├── services/
│   ├── ad_generator.py           # 프롬프트, LLM 호출, 오류 분류
│   └── ad_postprocessor.py       # 텍스트·해시태그 후처리
├── view/
│   ├── index.html                # 입력 폼과 결과 카드
│   ├── style.css                 # 화면과 로딩 애니메이션
│   └── script.js                 # API 호출, 타이머, 복사, 오류 표시
├── tests/
│   ├── test_ads_errors.py        # 정상 응답과 오류 분류 테스트
│   └── test_ad_postprocessor.py  # 후처리와 API 연동 테스트
├── .gitignore
├── requirements.txt
└── README.md
```

## API

### `POST /ads/generate`

모든 입력 필드는 필수 문자열입니다.

| 필드 | 의미 | 글자 수 |
| --- | --- | --- |
| `product_name` | 상품명 | 1~100 |
| `features` | 상품 특징 | 1~1000 |
| `target` | 타깃 고객 | 1~200 |
| `channel` | 광고 채널 | 1~50 |
| `tone` | 말투 | 1~50 |

요청 예시:

```json
{
  "product_name": "데일리 텀블러",
  "features": "350ml, 스테인리스 소재, 손잡이 있음",
  "target": "출퇴근하는 직장인",
  "channel": "인스타그램",
  "tone": "친근한 말투"
}
```

응답 형태 예시입니다. 실제 문구는 생성마다 달라질 수 있습니다.

```json
{
  "headline": "출근길에 함께할 데일리 텀블러",
  "body": "350ml 용량에 스테인리스 소재, 손잡이가 있는 데일리 텀블러를 만나보세요.",
  "cta": "오늘의 일상에 더해보세요.",
  "hashtags": ["#데일리텀블러", "#출근길"]
}
```

제목은 100자, 본문은 1000자, CTA는 100자로 제한합니다. 해시태그는 중복을 제거하고 최대 5개까지 반환하며 빈 목록도 허용합니다.

### 오류 응답

| HTTP 상태 | 코드 | 의미 |
| --- | --- | --- |
| 422 | FastAPI 기본 검증 오류 | 요청 JSON이나 입력 필드가 올바르지 않음 |
| 503 | `MODEL_UNAVAILABLE` | Ollama 연결·전송 실패 |
| 503 | `MODEL_NOT_FOUND` | 모델 API의 404 응답; 모델 설치 상태 확인 필요 |
| 504 | `MODEL_TIMEOUT` | 통신 대기 시간 초과 |
| 502 | `INVALID_MODEL_OUTPUT` | 출력 파싱·형식 검증 실패 |
| 502 | `MODEL_ERROR` | 그 외 Ollama 오류 응답 |
| 500 | `INTERNAL_ERROR` | 예상하지 못한 생성 처리 오류 |

모델 관련 오류는 다음 형식으로 반환합니다. 상세 예외는 서버 로그에 기록합니다.

```json
{
  "detail": {
    "code": "MODEL_UNAVAILABLE",
    "message": "광고 생성 모델에 연결할 수 없어요. Ollama 실행 상태를 확인해주세요."
  }
}
```

422 응답은 위 구조와 달리 FastAPI 기본 `detail` 목록을 사용합니다. 자동 재시도는 구현하지 않았으며, 입력을 유지한 채 사용자가 다시 생성할 수 있습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
```

자동 테스트는 LLM 응답과 예외를 모의하므로 Ollama를 실행하지 않아도 됩니다. 총 7개 테스트 메서드에서 정상 응답, 입력 검증, 오류 분류, 후처리, 정리 후 빈 출력의 거절을 확인합니다. 실제 모델 품질이나 브라우저 동작을 자동으로 검증하는 테스트는 아닙니다.

Node.js가 설치되어 있다면 JavaScript 문법도 확인할 수 있습니다. Node.js는 앱 실행에 필수는 아닙니다.

```powershell
node --check view/script.js
```

수동 데모 입력:

| 항목 | 상품 1 | 상품 2 |
| --- | --- | --- |
| 상품명 | 데일리 텀블러 | 코튼 데일리백 |
| 특징 | 350ml, 스테인리스 소재, 손잡이 있음 | 면 100%, 내부 포켓 1개, 베이지 색상 |
| 타깃 | 출퇴근하는 직장인 | 책과 소지품을 들고 다니는 대학생 |
| 채널 | 인스타그램 | 문자 메시지 |
| 톤 | 친근한 말투 | 재치 있는 말투 |

수동 확인 항목:

- 로딩·경과 시간이 표시되고 성공·실패 후 종료되는지
- 결과 카드 표시와 항목별 복사가 동작하는지
- 마크다운·이모지와 중복 해시태그가 정리되는지
- 문장이 잘리거나 입력에 없는 제품 특성이 추가되지 않는지
- Ollama를 종료했을 때 연결 실패 안내가 표시되는지

## 학습한 점과 한계

- **스키마 검증과 사실 검증은 다릅니다.** JSON 형태가 맞아도 제품의 무게·효과·수납 용량 등을 모델이 추론할 수 있습니다. 현재 후처리는 사실성을 검사하지 않습니다.
- **프롬프트만으로 형식 준수를 보장할 수 없습니다.** 이모지·마크다운 금지 지시가 지켜지지 않아 서버 후처리를 추가했습니다. 현재 정규식은 일반적인 표현을 대상으로 하며 모든 마크다운·유니코드 기호를 처리하는 완전한 파서는 아닙니다.
- **길이 제한은 단순 절단 방식입니다.** 제한을 넘으면 문장이 중간에 끊길 수 있습니다. 채널별 길이 제한은 아직 구현하지 않았습니다.
- **상품 정보를 보존하는 후처리에는 주의가 필요합니다.** 장식 기호와 의미 있는 상품 표기를 완벽히 구분하지 못할 수 있습니다. 게시 전에 결과를 확인해야 합니다.
- **공백 입력 처리 범위가 다릅니다.** 웹 폼은 앞뒤 공백을 제거하고 공백만 있는 입력을 거절합니다. 현재 API 스키마 자체에는 공백 제거 설정이 없어 직접 API를 호출하면 공백 문자열이 통과할 수 있습니다.
- **생성 속도는 환경에 따라 달라집니다.** 모델 로딩, 장치 성능, 입력과 출력 길이에 영향을 받으며, 현재 생성은 스트리밍 없이 완성된 응답을 기다립니다.

추후 개선 후보는 채널별 길이 정책, 문장 단위 길이 조정, 사실 주장 검사, 제한된 재시도입니다.
