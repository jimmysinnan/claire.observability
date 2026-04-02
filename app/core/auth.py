from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


def validate_token(x_api_token: str = Header(default="")) -> str:
    if x_api_token != settings.api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")
    return x_api_token


def token_dependency(_: str = Depends(validate_token)) -> None:
    return None
