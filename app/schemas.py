from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    ADDED = "added"
    CHANGED = "changed"
    REMOVED = "removed"

class CommitType(str, Enum):
    FEAT = "feat"
    FIX = "fix"
    REFACTOR = "refactor"
    PERF = "perf"
    DOCS = "docs"
    TEST = "test"
    STYLE = "style"
    CHORE = "chore"

# --- Структурированные изменения из Git Diff ---
class StructuredChange(BaseModel):
    action: ActionType = Field(..., description="Тип изменения: added, changed, removed")
    text: str = Field(..., description="Читаемое описание пункта на русском языке")
    entity_type: Optional[str] = Field(None, description="Тип сущности (function, class, dto, etc.)")
    entity_name: Optional[str] = Field(None, description="Имя сущности")
    file: Optional[str] = Field(None, description="Путь к файлу")

class AnalysisResponse(BaseModel):
    changes: List[StructuredChange]

# --- Генерация Conventional Commit ---
class CommitResponse(BaseModel):
    type: CommitType = Field(..., description="Тип коммита согласно Conventional Commits (feat, fix, refactor и т.д.)")
    scope: str = Field(..., description="Модуль или компонент (на английском)")
    message: str = Field(..., description="Текст сообщения коммита в повелительном наклонении (на английском, без type/scope префикса)")

# --- Генерация Pull Request ---
class PullRequestResponse(BaseModel):
    title: str = Field(..., description="Заголовок PR в imperative mood (на английском)")
    description: str = Field(..., description="Описание PR (на русском): общая суть и сгруппированные детали изменений")