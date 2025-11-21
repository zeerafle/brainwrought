from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def simple_llm_call(llm: ChatOpenAI, system_prompt: str, user_prompt: str) -> str:
    resp = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return resp.content if isinstance(resp.content, str) else str(resp.content)
