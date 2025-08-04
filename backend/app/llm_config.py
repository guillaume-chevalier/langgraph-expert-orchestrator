"""
LangChain LLM configuration for the LangGraph Expert Orchestrator.
Configure your model choice here.
"""

import os

from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI


def get_llm_model(model_name: str = None) -> BaseLanguageModel:
    """
    Get configured LLM model instance.

    Args:
        model_name: Override the default model name

    Returns:
        Configured LangChain LLM instance
    """
    default_model = os.getenv("OPENAI_MODEL", "gpt-4.1")
    model = model_name or default_model

    # Get configuration values from environment
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "32768"))

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


# Pre-configured models - lazy loaded to avoid import-time initialization
def get_models():
    """Get pre-configured models dictionary (lazy-loaded)."""
    return {
        "router": get_llm_model(),  # Use default
        "expert": get_llm_model(),  # Use default
        "summary": get_llm_model(),  # Use default
    }
