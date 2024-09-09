import streamlit as st

st.set_page_config(page_title="음유시인 챗봇", page_icon="📖")

st.title("🤖 음유시인 챗봇")
st.caption("음유시인 챗봇은 음유시인의 시를 창작하는 챗봇입니다.")

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_question := st.chat_input(placeholder="시를 창작해보세요."):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append(
        {"role": "user", "content": user_question})

    # st.chat_message("assistant").markdown("시를 창작하는 중입니다...")
