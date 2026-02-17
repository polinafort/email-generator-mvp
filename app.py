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


def fallback_plan(campaign_type: str, link_url: str) -> dict:
    # Минимальные планы на случай, если planner вернёт некорректный JSON
    if campaign_type == "Вебинар/ивент":
        return {
            "preset_id": "webinar",
            "blocks": ["intro", "event_details", "agenda", "cta", "help"],
            "steps_heading": "Как зарегистрироваться",
            "benefits_title": "Почему стоит прийти",
            "instruction_title": "Ссылка на регистрацию",
            "cta_title": "Зарегистрируйтесь на вебинар",
            "use_link": True if link_url else False,
            "notes": "fallback",
        }

    if campaign_type == "Акция/скидка/спецпредложение":
        return {
            "preset_id": "promo",
            "blocks": ["intro", "offer", "benefits", "promo_terms", "cta", "help"],
            "steps_heading": "Как воспользоваться предложением",
            "benefits_title": "Что вы получите",
            "instruction_title": "Подробнее об условиях",
            "cta_title": "Воспользуйтесь предложением",
            "use_link": True if link_url else False,
            "notes": "fallback",
        }

    # по умолчанию — фича/обычное письмо
    blocks = ["intro", "how_it_works", "benefits", "steps", "requirements", "cta", "help"]
    if link_url:
        blocks.insert(2, "instruction_link")  # после how_it_works
    return {
        "preset_id": "feature",
        "blocks": blocks,
        "steps_heading": "Как начать пользоваться",
        "benefits_title": "Преимущества",
        "instruction_title": "Инструкция",
        "cta_title": "Попробуйте прямо сейчас",
        "use_link": True if link_url else False,
        "notes": "fallback",
    }


def sanitize_plan(plan: dict, campaign_type: str, link_url: str) -> dict:
    """
    Страховка: убираем промо-блоки из НЕ promo и добавляем instruction_link, если ссылка дана.
    """
    plan = plan or {}
    blocks = plan.get("blocks") or []
    is_promo = campaign_type.strip() == "Акция/скидка/спецпредложение"

    if not is_promo:
        blocks = [b for b in blocks if b not in ("offer", "promo_terms")]

    # если ссылка дана — добавим instruction_link для сценариев, где это обычно полезно
    if link_url and link_url.strip():
        if campaign_type in (
            "Анонс фичи/продукта",
            "Реактивация (вернуть пользователя)",
            "Опрос/NPS/обратная связь",
            "Другое (опишите в цели и контексте)",
        ):
            if "instruction_link" not in blocks:
                if "how_it_works" in blocks:
                    blocks.insert(blocks.index("how_it_works") + 1, "instruction_link")
                elif "intro" in blocks:
                    blocks.insert(blocks.index("intro") + 1, "instruction_link")
                else:
                    blocks.insert(0, "instruction_link")

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

    topic = st.text_input("Тема/что за рассылка (кратко)", placeholder="Напр.: «ИИ-помощник в Директе»")
    audience = st.text_input("ЦА", placeholder="Напр.: маркетологи, владельцы бизнеса")
    goal = st.text_input("Цель", placeholder="Напр.: довести до использования / увеличить регистрации")

    link_url = st.text_input(
        "Ссылка (если есть) — справка/лендинг/регистрация",
        placeholder="Напр.: https://yandex.ru/support/...",
    )

    desired_length = st.selectbox("Желаемая длина", ["short", "medium"], index=0)

    must_include = st.text_area(
        "Обязательные пункты (что точно должно быть в письме)",
        placeholder="Списком. Например:\n- Где включить\n- Шаги\n- Ограничения\n- Контакт поддержки",
        height=180,
    )

    culture = st.text_area(
        "Тон/культура компании (опционально)",
        placeholder="Напр.: на «вы», коротко, без канцелярита",
        height=90,
    )

    context = st.text_area(
        "Контекст/детали (опционально)",
        placeholder="Детали: где кнопка, кому доступно, условия доступа, дата/время вебинара и т.д.",
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
        link_url=link_url,
    )

    with st.spinner("Генерирую письмо..."):
        try:
            raw_plan = ollama_generate(planner_prompt, temperature=0.1, num_predict=320)
            plan = safe_parse_json(raw_plan)
        except Exception:
            plan = fallback_plan(campaign_type, link_url)

        plan = sanitize_plan(plan, campaign_type, link_url)

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
            link_url=link_url,
        )

        try:
            result = ollama_generate(writer_prompt, temperature=0.8, num_predict=1200)
        except Exception as e:
            st.error("Не удалось получить ответ от модели. Проверьте Ollama и имя модели в app.py.")
            st.code(str(e))
            st.stop()

    st.subheader("Готовое письмо (Markdown)")
    st.markdown(result)

    st.subheader("Скопировать Markdown")
    st.code(result)
