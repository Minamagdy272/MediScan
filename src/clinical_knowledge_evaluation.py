"""
clinical_knowledge_evaluation.py - In-depth clinical observation and validation of MediScan RAG.
"""

import sys
sys.path.insert(0, "src")

from VDB.pipeline import MediScanRetriever
from VDB.schema import RetrievalFilter

def evaluate_and_observe():
    retriever = MediScanRetriever()

    test_cases = [
        {
            "id": "CASE_1_PNEUMOTHORAX",
            "scenario": "Pneumothorax Detection on Supine/ICU CXR",
            "query": "Deep sulcus sign and radiological findings of tension pneumothorax on supine chest film",
            "filter": RetrievalFilter(condition="Pneumothorax"),
            "clinical_criteria": ["deep sulcus", "visceral pleura", "supine", "tension", "decompression"]
        },
        {
            "id": "CASE_2_PNEUMONIA_PLEURAL_EFFUSION",
            "scenario": "Parapneumonic Effusion & Thoracentesis Criteria",
            "query": "When is thoracentesis indicated in suspected parapneumonic pleural effusion and pneumonia?",
            "filter": RetrievalFilter(knowledge_domain="clinical_references"),
            "clinical_criteria": ["thoracentesis", "parapneumonic", "drainage", "effusion", "infection"]
        },
        {
            "id": "CASE_3_HEART_FAILURE_DIURETICS",
            "scenario": "Acute Heart Failure Management & Congestion",
            "query": "Diuretic therapy, fluid restriction, and radiological signs of pulmonary venous congestion in heart failure",
            "filter": RetrievalFilter(condition="Heart_Failure"),
            "clinical_criteria": ["diuretics", "congestion", "fluid restriction", "pulmonary edema"]
        },
        {
            "id": "CASE_4_STROKE_GUIDELINES",
            "scenario": "Ischemic Stroke vs Hemorrhage Guidelines",
            "query": "Non-contrast CT imaging protocol and intravenous thrombolysis criteria in acute ischemic stroke",
            "filter": RetrievalFilter(knowledge_domain="guidelines"),
            "clinical_criteria": ["computed tomography", "thrombolysis", "ischemic", "stroke", "guideline"]
        },
        {
            "id": "CASE_5_COPD_PATIENT_CARE",
            "scenario": "COPD Exacerbation & Patient Self-Management",
            "query": "COPD warning signs, breathlessness triggers, and when to call emergency services",
            "filter": RetrievalFilter(knowledge_domain="patient_education", condition="COPD"),
            "clinical_criteria": ["shortness of breath", "cough", "emergency", "symptoms"]
        }
    ]

    print("=" * 90)
    print("        MEDISCAN RAG - CLINICAL KNOWLEDGE OBSERVATION & VALIDATION")
    print("=" * 90)

    for case in test_cases:
        print(f"\n==========================================================================================")
        print(f"TEST: [{case['id']}] - {case['scenario']}")
        print(f"Query: \"{case['query']}\"")
        print(f"Metadata Filter: {case['filter'].__dict__}")
        print(f"Clinical Success Criteria Keywords: {case['clinical_criteria']}")
        print(f"------------------------------------------------------------------------------------------")

        results = retriever.retrieve(case["query"], k=2, filter_obj=case["filter"])

        for idx, res in enumerate(results, 1):
            chunk = res.chunk
            content = chunk.content.lower()
            matched_keywords = [kw for kw in case["clinical_criteria"] if kw.lower() in content]
            
            print(f"\n[Result #{idx}] Source: {chunk.source_id} | Title: {chunk.title}")
            print(f"  Chunk ID: {chunk.chunk_id}")
            print(f"  Domain: {chunk.knowledge_domain} | Audience: {chunk.audience} | Score: {res.score:.4f}")
            print(f"  Matched Clinical Criteria: {matched_keywords} ({len(matched_keywords)}/{len(case['clinical_criteria'])})")
            print(f"  Snippet:")
            print(f"  \"\"\"\n  {chunk.content[:350]}...\n  \"\"\"")

    print("\n==========================================================================================")
    print("                             OBSERVATION COMPLETED")
    print("==========================================================================================")

if __name__ == "__main__":
    evaluate_and_observe()
