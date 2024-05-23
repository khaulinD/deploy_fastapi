from fastapi import Cookie, HTTPException, Response

from starlette import status

COOKIE_ACCESS_TOKEN = "access_token"
COOKIE_REFRESH_TOKEN = "refresh_token"


# def get_cookie_data(
#     # token: str = Cookie(alias=COOKIE_ACCESS_TOKEN),
#         response: Response
# ) -> dict:
#     token = response.cookies.get("access_token")
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="not authenticated",
#         )
#
#     return token

# def check_token_validity(token: str) -> bool:
