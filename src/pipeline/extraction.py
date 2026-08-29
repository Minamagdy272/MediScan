"""
Clinical Entity Extraction Component.
"""

from langchain_core.prompts import ChatPromptTemplate
from .schemas import ExtractedMedicalInfo
from .models import planner_llm

extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an extraction component for a clinical medical AI system.
Extract ONLY facts explicitly stated in the input text.
Rules:
- Do NOT make a diagnosis.
- Do NOT infer patient history not present.
- Separate positive and negative findings.
- List missing clinical information under missing_information.
"""),
    ("human", "Extract structured information from this text:\n\n{input_text}")
])

structured_extractor = planner_llm.with_structured_output(ExtractedMedicalInfo)
extraction_chain = extraction_prompt | structured_extractor


def extract_clinical_info(text: str) -> ExtractedMedicalInfo:
    """Extract structured clinical information from raw text or clinical notes."""
    try:
        return extraction_chain.invoke({"input_text": text})
    except Exception:
        return ExtractedMedicalInfo(
            imaging_findings=[text[:200]],
            missing_information=["Structured extraction fallback due to parsing."]
        )
