import streamlit as st
from controller import get_ai_message

from dotenv import load_dotenv


load_dotenv()

st.set_page_config(page_title="음유시봇", page_icon="📖")

st.title("🤖 음유시봇")
st.caption("음유시봇은 주제를 입력하면 당신만을 위한 시를 쓰는 챗봇입니다.")

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])


if user_question := st.chat_input(placeholder="'OO을 주제로 시를 창작해줘!' 라고 입력해주세요."):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append(
        {"role": "user", "content": user_question})

    with st.spinner("음유시봇이 당신만을 위한 시를 쓰는 중입니다..."):

        # AI 메세지 생성
        with st.chat_message("ai"):
            st.write(get_ai_message(user_question))
        st.session_state.message_list.append(
            {"role": "ai", "content": get_ai_message(user_question)})
