from langchain_openai import ChatOpenAI  # or your provider of choice


def get_llm(model_name: str = "gpt-5-mini"):
    # Extend later with caching, tracing, etc.
    return ChatOpenAI(model=model_name, temperature=0.4)
