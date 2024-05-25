import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.users import router as users_router
from router.devices import router as devices_router
from router.admin import router as admin_router
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#Root greeting
@app.get("/")
async def root():
    return {"message": "Hello API"}
 
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(admin_router, prefix='/admin', tags=["admin"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port="8000", reload=True)