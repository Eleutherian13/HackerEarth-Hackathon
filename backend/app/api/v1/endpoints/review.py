from __future__ import annotations

from fastapi.responses import JSONResponse


def build_stale_review_response(
    *,
    current_version: int,
    last_modified_by: str | None,
    last_modified_at: str | None,
    message: str = "Field was modified by another reviewer",
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "STALE_DATA",
            "message": message,
            "current_version": current_version,
            "details": {
                "last_modified_by": last_modified_by,
                "last_modified_at": last_modified_at,
            },
        },
    )


__all__ = ["build_stale_review_response"]
