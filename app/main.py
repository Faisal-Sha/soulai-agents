from fastapi import FastAPI
# imports of routers
from app.api.chat import router as chat_router


app = FastAPI()
    
# adding chat router to the main app
app.include_router(chat_router)

@app.get("/")
def home():
    return{
"message": "Welcome to SoulPlus AI Backend!"
    }