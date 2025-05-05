import streamlit as st
from openai import OpenAI
from parse_hh import get_html, extract_vacancy_data, extract_resume_data
import re


if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ Ключ OPENAI_API_KEY не найден в .streamlit/secrets.toml")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?) — эта оценка должна учитываться при выставлении финальной оценки.

‼️ В конце обязательно напиши строку строго в формате: Оценка: X/10, где X — целое число от 1 до 10 (без дополнительных комментариев).
""".strip()




def request_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content

# UI
st.title('CV Scoring App')

job_description = st.text_area('Введите ссылку на вакансию')
cv = st.text_area('Введите ссылку на резюме')

# 👇 Основная логика запуска анализа, реагируем на кнопку
if st.button("Проанализировать соответствие"):

     with st.spinner("Парсим данные и отправляем в GPT..."):
        try:
            job_html = get_html(job_description).text
            resume_html = get_html(cv).text

            job_text = extract_vacancy_data(job_html)
            resume_text = extract_resume_data(resume_html)

            # 👇 Предпросмотр вакансии
            with st.expander("📄 Посмотреть текст вакансии"):
                st.markdown(job_text)

            # 👇 Предпросмотр резюме
            with st.expander("👤 Посмотреть текст резюме"):
                st.markdown(resume_text)

            prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
            response = request_gpt(SYSTEM_PROMPT, prompt)

            score_match = re.search(r'(\d{1,2})\s*/\s*10', response)
            if score_match:
                score = int(score_match.group(1))
                st.subheader("🔢 Оценка соответствия:")
                st.progress(min(score, 10) / 10)
                st.markdown(f"**{score}/10** — чем выше, тем лучше соответствие.")
            else:
                st.info("⚠️ GPT не выдал числовую оценку — проверь формат промпта.")

            st.subheader("📊 Результат анализа:")
            st.markdown(response)

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")

