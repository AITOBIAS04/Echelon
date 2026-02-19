"""Standalone server entry point for the verification API."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from echelon_verify.api import router

app = FastAPI(title="Echelon Verification API", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run(
        "echelon_verify.server:app",
        host="0.0.0.0",
        port=8100,
        reload=False,
    )


if __name__ == "__main__":
    main()
