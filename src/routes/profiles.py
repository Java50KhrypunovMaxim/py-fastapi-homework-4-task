from sqlalchemy import select
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_s3_storage_client
from src.database.models.accounts import UserModel
from src.database.session_sqlite import get_sqlite_db
from src.models.profile import ProfileModel
from src.schemas.profiles import ProfileCreateSchema, ProfileResponseSchema
from src.storages.interfaces import S3StorageInterface
from src.validation.profile import validate_image

router = APIRouter()

def decode_token(token: str, secret_key: str, algorithms: list) -> dict:
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

async def get_user_by_id(user_id: int, db: AsyncSession) -> Optional[UserModel]:
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def user_has_profile(user_id: int, db: AsyncSession) -> bool:
    stmt = select(ProfileModel).where(ProfileModel.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()
    return profile is not None

async def create_user_profile(user_id: int, first_name: str, last_name: str, gender: str, date_of_birth: str, info: Optional[str], avatar_url: str, db: AsyncSession):
    new_profile = ProfileModel(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        info=info,
        avatar_url=avatar_url
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=201)
async def create_profile(
    user_id: int,
    profile: ProfileCreateSchema = Depends(),
    avatar: UploadFile = File(...),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="accounts/login")),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    db: AsyncSession = Depends(get_sqlite_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header is missing")


    SECRET_KEY = "your-secret-key"
    ALGORITHMS = ["HS256"]

    try:
        payload = decode_token(token, secret_key=SECRET_KEY, algorithms=ALGORITHMS)
        token_user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this profile.")

    user = await get_user_by_id(user_id, db)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or not active.")

    if await user_has_profile(user_id, db):
        raise HTTPException(status_code=400, detail="User already has a profile.")

    validate_image(avatar)

    try:
        avatar_filename = f"{user_id}_avatar.jpg"
        avatar_url = await s3_client.upload_file(avatar.file, "avatars", avatar_filename)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload avatar. Please try again later.")

    new_profile = await create_user_profile(
        user_id=user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=str(profile.date_of_birth),
        info=profile.info,
        avatar_url=avatar_url,
        db=db
    )

    return ProfileResponseSchema(
        id=new_profile.id,
        user_id=user_id,
        first_name=new_profile.first_name,
        last_name=new_profile.last_name,
        gender=new_profile.gender,
        date_of_birth=new_profile.date_of_birth,
        info=new_profile.info,
        avatar_url=avatar_url
    )
