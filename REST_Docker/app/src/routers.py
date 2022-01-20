import shutil
import pymongo
from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    File, 
    Form,
    UploadFile
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm

from .models import (
    UserModel,
    ShowUserModel,
    UpdateUserModel
)
from .dependecies import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_password_hash
)
from .settings import db, ACCESS_TOKEN_EXPIRE_MINUTES

from typing import List, Optional
from datetime import datetime, timedelta

import re

router = APIRouter()

# ============= Creating path operations ==============
@router.post("/create", response_description="Add new user", response_model=UserModel)
async def create_user(user: UserModel):
    if re.match("student|prof|TA", user.role):
        datetime_now = datetime.now()
        user.created_at = datetime_now.strftime("%m/%d/%y %H:%M:%S")
        user.password = get_password_hash(user.password)
        user = jsonable_encoder(user)
        new_user = await db["users"].insert_one(user)
        await db["users"].update_one({"_id": new_user.inserted_id}, {
                                     "$rename": {"password": "hashed_pass"}})

        created_user = await db["users"].find_one({"_id": new_user.inserted_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)

    raise HTTPException(status_code=406, detail="User role not acceptable")


@router.post("/uploadfile", response_description ='Upload a file')
async def upload_file(
    file:  UploadFile = File(...), file_name: str = Form(...)
):
    return {
        "file_content_type": file.content_type,
        "file_name": file_name,
    }

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorect ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["_id"]}, expires_delta=access_token_expires
    )
    await db["users"].update_one({"_id": form_data.username}, {"$set": {
        "last_login": datetime.now().strftime("%m/%d/%y %H:%M:%S"),
        "is_active": "true"
    }})

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/list", response_description="List all users", response_model=List[ShowUserModel])
async def list_users(sortBy: str = None, offset: int= 0, count: Optional[int] = None):
    users = await db["users"].find().to_list(1000)
    
    def get_param(user):
        return user[sortBy]
    
    if sortBy:
        users.sort(key = get_param)
    #    print(users)
    
    if count:
        if count > len(users) or offset >= len(users):
            raise HTTPException(status_code=405, detail="Not allowed")
        return users[offset:offset+count]
    else:
        return users[offset:]
        # return users

@router.get("/list/{user_id}", response_description="Get user by ID", response_model=List[ShowUserModel])
async def get_user_by_id(user_id: str):
    users = await db["users"].find().to_list(1000)
    for user in users:
        if user["_id"] == user_id:
            # print(user['_id'])
            return [user]
    
@router.get("/current", response_description="Current User", response_model=ShowUserModel)
async def current_user(current_user: ShowUserModel = Depends(get_current_user)):
    return current_user


@router.delete("/{user_id}", response_description="Delete a user")
async def delete_user(user_id: str):
    delete_result = await db["users"].delete_one({"_id": user_id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"User {user_id} not found")
