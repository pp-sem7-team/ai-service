import glob
import json
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from app.schemas import AnalysisResponse, CommitResponse, PullRequestResponse

load_dotenv()

# Инициализация клиента Groq
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY", "")
)

MODEL_NAME = "qwen/qwen3.8-27b"
OUTPUT_FILE = "evaluation_report.txt"

# Системные промпты для трех этапов
DIFF_SYSTEM_PROMPT = (
    "Ты — эксперт AI-инженер. Проанализируй raw_diff и разбей его на логические изменения.\n"
    "ТРЕБОВАНИЯ:\n"
    "1. Ответ строго в формате JSON с корневым ключом 'changes' (массив).\n"
    "2. Поле 'action': 'added', 'changed', 'removed'.\n"
    "3. Поле 'text' — НА РУССКОМ ЯЗЫКЕ.\n"
    "4. Никакого лишнего текста, только чистый JSON."
)

COMMIT_SYSTEM_PROMPT = (
    "Ты — профессиональный разработчик. На основе изменений сформируй Conventional Commit.\n"
    "ТРЕБОВАНИЯ:\n"
    "1. 'type': feat, fix, refactor, perf, docs, test, style, chore.\n"
    "2. 'scope': модуль (на английском).\n"
    "3. 'message': описание в imperative mood (на английском, без type/scope).\n"
    "4. Ответ строго в формате JSON."
)

PR_SYSTEM_PROMPT = (
    "Ты — тимлид. На основе контекста изменений ветки сгенерируй PR.\n"
    "ТРЕБОВАНИЯ:\n"
    "1. 'title': заголовок на английском в imperative mood.\n"
    "2. 'description': описание НА РУССКОМ ЯЗЫКЕ (суть + детали по компонентам).\n"
    "3. Ответ строго в формате JSON."
)

def evaluate_all_diffs():
    diff_files = glob.glob("diffs/*.diff")
    if not diff_files:
        print("❌ Ошибка: В папке diffs/ не найдены файлы для тестирования!")
        return

    # Буфер для накопления отчета
    report_lines = []

    def log(text: str = ""):
        """Печатает текст в консоль и сохраняет его в общий список для файла."""
        print(text)
        report_lines.append(text)

    log(f"📊 Найдено файлов для комплексного анализа: {len(diff_files)}")
    log("=" * 60)

    for idx, file_path in enumerate(diff_files, 1):
        filename = os.path.basename(file_path)
        is_broken = "broken" in filename
        
        log(f"\n🔹 ФАЙЛ [{idx}/{len(diff_files)}]: {filename} {'(Chaos / Stress Test)' if is_broken else ''}")
        log("-" * 60)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_diff = f.read()

        # --- Шаг 1: Анализ Diff (analyze-diff) ---
        log("⏳ Шаг 1: Выполнение analyze-diff...")
        changes_summary_text = ""
        branch_context_text = ""
        
        try:
            start_time = time.time()
            resp_diff = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": DIFF_SYSTEM_PROMPT},
                    {"role": "user", "content": f"raw_diff:\n{raw_diff}"}
                ],
                temperature=0.1,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            diff_latency = round(time.time() - start_time, 2)
            parsed_diff = AnalysisResponse.model_validate_json(resp_diff.choices[0].message.content)
            
            log(f"   ✅ Успешно ({diff_latency}s). Найдено изменений: {len(parsed_diff.changes)}")
            for change in parsed_diff.changes:
                log(f"      - [{change.action}] {change.file}: {change.text}")
            
            # Подготовка сводки для следующих шагов
            changes_summary_text = "\n".join([f"- [{c.action}] в {c.file}: {c.text}" for c in parsed_diff.changes])
            branch_context_text = f"Файл: {filename}\nИзменения:\n" + changes_summary_text

        except Exception as e:
            log(f"   ❌ Ошибка на этапе анализа diff: {e}")
            log("=" * 60)
            time.sleep(3)
            continue

        time.sleep(3) # Пауза для избежания лимитов Rate Limit (429)

        # --- Шаг 2: Генерация Коммита (generate-commit) ---
        log("⏳ Шаг 2: Выполнение generate-commit...")
        try:
            start_time = time.time()
            resp_commit = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": COMMIT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Changes summary:\n{changes_summary_text}"}
                ],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            commit_latency = round(time.time() - start_time, 2)
            parsed_commit = CommitResponse.model_validate_json(resp_commit.choices[0].message.content)
            
            log(f"   ✅ Успешно ({commit_latency}s)")
            log(f"      Commit: {parsed_commit.type}({parsed_commit.scope}): {parsed_commit.message}")

        except Exception as e:
            log(f"   ❌ Ошибка генерации коммита: {e}")

        time.sleep(3) # Пауза для избежания лимитов Rate Limit (429)

        # --- Шаг 3: Генерация Pull Request (generate-pr) ---
        log("⏳ Шаг 3: Выполнение generate-pr...")
        try:
            start_time = time.time()
            resp_pr = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": PR_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Branch context:\n{branch_context_text}"}
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            pr_latency = round(time.time() - start_time, 2)
            parsed_pr = PullRequestResponse.model_validate_json(resp_pr.choices[0].message.content)
            
            log(f"   ✅ Успешно ({pr_latency}s)")
            log(f"      PR Title: {parsed_pr.title}")
            log(f"      PR Description:\n{parsed_pr.description}")

        except Exception as e:
            log(f"   ❌ Ошибка генерации PR: {e}")

        log("=" * 60)
        time.sleep(3)

    # Запись всего текстового отчета в отдельный файл
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n✨ Результаты комплексного анализа успешно сохранены в файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    evaluate_all_diffs()