from fastapi import APIRouter, HTTPException, Depends, status
from talkingdb.clients.sqlite import sqlite_conn, GRAPH_DB
from talkingdb.helpers.auth import hash_password, verify_password, verify_service_secret
from talkingdb.helpers.jwt import create_access_token, get_current_user
from talkingdb.models.auth.auth import (
    SignupRequest,
    SignupResponse,
    LoginRequest,
    LoginResponse,
    ServiceApiKeyRequest,
    ServiceApiKeyResponse,
)
from talkingdb.models.auth.api_key import APIKeyModel
from talkingdb.models.auth.user import UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest):
    try:
        with sqlite_conn(GRAPH_DB) as conn:
            UserModel.create(
                conn=conn,
                email=payload.email,
                password_hash=hash_password(
                    payload.password
                ),
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return SignupResponse(
        message="Account created successfully"
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(payload: LoginRequest):
    with sqlite_conn(GRAPH_DB) as conn:
        user = UserModel.find_by_email(
            conn,
            payload.email,
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        {"sub": user.email}
    )

    return LoginResponse(
        access_token= token,
        message= "Successfully logged in"
    )


@router.post("/api-keys")
def create_api_key(user_email: str = Depends(get_current_user)):

    with sqlite_conn(GRAPH_DB) as conn:
        api_key_obj = APIKeyModel.create(
            conn=conn,
            user_email=user_email,
        )

    return {
        "api_key": api_key_obj.api_key,
        "created_at": api_key_obj.created_at,
    }


@router.post(
    "/service/api-keys",
    response_model=ServiceApiKeyResponse,
    dependencies=[Depends(verify_service_secret)],
)
def get_or_create_service_api_key(payload: ServiceApiKeyRequest):
    with sqlite_conn(GRAPH_DB) as conn:
        api_key_obj = APIKeyModel.get_or_create(
            conn=conn,
            user_email=payload.email.lower(),
        )

    return {
        "api_key": api_key_obj.api_key,
        "created_at": api_key_obj.created_at,
    }