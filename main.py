from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routers.ads import router as ads_router

app = FastAPI()
app.include_router(ads_router)

VIEW_DIR = Path(__file__).resolve().parent / "view"
app.mount("/static", StaticFiles(directory=VIEW_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(VIEW_DIR / "index.html")

# @app.get("/")
# def main() :
#     return {"Hello": "World"}
