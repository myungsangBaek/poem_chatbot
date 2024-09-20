import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains.combine_documents import create_stuff_documents_chain
from config import examples


from langchain_core.runnables.history import RunnableWithMessageHistory

store = {}


# 세센별 채팅 기록 관리
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# 벡터 검색기 설정 - 벡터 DB에서 유사한 데이터 검색
def get_retriever():

    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    index_name = 'poem-index'

    database = PineconeVectorStore.from_existing_index(
        index_name=index_name, embedding=embedding)
    retriever = database.as_retriever(search_kwargs={'k': 4})
    return retriever


def get_history_retriever():
    llm = get_llm()
    retriever = get_retriever()

    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

# 대화기록을 기반으로 새로운 질문을 독립적으로 재구성
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt)

    return history_aware_retriever
# LLM 객체 생성


def get_llm(model='gpt-4o'):
    llm = ChatOpenAI(model=model)
    return llm


# 키워드 추출 및 주제 설정 - 사용자 질문에서 불필요한 문장 제거 및 의미 있는 키워드 추출
def get_dictionary_chain():
    dictionary = ["키워드를 읽고 해당 관련된 주제로 변환"]
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(f"""
                                            사용자의 질문을 보고, 쓸데 없는 문장들은 제거하고 키워드를 찾아서 주제로 정할 수 없다고 판단되면, 다시 입력해달라고하고 
                                            주제를 정하면 해당 주제에 맞는 시를 창작해주세요.
                                            
                                            사용자의 질문: {{user_message}}
                                            주제: {dictionary}
                                              """)

    dictionary_chain = prompt | llm | StrOutputParser()
    return dictionary_chain


# 질문 재구성 및 검색 기반 답변 제공
def get_rag_chain():
    llm = get_llm()
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{answer}")
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples
    )

    system_prompt = ("You are a poet. Create a poem based on the user’s keyword."
                     "Look at the user’s keyword and create a poem."
                     "When creating the poem, start with: ‘XX(keyword)의 주제로 창작한 시 입니다.’ in your response."
                     "I would like a short response, about 6-7 sentences."
                     "\n\n"
                     "{context}"
                     )

# 검색된 정보를 GPT 모델이 처리하여 최종 답변 생성
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            few_shot_prompt,
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )
    history_aware_retriever = get_history_retriever()

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key='input',
        history_messages_key='chat_history',
        output_messages_key='answer',
    )

    return conversational_rag_chain


# 문맥과 생성 결합
def get_ai_message(user_message):
    dictionary_chain = get_dictionary_chain()
    rag_chain = get_rag_chain()

    poem_chain = {"input": dictionary_chain} | rag_chain
    ai_message = poem_chain.invoke({"user_message": user_message},   config={
                                   "configurable": {"session_id": "abc123"}},)
    content = ai_message["input"]
    answer = ai_message["answer"]

    # 동일한 입력에 대해 동일한 답변을 제공하기 위해 캐시 사용
    if user_message in store:
        return store[user_message]
    else:
        store[user_message] = f"설명 : {answer}"
        return store[user_message]
