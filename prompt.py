import json

STYLE_RULES = """
Пиши по-русски. Стиль: дружелюбно-деловой B2B, на «вы».
Формат: короткие абзацы (1–3 строки), много воздуха. Без эмодзи, без канцелярита.
Не выдумывай факты: даты, проценты, скидки, промокоды, сроки. Если нет данных — ставь плейсхолдеры: [дата], [время], [промокод], [ссылка].
«Обязательные пункты» должны быть включены (дословно или очень близко по смыслу).
""".strip()

PROMO_FORBIDDEN = """
Если тип рассылки НЕ «Акция/скидка/спецпредложение», запрещено использовать:
«акция», «скидка», «промокод», «условия акции», «правила акции», «участвовать в акции».
Вместо этого: «Что учитывать», «Ограничения», «Важно», «Условия доступа».
""".strip()

HEADING_RULES = """
Правила заголовков:
- Нельзя использовать «/» и нельзя использовать «…».
- Заголовки должны быть осмысленными под текущую тему.
- Для шагов используй один вариант (без синонимов): например «Как начать пользоваться», «Как зарегистрироваться».
""".strip()

# Заголовок для блока шагов по типу рассылки
STEPS_HEADING_BY_TYPE = {
    "Анонс фичи/продукта": "Как начать пользоваться",
    "Акция/скидка/спецпредложение": "Как воспользоваться предложением",
    "Вебинар/ивент": "Как зарегистрироваться",
    "Праздник/поздравление": "Поздравляем!",
    "Дайджест/новости": "",
    "Реактивация (вернуть пользователя)": "Как вернуться к использованию",
    "Опрос/NPS/обратная связь": "Как пройти опрос",
    "Другое (опишите в цели и контексте)": "Как начать",
}

# Библиотека блоков для плана
BLOCK_LIBRARY = {
    "intro": "Короткий человеческий интро-текст (1–2 абзаца) до подзаголовков.",
    "how_it_works": "Подзаголовок «Как это работает?» + 1 абзац.",
    "instruction_link": "Подзаголовок «Инструкция …» и отдельной строкой ссылка (Markdown link).",
    "benefits": "Подзаголовок выгод + 3–6 буллетов (начинать со *).",
    "steps": "Подзаголовок шагов (как в steps_heading) + 3–7 шагов (нумерованный список).",
    "requirements": "Подзаголовок «Что учитывать?» + 2–5 буллетов.",
    "offer": "Промо-блок (только для акции): что за предложение (без выдумок).",
    "promo_terms": "Подзаголовок «Условия акции» (только для акции): сроки/промокод/ограничения (или плейсхолдеры).",
    "event_details": "Подзаголовок «Детали вебинара» + 3–6 строк (дата/время/формат) (или плейсхолдеры).",
    "agenda": "Подзаголовок «Программа» + 3–6 буллетов.",
    "holiday_greeting": "Подзаголовок «Поздравляем!» или короткий тёплый блок (1 абзац).",
    "cta": "Подзаголовок-CTA (например «Попробуйте … прямо сейчас!») + 1 строка ниже «Подробнее — …»",
    "help": "Финальный абзац: «Если нужна помощь — ответьте на письмо или напишите в поддержку.»",
}

TEMPLATE_PRESETS = {
    "feature": ["intro", "how_it_works", "instruction_link", "benefits", "steps", "requirements", "cta", "help"],
    "promo": ["intro", "offer", "benefits", "promo_terms", "cta", "help"],
    "webinar": ["intro", "event_details", "agenda", "cta", "help"],
    "holiday": ["holiday_greeting", "intro", "benefits", "cta", "help"],
    "newsletter": ["intro", "benefits", "cta", "help"],
    "reactivation": ["intro", "benefits", "steps", "cta", "help"],
    "survey": ["intro", "cta", "help"],
}

def _blocks_md() -> str:
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
    link_url: str,
) -> str:
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"
    promo_guard = "" if is_promo else PROMO_FORBIDDEN

    steps_heading = STEPS_HEADING_BY_TYPE.get(campaign_type, "Как начать")

    return f"""
Ты — email-маркетолог. Составь план письма: какие блоки нужны и как их назвать.

{STYLE_RULES}
{HEADING_RULES}
{promo_guard}

Вводные:
- Тип рассылки: {campaign_type}
- Тема: {topic}
- ЦА: {audience}
- Цель: {goal}
- Длина: {desired_length} (short/medium)
- Ссылка (если дана): {link_url if link_url else "НЕ ДАНА"}

Обязательные пункты:
{must_include}

Тон/культура (если есть):
{culture}

Контекст (если есть):
{context}

Доступные пресеты: {", ".join(TEMPLATE_PRESETS.keys())}
Библиотека блоков:
{_blocks_md()}

Правила:
- Для «Анонс фичи/продукта» обычно нужны how_it_works + benefits + steps + requirements.
- Для «Вебинар/ивент» нужны event_details (+ agenda по возможности), steps обычно НЕ нужен.
- Если ссылка дана и это не праздник/дайджест, добавь instruction_link (особенно для фичи).
- Если это не promo — не добавляй offer/promo_terms.
- Заголовок steps должен быть ровно: «{steps_heading}» (если steps есть).

Верни СТРОГО JSON (без текста вокруг):

{{
  "preset_id": "feature|promo|webinar|holiday|newsletter|reactivation|survey",
  "blocks": ["intro", "...", "cta", "help"],
  "steps_heading": "{steps_heading}",
  "benefits_title": "Преимущества ... (под тему)",
  "instruction_title": "Инструкция ... (под тему)",
  "cta_title": "Короткий CTA-заголовок (под тему, с ! можно)",
  "use_link": true,
  "notes": "1 короткая причина"
}}
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
    link_url: str,
) -> str:
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"
    promo_guard = "" if is_promo else PROMO_FORBIDDEN

    blocks = plan.get("blocks", []) or []
    blocks_md = "\n".join([f"- {b}: {BLOCK_LIBRARY.get(b, '')}" for b in blocks])

    steps_heading = (plan.get("steps_heading") or "").strip()
    if "steps" in blocks and not steps_heading:
        steps_heading = STEPS_HEADING_BY_TYPE.get(campaign_type, "Как начать")

    benefits_title = (plan.get("benefits_title") or "Преимущества").strip()
    instruction_title = (plan.get("instruction_title") or "Инструкция").strip()
    cta_title = (plan.get("cta_title") or "Подробнее").strip()

    # ссылка: если дали — используем, если нет — плейсхолдер
    final_link = link_url.strip() if link_url and link_url.strip() else "https://[вставьте-ссылку]"

    # для непро-мо: прямое правило против "условия акции"
    nonpromo_fix = ""
    if not is_promo:
        nonpromo_fix = "Нельзя писать «Условия акции». Если нужны условия/ограничения — это только блок «Что учитывать?»."

    return f"""
Ты — опытный email-маркетолог и редактор.

{STYLE_RULES}
{HEADING_RULES}
{promo_guard}
{nonpromo_fix}

Ссылка для вставки (используй её, если в письме нужен блок со ссылкой):
{final_link}

Вводные:
- Тип рассылки: {campaign_type}
- Тема: {topic}
- ЦА: {audience}
- Цель: {goal}
- Длина: {desired_length} (short/medium)

План блоков (строго в этом порядке):
{blocks_md}

Настройки заголовков:
- benefits_title: {benefits_title}
- instruction_title: {instruction_title}
- steps_heading (если блок steps есть): {steps_heading}
- cta_title: {cta_title}

Обязательные пункты (встроить в письмо):
{must_include}

Тон/культура:
{culture}

Контекст:
{context}

Верни результат строго в таком Markdown-формате (как в примере):

# Прехедер
(1–2 предложения)

# Письмо
(1–2 коротких абзаца интро)

## Как это работает?
(если есть блок how_it_works)

## {instruction_title}
(если есть instruction_link)
(одной строкой Markdown-ссылка на {final_link})

## {benefits_title}
* ...
* ...

## {steps_heading}
(если есть steps)
1. ...
2. ...

## Что учитывать?
(если есть requirements)
* ...
* ...

## {cta_title}
Подробнее — в Справке: {final_link}

Если нужна помощь — ответьте на письмо или напишите в поддержку.

Самопроверка:
- Заголовки без «/» и без «…».
- Если не promo — нет слов «акция/скидка/промокод/условия акции».
- Обязательные пункты включены.
""".strip()


def safe_parse_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)
