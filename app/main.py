from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router


app = FastAPI()
# add cors to allow all 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat API
app.include_router(chat_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to SoulPlus AI Backend!"
    }


