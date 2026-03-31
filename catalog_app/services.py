"""
Vision AI 서비스 모듈
─────────────────────
B2B e카탈로그 MVP: 배경 제거(누끼 따기) 단일 파이프라인
  remove_background(input_path) → PNG bytes
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image
from rembg import remove

logger = logging.getLogger(__name__)


def remove_background(input_path: str | Path) -> bytes:
    """
    rembg(U2Net)로 제품 이미지 배경을 제거하고 투명 PNG bytes를 반환합니다.

    Args:
        input_path: 원본 업로드 이미지 절대 경로

    Returns:
        배경이 투명 처리된 PNG 바이트 데이터

    Raises:
        FileNotFoundError: 파일 경로가 잘못된 경우
        Exception: rembg 내부 오류
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {input_path}")

    logger.info(f"[BG Remove] 처리 시작: {input_path.name}")

    with open(input_path, 'rb') as f:
        raw = f.read()

    # rembg 처리 — 첫 실행 시 U2Net 모델 자동 다운로드 (~170MB)
    output_bytes: bytes = remove(raw)

    # RGBA 변환 후 PNG로 직렬화 (투명 채널 보존)
    img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
    logger.info(f"[BG Remove] 완료: 크기={img.size}, 모드={img.mode}")

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()
