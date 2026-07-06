import os

import groq
from langchain_groq import ChatGroq

llama3_70b_8192 = "llama3-70b-8192"
llama3_8b_8192 = "llama3-8b-8192"
llama31_70b = "llama-3.1-70b-versatile"
gemma_7b_it = "gemma-7b-it"
gemma2_9b_it = "gemma2-9b-it"


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", None)

groq_client = groq.Groq()

groq_chat = ChatGroq(
    model=llama31_70b,
    max_retries=8000,
    temperature=0,
    stop_sequences="###",
    verbose=True,
)
