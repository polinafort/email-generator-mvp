import streamlit as st
import requests
from prompt import build_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma2:2b"  

def ollama_generate(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "num_predict": 700
        }
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()

st.set_page_config(page_title="Email Generator MVP", layout="centered")
st.title("Генератор email-рассылки (MVP)")

with st.form("email_form"):
    audience = st.text_input("ЦА (кто читает)", placeholder="Напр.: владельцы малого бизнеса, пользователи SaaS, менеджеры по продажам")
    goal = st.text_input("Цель рассылки", placeholder="Напр.: рассказать о новой фиче и довести до использования")
    must_include = st.text_area(
        "Обязательные пункты (что точно должно быть в письме)",
        placeholder="- Как включить фичу\n- Ограничения\n- Где найти кнопку\n- Контакты поддержки"
    )
    culture = st.text_area(
        "Культура/тон компании",
        placeholder="Напр.: дружелюбно, на 'вы', без сленга, короткие предложения, без эмодзи, уверенно, но не агрессивно"
    )
    context = st.text_area(
        "Контекст/продукт (опционально)",
        placeholder="Напр.: Мы — сервис онлайн-аналитики. Фича: экспорт в CSV. Аудитория в РФ."
    )
    submitted = st.form_submit_button("Сгенерировать письмо")

if submitted:
    if not audience or not goal or not must_include:
        st.error("Заполните минимум: ЦА, цель, обязательные пункты.")
        st.stop()

    prompt = build_prompt(audience, goal, must_include, culture, context)

    with st.spinner("Генерирую..."):
        try:
            result = ollama_generate(prompt)
        except Exception as e:
            st.error("Не удалось получить ответ от модели. Проверьте, что Ollama запущена и модель скачана.")
            st.code(str(e))
            st.stop()

    st.subheader("Результат")
    st.markdown(result)

    st.subheader("Скопировать как текст")
    st.code(result)
