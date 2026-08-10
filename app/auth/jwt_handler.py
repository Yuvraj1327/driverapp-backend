"""
JWT decoding helper used by the auth dependency layer.
"""
from jose import JWTError

from app.core.security import decode_token
from app.schemas.auth import TokenPayload


class InvalidTokenError(Exception):
    pass


def parse_token(token: str, expected_type: str = "access") -> TokenPayload:
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise InvalidTokenError("Could not validate credentials") from exc

    token_data = TokenPayload(**payload)
    if token_data.type != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token")
    return token_data
