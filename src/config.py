import os
from typing import Literal

from langchain_core.language_models import BaseChatModel

ProviderType = Literal["openai", "gemini", "vertex"]

USE_MOCK_PRODUCTION = os.getenv("USE_MOCK_PRODUCTION", "false").lower() == "true"


def get_llm(
    provider: ProviderType = "openai",
    model_name: str | None = None,
    temperature: float = 0.4,
    **kwargs,
) -> BaseChatModel:
    """
    Get an LLM instance based on provider.

    Args:
        provider: The LLM provider to use ("openai", "gemini", "vertex")
        model_name: Model name. If None, uses provider default.
        temperature: Temperature for generation (0.0-1.0)
        **kwargs: Additional provider-specific arguments

    Environment variables required:
        - OpenAI: OPENAI_API_KEY
        - Gemini: GOOGLE_API_KEY
        - Vertex: GOOGLE_CLOUD_PROJECT (and GCP authentication)
    """

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model_name = model_name or "gpt-5-mini"
        return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = model_name or "gemini-2.0-flash-exp"

        # Ensure API key is set
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError(
                "GOOGLE_API_KEY environment variable must be set for Gemini.\n"
                "Get your API key at: https://aistudio.google.com/apikey"
            )

        return ChatGoogleGenerativeAI(
            model=model_name, temperature=temperature, **kwargs
        )

    elif provider == "vertex":
        from langchain_google_vertexai import ChatVertexAI

        model_name = model_name or "gemini-2.0-flash-001"

        # Ensure project is set
        project = kwargs.pop("project", os.getenv("GOOGLE_CLOUD_PROJECT"))
        location = kwargs.pop("location", "us-central1")

        if not project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable or 'project' argument must be set for Vertex AI"
            )

        return ChatVertexAI(
            model_name=model_name,
            project=project,
            location=location,
            temperature=temperature,
            **kwargs,
        )

    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Choose from: openai, gemini, vertex"
        )


# Convenience functions for specific providers
def get_openai_llm(model: str = "gpt-5-mini", **kwargs) -> BaseChatModel:
    """Get OpenAI LLM instance."""
    return get_llm(provider="openai", model_name=model, **kwargs)


def get_gemini_llm(model: str = "gemini-2.0-flash", **kwargs) -> BaseChatModel:
    """Get Google Gemini LLM instance (via direct API)."""
    return get_llm(provider="gemini", model_name=model, **kwargs)


def get_vertex_llm(model: str = "gemini-2.0-flash-001", **kwargs) -> BaseChatModel:
    """Get Google Vertex AI LLM instance (via GCP)."""
    return get_llm(provider="vertex", model_name=model, **kwargs)
