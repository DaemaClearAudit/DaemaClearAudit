import os
import time
from enum import Enum

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()  # 프로젝트 루트의 .env 읽음

MODEL = "gemini-2.5-flash"

app = FastAPI(title="Automatic Cleaning Inspection")

from inspection_server.api import router
app.include_router(router)


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class Inspection(BaseModel):
    verdict: Verdict
    reason: str


PROMPT = (
    "너는 청소 상태 검수원이다. 사진의 청소 상태를 판정해라. "
    "깨끗하면 PASS, 명확히 더러우면 FAIL, 애매하거나 판단 불가면 REVIEW. "
    "reason에는 판정 근거를 한국어 한 문장으로 써라."
)


def inspect_photo(image_bytes: bytes, mime_type: str, retries: int = 2) -> Inspection:
    """사진 1장 → Gemini 판정. 실패 시 재시도."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            client = genai.Client(api_key=os.getenv("API_KEY"))
            resp = client.models.generate_content(
                model=MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Inspection,
                ),
            )
            return resp.parsed
        except Exception as e:  # ponytail: 전 예외 재시도, 429/일시장애만 걸러야 하면 좁혀라
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise HTTPException(status_code=502, detail=f"Gemini 호출 실패: {last_err}")


@app.get("/health")
def health():
    return {"status": "ok", "api_key_loaded": bool(os.getenv("API_KEY"))}


@app.post("/inspect")
async def inspect(file: UploadFile):
    result = inspect_photo(await file.read(), file.content_type or "image/jpeg")
    return {"verdict": result.verdict, "reason": result.reason}
