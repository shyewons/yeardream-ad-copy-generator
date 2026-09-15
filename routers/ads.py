import logging

from fastapi import APIRouter, HTTPException

from schemas.ad import AdRequest, AdCopy
from services.ad_generator import AdGenerationError, generate_ad_copy

logger = logging.getLogger(__name__)

ERROR_RESPONSES = {
    "MODEL_UNAVAILABLE": (503, "광고 생성 모델에 연결할 수 없어요. Ollama 실행 상태를 확인해주세요."),
    "MODEL_TIMEOUT": (504, "모델 응답 대기 시간을 초과했어요. 잠시 후 다시 시도해주세요."),
    "INVALID_MODEL_OUTPUT": (502, "광고 형식을 맞추지 못했어요. 다시 생성해주세요."),
    "MODEL_NOT_FOUND": (503, "설정된 광고 생성 모델을 찾을 수 없어요. 모델 설치 상태를 확인해주세요."),
    "MODEL_ERROR": (502, "모델에서 요청을 처리하지 못했어요. 잠시 후 다시 시도해주세요."),
}

router = APIRouter(prefix="/ads", tags=["ads"])

# response_model=AdCopy : API의 최종 응답 구조를 FastAPI에 알려줌
@router.post("/generate", response_model=AdCopy)
def generate_ads(request : AdRequest):
    try:
        return generate_ad_copy(request)
    except AdGenerationError as error:
        logger.exception("Ad generation failed: %s", error.code)
        status, message = ERROR_RESPONSES[error.code]
        raise HTTPException(status_code=status, detail={"code": error.code, "message": message}) from error
    except Exception as error:
        logger.exception("Unexpected ad generation failure")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": "서버에서 오류가 발생했어요. 잠시 후 다시 시도해주세요."},
        ) from error
