from fastapi import FastAPI
from api.endpoints import router

app = FastAPI(title="Talent Scout API")
app.include_router(router)