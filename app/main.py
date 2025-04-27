from fastapi import FastAPI
from handlers import router

app = FastAPI(
    title="OTUS HL Architect",
    version="1.2.0"
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)