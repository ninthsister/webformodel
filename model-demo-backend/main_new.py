from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import BASE_DIR
from core.cors import setup_cors

from routers import (
    patient,
    analysis,
    images,
    assessment,
    reasoning,
    report,
    keyevidence,
    feedback,
    predict,
)


app = FastAPI(title="Medical AI Model Backend")

setup_cors(app)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/")
def root():
    print("有人进入")
    return {
        "message": "Medical AI backend is running",
        "docs": "/docs",
    }


app.include_router(patient.router)
app.include_router(analysis.router)
app.include_router(images.router)
app.include_router(assessment.router)
app.include_router(reasoning.router)
app.include_router(report.router)
app.include_router(keyevidence.router)
app.include_router(feedback.router)
app.include_router(predict.router)

# 启动命令：
# uvicorn main_new:app --reload --host 0.0.0.0 --port 8000