import json

STYLE_RULES = """
Пиши по-русски. Стиль: дружелюбно-деловой B2B, на «вы», без сленга, без эмодзи, без канцелярита.
Короткие абзацы, много воздуха. Уместны списки и шаги.

ВАЖНО:
- «Идеальный пример» — только ориентир по подаче (воздух, заголовки, списки), НЕ копируй его текст.
- Заголовки и формулировки должны быть осмысленно адаптированы под тему (акция/вебинар/праздник/фича и т.д.).
- Не выдумывай факты (цифры, сроки, скидки, даты), если их нет во вводных. Если данных нет — ставь плейсхолдеры: [дата], [ссылка], [промокод].
- «Обязательные пункты» должны быть включены (дословно или очень близко по смыслу).
"""

# Блоки — это “кирпичики”, из которых планировщик собирает письмо.
BLOCK_LIBRARY = {
    "intro": "Короткое вступление: о чём письмо и зачем читателю (1–2 абзаца).",
    "how_it_works": "«Как это работает» (1 абзац) — только если релевантно (для фич/процессов).",
    "benefits": "«Преимущества» (4–7 буллетов) — ценность для читателя.",
    "steps": "«Как подключить/сделать» (4–8 шагов) — нумерованный список, если нужна инструкция.",
    "requirements": "«Что учитывать» (3–6 буллетов): ограничения, условия, нюансы.",
    "offer": "Блок про предложение/акцию: что даём, на каких условиях, до какого срока, для кого.",
    "promo_terms": "Условия акции: ограничения, сроки, промокод, исключения (без выдумок).",
    "event_details": "Детали вебинара/ивента: тема, дата/время, формат, спикеры (если есть), запись.",
    "agenda": "Программа/план вебинара: 3–6 пунктов.",
    "registration_steps": "Как зарегистрироваться: 2–4 шага.",
    "holiday_greeting": "Поздравление/тёплый абзац + аккуратный мостик к продукту (если уместно).",
    "social_proof": "Соцдоказательство (очень осторожно): «нам уже пишут/часто спрашивают» без цифр.",
    "help": "Абзац «Если нужна помощь — ответьте на письмо/напишите в поддержку».",
    "ps": "P.S. (опционально) — короткая полезная ремарка.",
    "cta": "CTA строкой (как кнопка): «…» + ссылка плейсхолдером.",
    "help_link": "«Подробнее — в Справке: [вставьте ссылку]» или «Подробнее: [вставьте ссылку]».",
}


TEMPLATE_PRESETS = {
    # пресеты — стартовая точка; planner может добавлять/убирать блоки
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
    """
    Планировщик: выбирает пресет и финальный список блоков.
    Выход: строгий JSON.
    """
    return f"""
Ты — email-маркетолог. Сначала составь ПЛАН письма: выбери шаблон и блоки.

Стиль и правила:
{STYLE_RULES}

Тип рассылки (от пользователя): {campaign_type}
Тема/событие/фича: {topic}
ЦА: {audience}
Цель: {goal}
Желаемая длина: {desired_length} (short/medium)

Обязательные пункты:
{must_include}

Тон/культура компании (если есть):
{culture}

Контекст (если есть):
{context}

Доступные пресеты (можно использовать как основу):
- feature, promo, webinar, holiday, newsletter, reactivation, survey

Библиотека блоков (что можно включать/исключать):
{_blocks_md()}

Твоя задача:
1) Выбери preset_id (один из списка).
2) Собери итоговый список blocks (порядок важен). Можно добавить/убрать блоки относительно пресета.
3) Придумай CTA-текст (cta_text) и тип ссылки (cta_link_placeholder).
4) Укажи нужен ли help_link (true/false). Для вебинара/акции обычно ссылка нужна, для праздника — опционально.
5) Укажи заголовок для блока преимуществ (benefits_title) — он должен соответствовать теме (не “преимущества авторасстановки рекламы” всегда).

Верни СТРОГО JSON без текста вокруг:

{{
  "preset_id": "feature|promo|webinar|holiday|newsletter|reactivation|survey",
  "blocks": ["intro", "...", "cta", "help"],
  "benefits_title": "Преимущества ...",
  "cta_text": "…",
  "cta_link_placeholder": "[вставьте ссылку]",
  "include_help_link": true,
  "notes": "1 короткая причина выбора блоков"
}}

Ограничения:
- Не включай steps/how_it_works, если это не нужно (например, праздник/поздравление).
- Для promo обязательно добавь offer + promo_terms (если во вводных есть условия/сроки; если нет — плейсхолдеры).
- Для webinar обязательно event_details + registration_steps.
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
    blocks = plan.get("blocks", [])
    blocks_md = "\n".join([f"- {b}: {BLOCK_LIBRARY.get(b, '')}" for b in blocks])

    return f"""
Ты — опытный email-маркетолог и редактор.

{STYLE_RULES}

Вводные:
- Тип рассылки: {campaign_type}
- Тема/событие/фича: {topic}
- ЦА: {audience}
- Цель: {goal}
- Длина: {desired_length} (short/medium)

План письма (строго следуй блокам и их порядку):
{blocks_md}

Настройки из плана:
- Заголовок для блока преимуществ: {plan.get("benefits_title", "Преимущества")}
- CTA-текст: {plan.get("cta_text", "Подробнее")}
- CTA-ссылка: {plan.get("cta_link_placeholder", "[вставьте ссылку]")}
- include_help_link: {plan.get("include_help_link", True)}

Обязательные пункты (включи в письмо):
{must_include}

Тон/культура компании (если пусто — игнорируй):
{culture}

Контекст (если пусто — игнорируй):
{context}

Верни строго в Markdown:

## Тема (3 варианта)
- ...
- ...
- ...

## Прехедер
...

## Письмо (готово к отправке)
(короткие абзацы, много воздуха, 1–2 CTA строкой)

Самопроверка перед ответом:
- Блоки соответствуют типу рассылки.
- Нет лишних “технических” блоков там, где они не нужны.
- Обязательные пункты учтены.
""".strip()


def safe_parse_json(text: str) -> dict:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)
