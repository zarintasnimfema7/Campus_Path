import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status

from clerk_backend_api import (
    AuthenticateRequestOptions,
    authenticate_request,
)


load_dotenv()


CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

CLERK_AUTHORIZED_PARTIES = [
    item.strip()
    for item in os.getenv(
        "CLERK_AUTHORIZED_PARTIES",
        "http://localhost:3000",
    ).split(",")
    if item.strip()
]


if not CLERK_SECRET_KEY:
    raise RuntimeError(
        "CLERK_SECRET_KEY is missing from environment variables."
    )


async def get_current_user(
    request: Request,
):
    try:
        auth_state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=CLERK_SECRET_KEY,
                authorized_parties=CLERK_AUTHORIZED_PARTIES,
                accepts_token=["session_token"],
            ),
        )

        if not auth_state.is_signed_in:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
            )

        user_id = auth_state.payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID was not found in the token.",
            )

        return {
            "id": user_id,
            "session_id": auth_state.payload.get("sid"),
        }

    except HTTPException:
        raise

    except Exception as error:
        print("Clerk authentication error:", error)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )