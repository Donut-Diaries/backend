from typing import Annotated

from fastapi import APIRouter, Depends

from src.auth.jwt_bearer import SupabaseJWTBearer, SupabaseJWTPayload


consumer_router = APIRouter(prefix="/users", tags=["consumer"])


@consumer_router.get("/me")
def me(
    credentials: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
) -> SupabaseJWTPayload:
    return credentials
