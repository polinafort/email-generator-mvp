import streamlit as st
import requests
from prompt import build_prompt

# Если были проблемы с localhost — используйте 127.0.0.1
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# ВАЖНО: имя должно совпадать с тем, что показывает `ollama list`
MODEL = "gemma2:2b"


def ollama_generate(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "num_predict": 850,
            "repeat_penalty": 1.1,
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()


st.set_page_config(page_title="Email Generator MVP", layout="centered")
st.title("Генератор email-рассылки (MVP)")

with st.form("email_form"):
    st.subheader("Параметры письма")

    audience = st.text_input(
        "ЦА (кто читает)",
        placeholder="Напр.: владельцы сайтов, издатели, маркетологи, пользователи продукта",
    )

    goal = st.text_input(
        "Цель рассылки",
        placeholder="Напр.: пригласить в бета-тест и довести до включения фичи",
    )

    feature_name = st.text_input(
        "Название фичи/инициативы (1–5 слов)",
        placeholder="Напр.: авторазмещение блоков / экспорт в CSV / новый отчёт по конверсиям",
    )

    must_include = st.text_area(
        "Обязательные пункты (что точно должно быть в письме)",
        placeholder="Напр.:\n- Где включить\n- Пошаговая инструкция\n- Что учитывать перед запуском\n- Куда писать за помощью",
        height=190,
    )

    st.subheader("Стиль и контекст")

    culture = st.text_area(
        "Культура/тон компании (опционально)",
        placeholder="Напр.: дружелюбно-деловой тон, на «вы», короткие абзацы, без эмодзи, без канцелярита",
        height=110,
    )

    context = st.text_area(
        "Контекст/продукт (опционально)",
        placeholder="Напр.: что за продукт, для кого, какие ограничения/условия, что сейчас доступно",
        height=110,
    )

    submitted = st.form_submit_button("Сгенерировать письмо")


if submitted:
    if not audience or not goal or not feature_name or not must_include:
        st.error("Заполните минимум: ЦА, цель, название фичи, обязательные пункты.")
        st.stop()

    prompt = build_prompt(
        audience=audience,
        goal=goal,
        feature_name=feature_name,
        must_include=must_include,
        culture=culture,
        context=context,
    )

    with st.spinner("Генерирую письмо..."):
        try:
            result = ollama_generate(prompt)
        except Exception as e:
            st.error("Не удалось получить ответ от модели. Проверьте Ollama, модель и имя модели в app.py.")
            st.code(str(e))
            st.stop()

    st.subheader("Результат")
    st.markdown(result)

    st.subheader("Скопировать (Markdown)")
    st.code(result)
