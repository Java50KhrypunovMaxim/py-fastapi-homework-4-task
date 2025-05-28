from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError





router = APIRouter()

@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=201)
async def create_profile(
    user_id: int,
    profile: ProfileCreateSchema = Depends(),
    avatar: UploadFile = File(...),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="accounts/login")),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client)
):
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    try:
        payload = decode_token(token)
        token_user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this profile.")

    user = get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or not active.")

    if user_has_profile(user_id):
        raise HTTPException(status_code=400, detail="User already has a profile.")

    validate_image(avatar)

    try:
        avatar_filename = f"{user_id}_avatar.jpg"
        avatar_url = s3_client.upload_file(avatar.file, "avatars", avatar_filename)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload avatar. Please try again later.")

    new_profile = create_user_profile(user_id=user_id, **profile.dict(), avatar=avatar_url)

    return ProfileResponseSchema(
        id=new_profile.id,
        user_id=user_id,
        first_name=new_profile.first_name,
        last_name=new_profile.last_name,
        gender=new_profile.gender,
        date_of_birth=new_profile.date_of_birth,
        info=new_profile.info,
        avatar=avatar_url
    )
