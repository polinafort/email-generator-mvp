import json

# Короткий референс: только структура/подача (не “сюжет”).
# Полный текст эталона лучше НЕ вставлять, маленькие модели начинают тащить слова/смыслы.
IDEAL_STYLE_REFERENCE = """
РЕФЕРЕНС СТИЛЯ (не копировать дословно):
- 1 строка заголовок-приглашение/анонс
- 1–2 коротких абзаца «что изменилось и почему полезно»
- блок «Как это работает»
- блок «Преимущества …» списком
- блок «Как подключить/включить …» шагами
- блок «Что учитывать …» списком
- CTA отдельной строкой (может повториться 1–2 раза)
- «Подробнее — в Справке: [ссылка]»
- финал: «если нужна помощь — ответьте на письмо/напишите в поддержку»
""".strip()

STYLE_RULES = """
Пиши по-русски. Тон: дружелюбно-деловой B2B, на «вы».
Формат: короткие абзацы (1–3 строки), много воздуха.
Без эмодзи, без канцелярита, без “воды”. Пишите просто и по делу.

Ключевое:
- Письмо должно выглядеть как написанное человеком.
- Не выдумывай факты (цифры, даты, скидки, сроки). Если данных нет — ставь плейсхолдер: [дата], [время], [ссылка], [промокод].
- Обязательные пункты должны быть включены (дословно или очень близко по смыслу).
""".strip()

PROMO_FORBIDDEN = """
ЗАПРЕТ ДЛЯ НЕ-АКЦИЙ:
Если это НЕ «Акция/скидка/спецпредложение», нельзя использовать:
«акция», «скидка», «промокод», «условия акции», «правила акции», «участвовать в акции».

Если нужно описать условия/ограничения — используй нейтральные заголовки:
«Что учитывать», «Ограничения», «Важно», «Условия доступа».
""".strip()

BLOCK_LIBRARY = {
    "intro": "Короткое вступление (1–2 абзаца): о чём письмо и зачем читателю.",
    "how_it_works": "Подзаголовок «Как это работает» + 1 абзац.",
    "benefits": "Подзаголовок (осмысленный под тему) + 4–7 буллетов выгод.",
    "steps": "Подзаголовок «Как …» + 4–8 шагов (нумерованный список).",
    "requirements": "Подзаголовок «Что учитывать …» + 3–6 буллетов нюансов/ограничений.",
    "offer": "Блок предложения (только для акции): что даём/кому.",
    "promo_terms": "Условия акции (только для акции): сроки/ограничения/промокод (или плейсхолдеры).",
    "event_details": "Детали вебинара: тема, дата/время, формат, запись (или плейсхолдеры).",
    "agenda": "Программа вебинара: 3–6 пунктов.",
    "registration_steps": "Регистрация: 2–4 шага.",
    "holiday_greeting": "Поздравление + аккуратный мостик к теме.",
    "cta": "CTA отдельной строкой: «…» и ниже строка «Ссылка: [вставьте ссылку]».",
    "help_link": "«Подробнее — в Справке: [вставьте ссылку]» или «Подробнее: [вставьте ссылку]».",
    "help": "Финальный абзац: предложить помощь (ответить на письмо/написать в поддержку).",
}

TEMPLATE_PRESETS = {
    "feature": ["intro", "how_it_works", "benefits", "steps", "requirements", "cta", "help_link", "help"],
    "promo": ["intro", "offer", "benefits", "promo_terms", "cta", "help_link", "help"],
    "webinar": ["intro", "event_details", "agenda", "registration_steps", "cta", "help_link", "help"],
    "holiday": ["holiday_greeting", "intro", "benefits", "cta", "help"],
    "newsletter": ["intro", "benefits", "cta", "help_link", "help"],
    "reactivation": ["intro", "benefits", "steps", "cta", "help_link", "help"],
    "survey": ["intro", "cta", "help"],
}

def _blocks_md():
    return "\n".join([f"- {k}: {v}" for k, v in BLOCK_LIBRARY.items()])


def build_planner_prompt(
    campaign_type: str,
    audience: str,
    goal: str,
    topic: str,
    must_include: str,
    culture: str,
    context: str,
    desired_length: str,
) -> str:
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"
    promo_guard = "" if is_promo else PROMO_FORBIDDEN

    return f"""
Ты — сильный email-маркетолог. Сначала составь план письма: выбери пресет и блоки.

{STYLE_RULES}
{promo_guard}

{IDEAL_STYLE_REFERENCE}

Вводные:
- Тип рассылки: {campaign_type}
- Тема: {topic}
- ЦА: {audience}
- Цель: {goal}
- Длина: {desired_length} (short/medium)

Обязательные пункты (их надо встроить в блоки письма):
{must_include}

Тон/культура (если есть, соблюдай):
{culture}

Контекст (если есть, используй для конкретики):
{context}

Доступные пресеты: {", ".join(TEMPLATE_PRESETS.keys())}

Блоки (что можно включать):
{_blocks_md()}

Правила выбора:
- feature: если анонс/обучение по фиче, нужны steps/requirements.
- promo: только если реально акция/скидка/промокод.
- webinar: только если вебинар/ивент (нужны event_details и registration_steps).
- holiday: поздравление, без тех.блоков, если не просят.
- survey: коротко, 1 CTA на опрос.

Верни СТРОГО JSON (без текста вокруг):

{{
  "preset_id": "feature|promo|webinar|holiday|newsletter|reactivation|survey",
  "blocks": ["intro", "...", "cta", "help"],
  "benefits_title": "Осмысленный заголовок выгод под тему (НЕ «Условия акции»)",
  "cta_text": "Короткий текст CTA под цель",
  "cta_link_placeholder": "[вставьте ссылку]",
  "include_help_link": true,
  "notes": "почему выбран этот план"
}}

Важно:
- Если это не promo — НИКОГДА не добавляй offer/promo_terms.
""".strip()


def build_writer_prompt(
    plan: dict,
    campaign_type: str,
    audience: str,
    goal: str,
    topic: str,
    must_include: str,
    culture: str,
    context: str,
    desired_length: str,
) -> str:
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"
    promo_guard = "" if is_promo else PROMO_FORBIDDEN

    blocks = plan.get("blocks", [])
    blocks_md = "\n".join([f"- {b}: {BLOCK_LIBRARY.get(b, '')}" for b in blocks])

    # Жёсткая подсказка для заголовка "conditions" в НЕ-promo сценариях
    nonpromo_heading_rule = ""
    if not is_promo:
        nonpromo_heading_rule = "Если нужен блок про ограничения/условия — называй его только «Что учитывать» или «Важно». Никогда не «Условия акции»."

    return f"""
Ты — опытный email-маркетолог и редактор. Напиши письмо строго по плану.

{STYLE_RULES}
{promo_guard}
{nonpromo_heading_rule}

{IDEAL_STYLE_REFERENCE}

Вводные:
- Тип рассылки: {campaign_type}
- Тема: {topic}
- ЦА: {audience}
- Цель: {goal}
- Длина: {desired_length} (short/medium)

План блоков (строго в этом порядке):
{blocks_md}

Настройки:
- Заголовок блока выгод: {plan.get("benefits_title", "Преимущества")}
- CTA текст: {plan.get("cta_text", "Подробнее")}
- CTA ссылка: {plan.get("cta_link_placeholder", "[вставьте ссылку]")}
- include_help_link: {plan.get("include_help_link", True)}

Обязательные пункты (встроить в письмо):
{must_include}

Тон/культура:
{culture}

Контекст:
{context}

Выход: верни строго Markdown:

## Тема (3 варианта)
- ...
- ...
- ...

## Прехедер
...

## Письмо (готово к отправке)
Требования к телу письма:
- 3–8 коротких абзацев + списки/шаги по необходимости
- CTA оформляй отдельной строкой: например «{plan.get("cta_text", "Подробнее")}» и отдельной строкой «Ссылка: {plan.get("cta_link_placeholder", "[вставьте ссылку]")}»
- Если include_help_link=true — добавь строку «Подробнее — в Справке: [вставьте ссылку]»
- Финал: 1–2 строки “если нужна помощь…”

Самопроверка перед ответом:
- Текст соответствует теме «{topic}» и цели.
- Нет промо-слов (если это не акция).
- Все обязательные пункты присутствуют.
""".strip()


def safe_parse_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)
