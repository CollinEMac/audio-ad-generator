from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/generate-ad")
def generate_ad(brand: str = Form(...)):
    return JSONResponse({"message": f"Received brand: {brand}"})
