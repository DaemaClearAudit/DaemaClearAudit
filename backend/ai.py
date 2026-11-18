import os
from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = "gemini-2.5-flash"

# AI가 찾아낼 청소 불량 항목과 한글 이름
VIOLATION_LABELS = {
    "TISSUE": "휴지",
    "CAN": "캔",
    "VINYL": "비닐",
    "DRINK_STAIN": "음료 얼룩",
    "PLASTIC_TRASH": "플라스틱 쓰레기",
    "DISH_REMAINS": "음식물 또는 식기 잔여",
}


class Violation(BaseModel):
    type: str
    label: str
    count: int


class AIResult(BaseModel):
    table_id: str
    image_quality: str  # GOOD, BLURRY, PARTIAL, UNUSABLE
    violations: list[Violation]
    reason: str
    confidence: float


PROMPT = """너는 학교 테이블 청소 상태 검수원이다. 사진 1장에는 테이블 {table_id} 하나만 있다.
- 테이블 상판을 중심으로, 사진에 실제로 보이는 것만 판단한다.
- 확인할 항목: TISSUE(휴지), CAN(캔), VINYL(비닐), DRINK_STAIN(음료 얼룩), PLASTIC_TRASH(플라스틱 쓰레기), DISH_REMAINS(음식물 또는 식기 잔여)
- 사진이 흐리면 image_quality="BLURRY", 테이블이 잘리거나 가려지면 "PARTIAL", 판단 불가면 "UNUSABLE", 정상이면 "GOOD"으로 쓴다.
- 문제가 없으면 violations는 빈 배열([])로 쓴다.
- reason에는 판정 근거를 한국어 한 문장으로 쓴다.
- confidence는 0.0 ~ 1.0 사이의 확신도다.
- table_id에는 "{table_id}"를 그대로 쓴다."""


def judge(result: AIResult) -> str:
    """AI 판독 결과를 받아 최종 상태(PASS / FAIL / REVIEW)를 결정한다."""
    # 1. 사진 품질이 좋지 않거나 AI 확신도가 0.7 미만이면 관리자가 직접 확인(REVIEW)
    if result.image_quality != "GOOD" or result.confidence < 0.7:
        return "REVIEW"
    # 2. 청소 불량 항목이 하나라도 있으면 불합격(FAIL)
    if len(result.violations) > 0:
        return "FAIL"
    # 3. 아무 문제 없으면 통과(PASS)
    return "PASS"


def analyze(image_bytes: bytes, mime_type: str, table_id: str) -> AIResult:
    """사진 1장을 Gemini에 보내 판독 결과를 받아온다."""
    client = genai.Client(api_key=os.getenv("API_KEY"))
    prompt = PROMPT.format(table_id=table_id)

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIResult,
        ),
    )

    result = AIResult.model_validate_json(response.text)
    result.table_id = table_id
    for v in result.violations:
        if v.type in VIOLATION_LABELS:
            v.label = VIOLATION_LABELS[v.type]
    return result
