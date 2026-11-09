from openai import OpenAI
from app.config import GROQ_API_KEY, MODEL_NAME
from app.schemas import AnalysisResponse, CommitResponse, PullRequestResponse

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY,
)

# --- Промпт для Git Diff ---
DIFF_ANALYSIS_PROMPT = """
Ты — эксперт AI-инженер и код-ревьюер. Проанализируй переданный raw_diff и разбей его на логически цельные изменения.
ТРЕБОВАНИЯ:
1. Ответ должен быть строго в формате JSON с корневым ключом 'changes' (массив объектов).
2. Поле 'action' должно строго принимать одно из трех значений: "added", "changed", "removed".
3. Поле 'text' ДОЛЖНО быть читаемым описанием НА РУССКОМ ЯЗЫКЕ. Запрещено дублировать код!
4. Заполни поля 'entity_type', 'entity_name' и 'file', если они применимы.
5. Никаких markdown-оберток (типа ```json), только чистый JSON.
"""

# --- Промпт для Conventional Commits ---
COMMIT_PROMPT = """
Ты — профессиональный разработчик. На основе переданных структурированных изменений сформируй сообщение коммита в формате Conventional Commits.
ТРЕБОВАНИЯ:
1. 'type' должен быть одним из: feat, fix, refactor, perf, docs, test, style, chore.
2. 'scope' — компонент или модуль (на английском).
3. 'message' — краткое описание на английском в повелительном наклонении (imperative mood), БЕЗ префикса типа и скоупа.
4. Ответ строго в формате JSON без лишнего текста и markdown-оберток.
"""

# --- Промпт для Pull Request ---
PR_PROMPT = """
Ты — тимлид. На основе накопленного контекста изменений ветки сгенерируй заголовок и описание Pull Request.
ТРЕБОВАНИЯ:
1. 'title' — заголовок PR на английском языке в imperative mood (например: "Implement user authentication service").
2. 'description' — описание НА РУССКОМ ЯЗЫКЕ, состоящее из:
   - 1-2 общих предложений о сути проделанной работы.
   - Списка деталей, сгруппированных по компонентам/модулям (на основе путей к файлам).
3. Ответ строго в формате JSON без markdown-оберток.
"""

def analyze_git_diff(raw_diff: str) -> AnalysisResponse:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": DIFF_ANALYSIS_PROMPT},
            {"role": "user", "content": f"raw_diff:\n{raw_diff}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return AnalysisResponse.model_validate_json(response.choices[0].message.content)

def generate_commit_message(changes_summary: str) -> CommitResponse:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": COMMIT_PROMPT},
            {"role": "user", "content": f"Changes:\n{changes_summary}"}
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return CommitResponse.model_validate_json(response.choices[0].message.content)

def generate_pull_request(branch_context: str) -> PullRequestResponse:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": PR_PROMPT},
            {"role": "user", "content": f"Branch changes context:\n{branch_context}"}
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return PullRequestResponse.model_validate_json(response.choices[0].message.content)