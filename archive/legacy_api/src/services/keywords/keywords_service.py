from typing import List

from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel

from src.services.file_service import get_file_contents
from src.services.keywords.examples import examples
from src.services.openai_service import openai_chat


class KeywordGeneratorParser(BaseModel):
    keywords: List[str]


chunk_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{query}"),
        ("assistant", "{keywords}"),
    ]
)

keywords_prompt = get_file_contents("src/services/keywords/keywords_prompt.md")

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=chunk_prompt,
    examples=examples,
)


def get_query_keywords(task_description: str) -> List[str]:
    parser = JsonOutputParser(pydantic_object=KeywordGeneratorParser)
    system_prompt = SystemMessagePromptTemplate.from_template(
        template=keywords_prompt,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    prompt_template = ChatPromptTemplate(
        [
            system_prompt,
            # few_shot_prompt,
            ("human", "{task_description}"),
        ]
    )

    chain = {"task_description": RunnablePassthrough()} | prompt_template | openai_chat | parser

    llm_response = chain.invoke({"task_description": task_description})

    return llm_response["keywords"]
    # if isinstance(llm_response.content, str):
    #     try:
    #         parsed = parser.parse(llm_response.content)
    #         return parsed["keywords"]
    #     except Exception:
    #         return []

    # return []
