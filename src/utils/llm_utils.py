from typing import Type, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel


def simple_llm_call(llm: BaseChatModel, system_prompt: str, user_prompt: str) -> str:
    resp = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return resp.content if isinstance(resp.content, str) else str(resp.content)


T = TypeVar("T", bound=BaseModel)


def structured_llm_call(
    llm: BaseChatModel, system_prompt: str, user_prompt: str, response_model: Type[T]
) -> T:
    """
    Call LLM with structured output using a Pydantic model.
    Works with any LangChain-compatible chat model that supports structured output.
    """
    structured_llm = llm.with_structured_output(response_model, method="json_schema")
    resp = structured_llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    # Type assertion since we're explicitly using json_schema method with a Pydantic model
    return resp  # type: ignore[return-value]
