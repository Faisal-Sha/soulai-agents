import uvicorn

if __name__ == "__main__":
    # reload=False avoids Windows spawn/reload crashes while editing files
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=False,
    )