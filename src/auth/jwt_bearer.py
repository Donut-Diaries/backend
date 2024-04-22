from pydantic import BaseModel
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing_extensions import Annotated, Doc

from src.auth.utils import decodeJWT


class SupabaseJWTPayload(BaseModel):
    """
    The result of using `SupabaseJWTBearer` in a dependency.

    Includes `sub`, `email`, `phone`, `is_anonymous` and `user_metadata`
    fields of the payload.
    """

    sub: Annotated[str, Doc("UUID of the user")]
    email: Annotated[
        str,
        Doc(
            """
            Email of the user.
            
            If user is anonymous the email will be an empty string
            """
        ),
    ]
    phone: Annotated[
        str,
        Doc(
            """
            Phone number of the user
            
            If user is anonymous or has not set phone number it will
            be an empty string
            """
        ),
    ]
    is_anonymous: Annotated[bool, Doc("Whether the user is anonymous")]
    user_metadata: Annotated[
        dict,
        Doc(
            """
            Additional data about the user
            
            `is_customer` is set to true for a customer user.
            `is_vendor` is set to true for a vendor user.
            """
        ),
    ]


class SupabaseJWTBearer(HTTPBearer):
    """
    HTTP Bearer Authenticator for Supabase JWT.

    ## Usage

    Create an instance object and use that object as the dependency in `Depends()`.

    The dependency result will be an `SupabaseJWTPayload` object.

    ## Example

    ```python
    from typing import Annotated

    from fastapi import Depends, FastAPI

    from src.auth.jwt_bearer import SupabaseJWTBearer
    from src.auth.schema import SupabaseJWTPayload


    app = FastAPI()


    @app.get("/users/me")
    def read_current_user(
        payload: Annotated[SupabaseJWTPayload, Depends(SupabaseJWTBearer())]
    ):
        return payload
    ```
    """

    def __init__(self):
        super(SupabaseJWTBearer, self).__init__()

    async def __call__(self, request: Request) -> Optional[SupabaseJWTPayload]:
        credentials: HTTPAuthorizationCredentials = await super(
            SupabaseJWTBearer, self
        ).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )

            payload = decodeJWT(credentials.credentials, "authenticated")

            if not payload:
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )

            return SupabaseJWTPayload(**payload)
        else:
            raise HTTPException(
                status_code=403, detail="Invalid authorization code."
            )
