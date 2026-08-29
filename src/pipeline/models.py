"""
LLM and Provider Initialization for MediScan Pipeline.
"""

import re
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage

from .config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    ROUTER_MODEL,
    AGENT_MODEL,
    EVALUATOR_MODEL
)

# 1. Router Model (NVIDIA NIM)
router_llm = ChatNVIDIA(
    model=ROUTER_MODEL,
    api_key=NVIDIA_API_KEY,
    base_url=NVIDIA_BASE_URL,
    temperature=0.0,
    max_tokens=512,
    timeout=15,
)

# 2. Agent Planner & Generator Models (GLM-5.3-Flash via OpenRouter)
planner_llm = ChatOpenAI(
    model=AGENT_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    temperature=0.0,
    max_tokens=8192,
    timeout=60,
)

generator_llm = ChatOpenAI(
    model=AGENT_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    temperature=0.1,
    max_tokens=8192,
    timeout=90,
)

# 3. Evaluator Model (DeepSeek-V4-Flash via NVIDIA NIM)
evaluator_llm = ChatNVIDIA(
    model=EVALUATOR_MODEL,
    api_key=NVIDIA_API_KEY,
    base_url=NVIDIA_BASE_URL,
    temperature=0.0,
    max_tokens=2048,
    timeout=15,
)

T = TypeVar("T", bound=BaseModel)


def invoke_json_model(
    llm,
    prompt,
    schema: Type[T],
    *,
    temperature: float = 0.0
) -> T:
    """Helper to enforce pure JSON structured outputs from NVIDIA NIM / OpenRouter LLMs."""
    schema_json = json.dumps(schema.model_json_schema(), indent=2)

    instructions = f"""
You must return ONLY a valid JSON object.

Do not return Markdown.
Do not use code fences.
Do not include explanations before or after the JSON.

Your JSON must follow this schema:

{schema_json}
"""

    if isinstance(prompt, list):
        messages = list(prompt)
        messages.append(HumanMessage(content=instructions))
        response = llm.bind(temperature=temperature).invoke(messages)
    else:
        full_prompt = f"""{instructions}

Task:

{prompt}
"""
        response = llm.bind(temperature=temperature).invoke(full_prompt)

    content = response.content if hasattr(response, "content") else str(response)
    content = content.strip()

    # Remove Markdown code fences
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # Extract JSON object
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found.\nRaw output:\n{content}")

    json_text = content[start:end + 1]

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned: {e}\nRaw output:\n{content}")

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"JSON failed Pydantic validation:\n{e}\nData: {data}")
