from typing import Annotated, List, Optional
import uuid
from fastapi import FastAPI,HTTPException, Response
from dotenv import dotenv_values
import motor.motor_asyncio
from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter
from bson import ObjectId
from pymongo import ReturnDocument

config = dotenv_values(".env")

client = motor.motor_asyncio.AsyncIOMotorClient(config["MONGO_URL"])
db = client.tank_man

app = FastAPI()

PyObjectId = Annotated[str, BeforeValidator(str)]

class Profile(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None) 
    username:  Optional[str] = None 
    role:Optional[str] = None 
    color: Optional[str] = None 
class Tank(BaseModel):
    id:Optional[PyObjectId] = Field(alias="_id", default=None) 
    location: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    

@app.post("/profile", response_model=Profile, status_code=201)
async def create_profile(profile: Profile):
    profile.id = str(uuid.uuid4())
    await db["profiles"].insert_one(profile.dict())
    return profile

@app.get("/profile", response_model=Profile)
async def get_profile():
    profile = await db["profiles"].find_one()
    if profile:
        return profile
    raise HTTPException(status_code=404, detail="Profile not found")



@app.get("/tank")
async def get_tank():
    tanks = await db["tanks"].find().to_list(999)
    return TypeAdapter(List[Tank]).validate_python(tanks)

@app.post("/tank", status_code=201)
async def created_tank(tank: Tank):
    new_tank = await db["tanks"].insert_one(tank.model_dump())

    created_tank = await db["tanks"].find_one({"_id":new_tank.inserted_id})
    return Tank(**created_tank)


@app.patch("/tank/{id}")
async def update_tank(id:str, tank_update: Tank):
    updated_tank = await db["tank"].update_one({"_id": ObjectId(id)}, {"$set": tank_update})

    if updated_tank.modified_count > 0:
        patched_tank = await db["tanks"].find_one({"_id" : ObjectId(id)})
        print(patched_tank)
        return patched_tank
    raise HTTPException(status_code=404,detail="Tank of id:" + id + "not found.")

@app.delete("/tank/{id}")
async def delete_tank(id: str):
    deleted_tank = await db["tanks"].delete_one({"_id": id})
    if deleted_tank.deleted_count > 0:
        return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Tank not found")