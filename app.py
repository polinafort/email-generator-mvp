import streamlit as st
import requests
from prompt import build_planner_prompt, build_writer_prompt, safe_parse_json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma2:2b"  # должно совпадать с `ollama list`


def ollama_generate(prompt: str, *, temperature: float, num_predict: int) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": num_predict,
            "repeat_penalty": 1.1,
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    return (r.json().get("response") or "").strip()


def fallback_plan(campaign_type: str) -> dict:
    mapping = {
        "Анонс фичи/продукта": {
            "preset_id": "feature",
            "blocks": ["intro", "how_it_works", "benefits", "steps", "requirements", "cta", "help_link", "help"],
            "benefits_title": "Преимущества",
            "cta_text": "Включить",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Акция/скидка/спецпредложение": {
            "preset_id": "promo",
            "blocks": ["intro", "offer", "benefits", "promo_terms", "cta", "help_link", "help"],
            "benefits_title": "Что вы получите",
            "cta_text": "Воспользоваться предложением",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Вебинар/ивент": {
            "preset_id": "webinar",
            "blocks": ["intro", "event_details", "agenda", "registration_steps", "cta", "help_link", "help"],
            "benefits_title": "Почему стоит прийти",
            "cta_text": "Зарегистрироваться",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Праздник/поздравление": {
            "preset_id": "holiday",
            "blocks": ["holiday_greeting", "intro", "benefits", "cta", "help"],
            "benefits_title": "Что полезного",
            "cta_text": "Перейти",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": False,
            "notes": "fallback",
        },
        "Дайджест/новости": {
            "preset_id": "newsletter",
            "blocks": ["intro", "benefits", "cta", "help_link", "help"],
            "benefits_title": "Главное",
            "cta_text": "Открыть",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Реактивация (вернуть пользователя)": {
            "preset_id": "reactivation",
            "blocks": ["intro", "benefits", "steps", "cta", "help_link", "help"],
            "benefits_title": "Что изменилось",
            "cta_text": "Попробовать снова",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Опрос/NPS/обратная связь": {
            "preset_id": "survey",
            "blocks": ["intro", "cta", "help"],
            "benefits_title": "Зачем это нужно",
            "cta_text": "Пройти опрос",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": False,
            "notes": "fallback",
        },
        "Другое (опишите в цели и контексте)": {
            "preset_id": "newsletter",
            "blocks": ["intro", "benefits", "cta", "help_link", "help"],
            "benefits_title": "Главное",
            "cta_text": "Подробнее",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
    }
    return mapping.get(campaign_type, mapping["Другое (опишите в цели и контексте)"])


def sanitize_plan(plan: dict, campaign_type: str) -> dict:
    """
    Страховка: если это не промо, выкидываем промо-блоки и убираем промо-лексикон из заголовков.
    Так вы гарантированно не получите «Условия акции» в анонсе фичи.
    """
    plan = plan or {}
    blocks = plan.get("blocks") or []

    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"

    if not is_promo:
        # 1) Удаляем промо-блоки
        blocks = [b for b in blocks if b not in ("offer", "promo_terms")]

        # 2) Если нужны условия/ограничения — это requirements (а не promo_terms)
        if "requirements" not in blocks:
            if "cta" in blocks:
                idx = blocks.index("cta")
                blocks.insert(idx, "requirements")
            else:
                blocks.append("requirements")

        # 3) Подчищаем benefits_title, если он вдруг “съехал” в акцию
        bt = (plan.get("benefits_title") or "").lower()
        if any(word in bt for word in ["акц", "скид", "промокод", "услов"]):
            plan["benefits_title"] = "Преимущества"

    # Для promo наоборот — убеждаемся, что нужные блоки на месте
    if is_promo:
        if "offer" not in blocks:
            blocks.insert(1, "offer") if blocks else blocks.append("offer")
        if "promo_terms" not in blocks:
            # обычно условия лучше ближе к CTA
            if "cta" in blocks:
                idx = blocks.index("cta")
                blocks.insert(idx, "promo_terms")
            else:
                blocks.append("promo_terms")

    plan["blocks"] = blocks
    return plan


st.set_page_config(page_title="Email Generator (Smart Templates)", layout="centered")
st.title("Генератор рассылок: авто-шаблон + умные блоки")

with st.form("form"):
    campaign_type = st.selectbox(
        "Тип рассылки",
        [
            "Анонс фичи/продукта",
            "Акция/скидка/спецпредложение",
            "Вебинар/ивент",
            "Праздник/поздравление",
            "Дайджест/новости",
            "Реактивация (вернуть пользователя)",
            "Опрос/NPS/обратная связь",
            "Другое (опишите в цели и контексте)",
        ],
    )

    topic = st.text_input(
        "Тема/что за рассылка (кратко)",
        placeholder="Напр.: «Новый экспорт в CSV» / «Вебинар про отчёты» / «Поздравление с праздником»",
    )

    audience = st.text_input("ЦА", placeholder="Напр.: владельцы сайтов, маркетологи, пользователи тарифа PRO")
    goal = st.text_input("Цель", placeholder="Напр.: довести до включения / увеличить регистрации / собрать ответы")

    desired_length = st.selectbox("Желаемая длина", ["short", "medium"], index=0)

    must_include = st.text_area(
        "Обязательные пункты (что точно должно быть в письме)",
        placeholder="Списком. Напр.:\n- Где включить\n- Инструкция\n- Ограничения\n- Даты/время (если вебинар)\n- Условия (если акция)\n- Контакт поддержки",
        height=180,
    )

    culture = st.text_area(
        "Тон/культура компании (опционально)",
        placeholder="Напр.: на «вы», коротко, без эмодзи, без канцелярита, дружелюбно-деловой",
        height=90,
    )

    context = st.text_area(
        "Контекст/детали (опционально)",
        placeholder="Любые детали: даты/время/ссылка, условия акции, кому доступно, где находится кнопка, и т.д.",
        height=120,
    )

    submitted = st.form_submit_button("Сгенерировать")


if submitted:
    if not campaign_type or not topic or not audience or not goal or not must_include:
        st.error("Заполните минимум: тип рассылки, тема, ЦА, цель, обязательные пункты.")
        st.stop()

    # 1) Planner
    planner_prompt = build_planner_prompt(
        campaign_type=campaign_type,
        audience=audience,
        goal=goal,
        topic=topic,
        must_include=must_include,
        culture=culture,
        context=context,
        desired_length=desired_length,
    )

    with st.spinner("Подбираю шаблон и блоки..."):
        try:
            raw_plan = ollama_generate(planner_prompt, temperature=0.1, num_predict=320)
            plan = safe_parse_json(raw_plan)
        except Exception:
            plan = fallback_plan(campaign_type)

    # Санитарная правка плана, чтобы не было «Условия акции» вне промо-сценария
    plan = sanitize_plan(plan, campaign_type)

    # 2) Writer
    writer_prompt = build_writer_prompt(
        plan=plan,
        campaign_type=campaign_type,
        audience=audience,
        goal=goal,
        topic=topic,
        must_include=must_include,
        culture=culture,
        context=context,
        desired_length=desired_length,
    )

    with st.spinner("Пишу письмо..."):
        try:
            result = ollama_generate(writer_prompt, temperature=0.8, num_predict=1100)
        except Exception as e:
            st.error("Не удалось получить ответ от модели. Проверьте Ollama и имя модели в app.py.")
            st.code(str(e))
            st.stop()

    st.subheader("План (что выбрал ИИ)")
    st.json(plan)

    st.subheader("Результат")
    st.markdown(result)

    st.subheader("Скопировать (Markdown)")
    st.code(result)
