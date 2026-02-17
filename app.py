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
            "steps_heading": "Как начать пользоваться",
            "cta_text": "Начать пользоваться",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Акция/скидка/спецпредложение": {
            "preset_id": "promo",
            "blocks": ["intro", "offer", "benefits", "promo_terms", "cta", "help_link", "help"],
            "benefits_title": "Что вы получите",
            "steps_heading": "",
            "cta_text": "Воспользоваться предложением",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Вебинар/ивент": {
            "preset_id": "webinar",
            "blocks": ["intro", "event_details", "agenda", "registration_steps", "cta", "help_link", "help"],
            "benefits_title": "Почему стоит прийти",
            "steps_heading": "",
            "cta_text": "Зарегистрироваться",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Праздник/поздравление": {
            "preset_id": "holiday",
            "blocks": ["holiday_greeting", "intro", "benefits", "cta", "help"],
            "benefits_title": "Что полезного",
            "steps_heading": "",
            "cta_text": "Перейти",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": False,
            "notes": "fallback",
        },
        "Дайджест/новости": {
            "preset_id": "newsletter",
            "blocks": ["intro", "benefits", "cta", "help_link", "help"],
            "benefits_title": "Главное",
            "steps_heading": "",
            "cta_text": "Открыть",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Реактивация (вернуть пользователя)": {
            "preset_id": "reactivation",
            "blocks": ["intro", "benefits", "steps", "cta", "help_link", "help"],
            "benefits_title": "Что изменилось",
            "steps_heading": "Как вернуться к использованию",
            "cta_text": "Попробовать снова",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
        "Опрос/NPS/обратная связь": {
            "preset_id": "survey",
            "blocks": ["intro", "cta", "help"],
            "benefits_title": "Зачем это нужно",
            "steps_heading": "",
            "cta_text": "Пройти опрос",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": False,
            "notes": "fallback",
        },
        "Другое (опишите в цели и контексте)": {
            "preset_id": "newsletter",
            "blocks": ["intro", "benefits", "cta", "help_link", "help"],
            "benefits_title": "Главное",
            "steps_heading": "",
            "cta_text": "Подробнее",
            "cta_link_placeholder": "[вставьте ссылку]",
            "include_help_link": True,
            "notes": "fallback",
        },
    }
    return mapping.get(campaign_type, mapping["Другое (опишите в цели и контексте)"])


def sanitize_plan(plan: dict, campaign_type: str) -> dict:
    """
    Страховка от промо-блоков и промо-заголовков в непро-мо рассылках.
    """
    plan = plan or {}
    blocks = plan.get("blocks") or []

    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"

    if not is_promo:
        blocks = [b for b in blocks if b not in ("offer", "promo_terms")]

        # если модель всё равно хочет вставить "условия", пусть это будет requirements
        if "requirements" not in blocks:
            if "cta" in blocks:
                idx = blocks.index("cta")
                blocks.insert(idx, "requirements")
            else:
                blocks.append("requirements")

        bt = (plan.get("benefits_title") or "").lower()
        if any(word in bt for word in ["акц", "скид", "промокод", "услов"]):
            plan["benefits_title"] = "Преимущества"

        # если в не-про-мо steps_heading вдруг пустой, оставляем пустым — writer сам подставит по типу
        if plan.get("steps_heading") is None:
            plan["steps_heading"] = ""

    if is_promo:
        if "offer" not in blocks:
            blocks.insert(1, "offer") if blocks else blocks.append("offer")
        if "promo_terms" not in blocks:
            if "cta" in blocks:
                idx = blocks.index("cta")
                blocks.insert(idx, "promo_terms")
            else:
                blocks.append("promo_terms")

    plan["blocks"] = blocks
    return plan


st.set_page_config(page_title="Email Generator", layout="centered")
st.title("Генератор рассылок")

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

    topic = st.text_input("Тема/что за рассылка (кратко)", placeholder="Напр.: «Экспорт в CSV»")
    audience = st.text_input("ЦА", placeholder="Напр.: владельцы сайтов, маркетологи")
    goal = st.text_input("Цель", placeholder="Напр.: довести до использования / увеличить регистрации")

    desired_length = st.selectbox("Желаемая длина", ["short", "medium"], index=0)

    must_include = st.text_area(
        "Обязательные пункты (что точно должно быть в письме)",
        placeholder="Списком. Например:\n- Где включить\n- Шаги\n- Ограничения\n- Ссылка на справку\n- Куда писать за помощью",
        height=180,
    )

    culture = st.text_area(
        "Тон/культура компании (опционально)",
        placeholder="Напр.: на «вы», коротко, без канцелярита",
        height=90,
    )

    context = st.text_area(
        "Контекст/детали (опционально)",
        placeholder="Даты/ссылки/условия/где кнопка/что важно учесть и т.д.",
        height=120,
    )

    submitted = st.form_submit_button("Сгенерировать письмо")


if submitted:
    if not topic or not audience or not goal or not must_include:
        st.error("Заполните минимум: тема, ЦА, цель, обязательные пункты.")
        st.stop()

    # 1) Planner (внутренний шаг)
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

    with st.spinner("Генерирую..."):
        try:
            raw_plan = ollama_generate(planner_prompt, temperature=0.1, num_predict=320)
            plan = safe_parse_json(raw_plan)
        except Exception:
            plan = fallback_plan(campaign_type)

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

        try:
            result = ollama_generate(writer_prompt, temperature=0.8, num_predict=1100)
        except Exception as e:
            st.error("Не удалось получить ответ от модели. Проверьте Ollama и имя модели в app.py.")
            st.code(str(e))
            st.stop()

    # Публикуем только результат
    st.subheader("Готовое письмо")
    st.markdown(result)

    st.subheader("Markdown для копирования")
    st.code(result)
