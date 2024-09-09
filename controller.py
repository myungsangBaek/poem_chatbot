import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain import hub
from langchain_pinecone import PineconeVectorStore


def get_retriever():

    embedding = OpenAIEmbeddings(model='text-embedding-3-large')
    index_name = 'poem-index'

    database = PineconeVectorStore.from_existing_index(
        index_name=index_name, embedding=embedding)
    retriever = database.as_retriever(search_kwargs={'k': 4})
    return retriever


def get_llm(model='gpt-4o'):
    llm = ChatOpenAI(model=model)
    return llm


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


def get_qa_chain():
    llm = get_llm()
    retriever = get_retriever()
    prompt = hub.pull('rlm/rag-prompt')

    qa_chain = RetrievalQA.from_chain_type(
        llm, retriever=retriever, chain_type_kwargs={'prompt': prompt})
    return qa_chain


def get_ai_message(user_message):
    dictionary_chain = get_dictionary_chain()
    qa_chain = get_qa_chain()

    poem_chain = {"query": dictionary_chain} | qa_chain
    ai_message = poem_chain.invoke({"user_message": user_message})

    content = ai_message["query"]
    result = ai_message["result"]

    return f"{content}\n\n 설명 : {result}"
