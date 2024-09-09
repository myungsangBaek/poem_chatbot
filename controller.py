from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def get_ai_message(user_message):
    load_dotenv()
    llm = ChatOpenAI(model='gpt-4o')

    response = llm.invoke(user_message)

    return response.content
