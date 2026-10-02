from fastapi import Header, HTTPException, status
from config import settings


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key != settings.api_auth_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key
