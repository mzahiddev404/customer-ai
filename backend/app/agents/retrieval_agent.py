import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")

def get_retriever(k=4):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = Chroma(persist_directory=CHROMA_PATH, collection_name="pdf_docs", embedding_function=embeddings)
    return vectordb.as_retriever(search_kwargs={"k": k})

def make_conversational_agent():
    chat = ChatOpenAI(temperature=0.0, openai_api_key=OPENAI_API_KEY)
    retriever = get_retriever()
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    qa = ConversationalRetrievalChain.from_llm(chat, retriever, memory=memory)
    return qa

