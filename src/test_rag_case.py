"""
test_rag_case.py - End-to-end clinical test case demonstrating the MediScan RAG pipeline.
"""

import sys
sys.path.insert(0, "src")

from VDB.pipeline import MediScanRetriever
from VDB.schema import RetrievalFilter

def run_clinical_rag_test():
    print("=" * 80)
    print("              MEDISCAN RAG - CLINICAL TEST CASE")
    print("=" * 80)

    # 1. Simulate Upstream CV Model & Patient Clinical Context
    patient_info = {
        "age": 64,
        "gender": "Male",
        "chief_complaint": "Acute worsening shortness of breath, fever (38.5 C), and productive cough for 4 days.",
        "upstream_cv_findings": (
            "Chest X-Ray (PA view): Focal consolidation and airspace opacity in the right lower lobe "
            "with visible air bronchograms. Moderate blunting of the right costophrenic sulcus consistent "
            "with right-sided pleural effusion. Cardiothoracic ratio is mildly increased."
        ),
        "suspected_conditions": ["Pneumonia", "Pleural_Effusion", "Cardiomegaly"]
    }

    print("\n--- [1] PATIENT & UPSTREAM CV MODEL FINDINGS ---")
    print(f"Patient: {patient_info['age']}yo {patient_info['gender']}")
    print(f"Chief Complaint: {patient_info['chief_complaint']}")
    print(f"CV Model Finding: {patient_info['upstream_cv_findings']}")
    print(f"Suspected Conditions: {', '.join(patient_info['suspected_conditions'])}")

    # 2. Initialize Retriever
    retriever = MediScanRetriever()

    # 3. Step A: SimilarCaseTool Bridge - Match against validated radiology reports
    print("\n" + "=" * 80)
    print("--- [2] SIMILAR CASE RETRIEVAL (SimilarCaseTool Bridge) ---")
    print("Searching OpenI Chest X-ray reports & PMC Case Studies for matching presentation...")
    print("=" * 80)
    case_query = "Right lower lobe consolidation air bronchograms and pleural effusion"
    case_results = retriever.search_cases(case_query, modality="CXR", k=3)

    for i, res in enumerate(case_results, 1):
        print(f"\n[Case Match {i}] ({res.retriever_type.upper()} | Score: {res.score:.4f})")
        print(f"  Source: {res.chunk.source_id} - {res.chunk.title}")
        print(f"  Chunk ID: {res.chunk.chunk_id}")
        print(f"  Content Snippet:\n  {res.chunk.content[:250]}...")

    # 4. Step B: ClinicalGuidelineTool Bridge - Fetch Management & Imaging Guidelines
    print("\n" + "=" * 80)
    print("--- [3] CLINICAL GUIDELINE RETRIEVAL (ClinicalGuidelineTool Bridge) ---")
    print("Fetching authoritative clinical guidelines for diagnosis and workup...")
    print("=" * 80)
    guideline_query = "Diagnostic workup for adult pneumonia and parapneumonic pleural effusion thoracentesis"
    guideline_results = retriever.search_guidelines(guideline_query, k=2)

    for i, res in enumerate(guideline_results, 1):
        print(f"\n[Guideline Match {i}] ({res.retriever_type.upper()} | Score: {res.score:.4f})")
        print(f"  Source: {res.chunk.source_id} - {res.chunk.title}")
        print(f"  Chunk ID: {res.chunk.chunk_id}")
        print(f"  Content Snippet:\n  {res.chunk.content[:280]}...")

    # 5. Step C: Patient Education & Discharge Planning
    print("\n" + "=" * 80)
    print("--- [4] PATIENT CARE & EDUCATION RETRIEVAL (PatientHistoryTool Bridge) ---")
    print("Fetching patient-friendly care instructions and warning signs...")
    print("=" * 80)
    patient_query = "Pneumonia warning signs when to seek immediate medical attention"
    patient_results = retriever.search_patient_education(patient_query, k=2)

    for i, res in enumerate(patient_results, 1):
        print(f"\n[Patient Care Match {i}] ({res.retriever_type.upper()} | Score: {res.score:.4f})")
        print(f"  Source: {res.chunk.source_id} - {res.chunk.title}")
        print(f"  Chunk ID: {res.chunk.chunk_id}")
        print(f"  Content Snippet:\n  {res.chunk.content[:250]}...")

    # 6. Step D: Grounded Evidence Block for Agent / LLM Synthesis
    print("\n" + "=" * 80)
    print("--- [5] COMPLETE GROUNDED EVIDENCE CONTEXT (Ready for LLM Prompt) ---")
    print("=" * 80)
    grounded_block = retriever.get_grounded_context(
        query="What are the essential diagnostic findings, imaging confirmation, and management steps for pneumonia with pleural effusion?",
        k=3
    )
    print(grounded_block)

    print("\n" + "=" * 80)
    print("  CLINICAL TEST CASE COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_clinical_rag_test()
