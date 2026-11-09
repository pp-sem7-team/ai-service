import os
import sys
import io
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import MODEL_NAME
from app.services.llm import analyze_git_diff, generate_commit_message, generate_pull_request

# Принудительная кодировка UTF-8 для корректного вывода кириллицы в консоли Windows
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

app = FastAPI(
    title="Git Context AI Service",
    version="1.0.0",
    description="Микросервис на FastAPI для анализа git diff, генерации коммитов и PR с использованием Groq API"
)

class DiffRequest(BaseModel):
    raw_diff: str

class CommitRequest(BaseModel):
    changes_summary: str

class PullRequestRequest(BaseModel):
    branch_context: str

@app.get("/health")
def health_check():
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/api/v1/analyze-diff")
def endpoint_analyze_diff(payload: DiffRequest):
    """Анализ сырого Git diff и возврат структурированных изменений"""
    try:
        result = analyze_git_diff(payload.raw_diff)
        return {"status": "success", "data": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки diff: {str(e)}")

@app.post("/api/v1/generate-commit")
def endpoint_generate_commit(payload: CommitRequest):
    """Генерация Conventional Commit сообщения на основе изменений"""
    try:
        result = generate_commit_message(payload.changes_summary)
        return {"status": "success", "data": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации коммита: {str(e)}")

@app.post("/api/v1/generate-pr")
def endpoint_generate_pr(payload: PullRequestRequest):
    """Генерация заголовка и описания Pull Request"""
    try:
        result = generate_pull_request(payload.branch_context)
        return {"status": "success", "data": result.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации PR: {str(e)}")