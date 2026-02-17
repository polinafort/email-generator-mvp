import json

# Короткий референс по манере (не текст, чтобы модель не тащила слова/сюжет)
IDEAL_STYLE_REFERENCE = """
РЕФЕРЕНС СТИЛЯ (не копировать дословно):
- 1 строка заголовок-приглашение/анонс
- 1–2 коротких абзаца «что и почему полезно»
- уместные подзаголовки
- списки выгод
- пошаговый блок «Как ...» (если нужен)
- блок «Что учитывать» (если нужны ограничения)
- CTA отдельной строкой
- «Подробнее — в Справке: [ссылка]» (если уместно)
- финал: «если нужна помощь — ответьте на письмо/напишите в поддержку»
""".strip()

STYLE_RULES = """
Пиши по-русски. Тон: дружелюбно-деловой B2B, на «вы».
Формат: короткие абзацы (1–3 строки), много воздуха.
Без эмодзи, без канцелярита, без “воды”.

Факты:
- Не выдумывай даты, проценты, скидки, сроки, промокоды, гарантии. Если данных нет — плейсхолдеры: [дата], [время], [ссылка], [промокод].
- Обязательные пункты должны быть включены (дословно или очень близко по смыслу).
""".strip()

PROMO_FORBIDDEN = """
ЗАПРЕТ ДЛЯ НЕ-АКЦИЙ:
Если это НЕ «Акция/скидка/спецпредложение», нельзя использовать:
«акция», «скидка», «промокод», «условия акции», «правила акции», «участвовать в акции».

Если нужно описать условия/ограничения — используй нейтральные заголовки:
«Что учитывать», «Ограничения», «Важно», «Условия доступа».
""".strip()

HEADING_RULES = """
Формат заголовков:
- В заголовках нельзя использовать «/» и нельзя использовать «…».
- Заголовки короткие и конкретные.
- Для блока шагов используй ровно один глагол: «Как начать пользоваться» ИЛИ «Как зарегистрироваться» ИЛИ «Как настроить» и т.п. (без вариантов через слеш).
""".strip()

# "Правильные" заголовки для блока шагов по типу рассылки
STEPS_HEADING_BY_TYPE = {
    "Анонс фичи/продукта": "Как начать пользоваться",
    "Акция/скидка/спецпредложение": "Как воспользоваться предложением",
    "Вебинар/ивент": "Как зарегистрироваться",
    "Праздник/поздравление": "",  # обычно шаги не нужны
    "Дайджест/новости": "",       # обычно шаги не нужны
    "Реактивация (вернуть пользователя)": "Как вернуться к использованию",
    "Опрос/NPS/обратная связь": "Как пройти опрос",
    "Другое (опишите в цели и контексте)": "Как начать",
}

BLOCK_LIBRARY = {
    "intro": "Короткое вступление (1–2 абзаца): о чём письмо и зачем читателю.",
    "how_it_works": "Подзаголовок «Как это работает» + 1 абзац.",
    "benefits": "Заголовок выгод (под тему) + 4–7 буллетов.",
    "steps": "Пошаговый блок: заголовок «<STEPS_HEADING>» + 4–8 шагов (нумерованный список).",
    "requirements": "Подзаголовок «Что учитывать» (или «Важно/Ограничения») + 3–6 буллетов нюансов.",
    "offer": "Блок предложения (только для акции): что даём/кому/суть (без выдумок).",
    "promo_terms": "Условия акции (только для акции): сроки/ограничения/промокод (или плейсхолдеры).",
    "event_details": "Детали вебинара: тема, дата/время, формат, запись (или плейсхолдеры).",
    "agenda": "Программа вебинара: 3–6 пунктов.",
    "registration_steps": "Регистрация: 2–4 шага (если нужен отдельный блок помимо steps).",
    "holiday_greeting": "Поздравление + аккуратный мостик к теме.",
    "cta": "CTA отдельной строкой: 2–5 слов. Ниже строка «Ссылка: [вставьте ссылку]». Без «…».",
    "help_link": "Строка «Подробнее — в Справке: [вставьте ссылку]» или «Подробнее: [вставьте ссылку]».",
    "help": "Финал: предложить помощь (ответить на письмо/написать в поддержку).",
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
) -> str:
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"
    promo_guard = "" if is_promo else PROMO_FORBIDDEN

    steps_heading = STEPS_HEADING_BY_TYPE.get(campaign_type, "Как начать")
    steps_note = f"Для блока steps используй заголовок: «{steps_heading}»." if steps_heading else "Для этого типа рассылки блок steps обычно не нужен."

    return f"""
Ты — сильный email-маркетолог. Сначала составь план письма: выбери пресет и блоки.

{STYLE_RULES}
{HEADING_RULES}
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

Подсказка по шагам:
- {steps_note}

Доступные пресеты: {", ".join(TEMPLATE_PRESETS.keys())}

Блоки (что можно включать):
{_blocks_md()}

Правила выбора:
- feature: анонс/обучение по фиче (steps/requirements часто нужны).
- promo: только если реально акция/скидка/промокод.
- webinar: вебинар/ивент (нужны event_details и registration_steps; steps обычно не нужен).
- holiday: поздравление (без how_it_works/steps, если явно не просят).
- survey: коротко, 1 CTA на опрос.

Верни СТРОГО JSON (без текста вокруг):

{{
  "preset_id": "feature|promo|webinar|holiday|newsletter|reactivation|survey",
  "blocks": ["intro", "...", "cta", "help"],
  "benefits_title": "Осмысленный заголовок выгод под тему",
  "steps_heading": "{steps_heading if steps_heading else ""}",
  "cta_text": "Короткий CTA под цель (без «…»)",
  "cta_link_placeholder": "[вставьте ссылку]",
  "include_help_link": true,
  "notes": "почему выбран этот план"
}}

Важно:
- Если это не promo — НИКОГДА не добавляй offer/promo_terms.
- Если в blocks нет steps, поле steps_heading оставь пустым.
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

    blocks = plan.get("blocks", []) or []
    blocks_md = "\n".join([f"- {b}: {BLOCK_LIBRARY.get(b, '')}" for b in blocks])

    steps_heading = (plan.get("steps_heading") or "").strip()

    nonpromo_heading_rule = ""
    if not is_promo:
        nonpromo_heading_rule = "Если нужен блок про ограничения/условия — называй его «Что учитывать» или «Важно». Никогда не «Условия акции»."

    steps_heading_rule = ""
    if "steps" in blocks:
        # Если planner не заполнил — подставим дефолт по типу
        if not steps_heading:
            steps_heading = STEPS_HEADING_BY_TYPE.get(campaign_type, "Как начать")
        steps_heading_rule = f"Для блока steps используй заголовок РОВНО: «{steps_heading}» (без «/» и без «…»)."
    else:
        steps_heading_rule = "Блок steps не используй, если его нет в плане."

    return f"""
Ты — опытный email-маркетолог и редактор. Напиши письмо строго по плану.

{STYLE_RULES}
{HEADING_RULES}
{promo_guard}
{nonpromo_heading_rule}
{steps_heading_rule}

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
- 3–10 коротких абзацев + списки/шаги по необходимости
- CTA оформляй отдельной строкой: «{plan.get("cta_text", "Подробнее")}»
- Следующей строкой: «Ссылка: {plan.get("cta_link_placeholder", "[вставьте ссылку]")}»
- Если include_help_link=true — добавь строку «Подробнее — в Справке: [вставьте ссылку]»
- Финал: 1–2 строки “если нужна помощь…”

Самопроверка перед ответом:
- Заголовки без «/» и без «…».
- Если есть steps — заголовок steps ровно «{steps_heading}».
- Текст соответствует теме и цели, использует вводные.
- Если это не promo — нет слов «акция/скидка/промокод/условия акции».
- Все обязательные пункты присутствуют.
""".strip()


def safe_parse_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)
