import time
from typing import Any, Dict

import jwt

from src.config import CONFIG
from src.auth.exceptions import JWTSecretUndefined, JWTSecretFileNotFound


def get_jwt_secret() -> str:
    """
    Gets the `JWT_SECRET` env variable. If not set, `JWT_SECRET_FILE` is
    read and `JWT_SECRET` set from its content.

    Raises:
        `JWTSecretUndefined`: Raised if the `JWT_SECRET` is not set and cannot
            be read from `JWT_SECRET_FILE`
        `JWTSecretFileNotFound`: If the given `JWT_SECRET_FILE` is not found.

    Returns:
        `str`: jwt secret
    """

    if CONFIG.JWT_SECRET:
        return CONFIG.JWT_SECRET

    elif CONFIG.JWT_SECRET_FILE:
        try:
            with open(CONFIG.JWT_SECRET_FILE, "r") as f:
                jwt_secret = f.read().strip()

            if jwt_secret:
                return jwt_secret

        except FileNotFoundError:
            raise JWTSecretFileNotFound(CONFIG.JWT_SECRET_FILE)

    raise JWTSecretUndefined


JWT_SECRET: str = get_jwt_secret()
JWT_ALGORITHM = CONFIG.JWT_ALGORITHM


def token_response(token: str):
    return {"access_token": token}


def signJWT(
    expiry: float | None = None, **payload: dict[str, Any]
) -> Dict[str, Any]:
    """
    Encodes a given payload

    Args:
        `expiry` (float | None, optional): Expiry time of the JWT.
            Defaults to None.

    Returns:
        Dict[str, Any]: a dict containing the access_token


    ### Note:
    * `JWT_SECRET` env variable should be set to the jwt secret
    * `JWT_ALGORITHM` env variable should be set to the algorithm to use

    ## Example

    ```Python
    import time

    from src.auth.auth_handler import signJWT

    # signed JWT with an expiry of 1 day
    signedJWT = signJWT(expiry=time.time() + 86400, {'user_id': '1234', 'email': 'one@one.com'})

    print(signedJWT.access_token)   # prints the encoded jwt
    ```
    """
    _payload = {**payload, "exp": expiry or time.time() + 86400}
    token = jwt.encode(_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)


def decodeJWT(token: str, audience: str | None = None) -> dict:
    """
    Decodes provided JWT.

    Args:
        `token` (str): JWT to decode.
        `audience` (str | None): audience of the token. Defaults to None.

    Returns:
        dict: Decoded JWT.

    ### Note:
    * `JWT_SECRET` env variable should be set to the jwt secret
    * `JWT_ALGORITHM` env variable should be set to the algorithm to use
    """
    try:
        decoded_token = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience=audience
        )

        return decoded_token if decoded_token["exp"] >= time.time() else None
    except Exception:
        return {}
