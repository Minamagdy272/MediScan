"""
test_queries.py - Fixed 22-Case Clinical Retrieval Benchmark Dataset.

Covers 12 medical conditions across radiology (CXR, CT), clinical guidelines,
differential diagnoses, patient education, and clinical case reports.
"""

from typing import List, Dict, Any

BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "TC01_PNEUMONIA_CXR",
        "query": "What chest X-ray findings indicate bacterial pneumonia and focal consolidation with air bronchograms?",
        "expected_conditions": ["Pneumonia"],
        "expected_source_types": ["reference", "guideline", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Pneumonia", "SRC_LOCAL_NICE_Pneumonia_Guideline", "SRC_LOCAL_Consolidation"],
        "acceptable_knowledge_domains": ["clinical_references", "guidelines", "cases"],
        "modality": "CXR",
        "difficulty": "medium",
        "keywords": ["consolidation", "infiltrate", "air bronchogram", "opacity", "pneumonia"],
        "notes": "Classic radiological presentation of lobar pneumonia."
    },
    {
        "case_id": "TC02_PLEURAL_EFFUSION_SIGNS",
        "query": "Radiological meniscus sign and blunting of the costophrenic angle on chest radiograph",
        "expected_conditions": ["Pleural_Effusion"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Pleural_Effusion", "SRC_LOCAL_basic_interpretation"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "easy",
        "keywords": ["meniscus", "costophrenic", "blunting", "effusion", "fluid"],
        "notes": "Pathognomonic signs of pleural effusion."
    },
    {
        "case_id": "TC03_PNEUMOTHORAX_DEEP_SULCUS",
        "query": "Deep sulcus sign and visceral pleural line on supine ICU chest film",
        "expected_conditions": ["Pneumothorax"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Pneumothorax", "SRC_LOCAL_basic_interpretation"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "hard",
        "keywords": ["deep sulcus", "visceral pleura", "pneumothorax", "supine", "collapse"],
        "notes": "Critical supine ICU pneumothorax diagnostic finding."
    },
    {
        "case_id": "TC04_PULMONARY_EDEMA_KERLEY",
        "query": "Kerley B lines, bat wing alveolar edema, and cardiomegaly on chest X-ray",
        "expected_conditions": ["Pulmonary_Edema", "Heart_Failure"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Pulmonary_Edema", "SRC_LOCAL_Heart_Failure"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "medium",
        "keywords": ["kerley", "bat wing", "edema", "cardiomegaly", "congestion"],
        "notes": "Classic congestive heart failure radiological signs."
    },
    {
        "case_id": "TC05_HF_GUIDELINE_CONGESTION",
        "query": "Clinical guideline recommendations for acute decompensated heart failure diuretic therapy",
        "expected_conditions": ["Heart_Failure"],
        "expected_source_types": ["guideline", "reference"],
        "acceptable_source_ids": ["SRC_LOCAL_Heart_Failure", "SRC_LOCAL_AHA_HF_Guideline"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references"],
        "modality": None,
        "difficulty": "medium",
        "keywords": ["diuretic", "heart failure", "furosemide", "congestion", "guideline"],
        "notes": "Inpatient guideline recommendations for volume overload."
    },
    {
        "case_id": "TC06_STROKE_CT_PROTOCOL",
        "query": "Emergency non-contrast CT protocol and time window for acute ischemic stroke thrombolysis",
        "expected_conditions": ["Ischemic_Stroke"],
        "expected_source_types": ["guideline", "reference"],
        "acceptable_source_ids": ["SRC_LOCAL_AHA_Ischemic_Stroke_Guideline", "SRC_LOCAL_Stroke"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references"],
        "modality": "CT",
        "difficulty": "medium",
        "keywords": ["stroke", "computed tomography", "thrombolysis", "time window", "alteplase"],
        "notes": "Emergency imaging to rule out intracranial hemorrhage."
    },
    {
        "case_id": "TC07_APPENDICITIS_US_CT",
        "query": "Ultrasound and CT diagnostic criteria for acute appendicitis including outer wall diameter",
        "expected_conditions": ["Appendicitis"],
        "expected_source_types": ["guideline", "reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Appendicitis", "SRC068"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references", "cases"],
        "modality": "US",
        "difficulty": "medium",
        "keywords": ["appendicitis", "diameter", "ultrasound", "target sign", "appendix"],
        "notes": "Criteria for appendiceal inflammation."
    },
    {
        "case_id": "TC08_COPD_EXACERBATION_SIGNS",
        "query": "Acute COPD exacerbation symptoms, purulent sputum, and noninvasive ventilation criteria",
        "expected_conditions": ["COPD"],
        "expected_source_types": ["guideline", "reference"],
        "acceptable_source_ids": ["SRC_LOCAL_COPD", "SRC_LOCAL_GOLD_COPD_Guideline"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references"],
        "modality": None,
        "difficulty": "medium",
        "keywords": ["copd", "exacerbation", "sputum", "dyspnea", "ventilation"],
        "notes": "GOLD guideline exacerbation triage."
    },
    {
        "case_id": "TC09_PULMONARY_NODULE_FLEISCHNER",
        "query": "Fleischner Society guidelines for management of solid indeterminate pulmonary nodules on CT",
        "expected_conditions": ["Pulmonary_Nodules"],
        "expected_source_types": ["guideline", "reference"],
        "acceptable_source_ids": ["SRC_LOCAL_Pulmonary_Nodules", "SRC_LOCAL_NCCN_NSCLC_Guideline"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references"],
        "modality": "CT",
        "difficulty": "hard",
        "keywords": ["fleischner", "nodule", "surveillance", "solid", "computed tomography"],
        "notes": "Nodule surveillance thresholds by size and risk."
    },
    {
        "case_id": "TC10_THORACENTESIS_INDICATIONS",
        "query": "Indications for diagnostic thoracentesis and Light's criteria for pleural fluid analysis",
        "expected_conditions": ["Pleural_Effusion"],
        "expected_source_types": ["reference", "guideline"],
        "acceptable_source_ids": ["SRC_LOCAL_Pleural_Effusion"],
        "acceptable_knowledge_domains": ["clinical_references", "guidelines"],
        "modality": None,
        "difficulty": "medium",
        "keywords": ["thoracentesis", "light", "exudate", "transudate", "ldh", "protein"],
        "notes": "Biochemical classification of pleural fluid."
    },
    {
        "case_id": "TC11_HF_PATIENT_EDUCATION",
        "query": "Low sodium dietary restrictions and daily morning weight monitoring for heart failure patients",
        "expected_conditions": ["Heart_Failure"],
        "expected_source_types": ["patient_education"],
        "acceptable_source_ids": ["SRC_LOCAL_living_with_heart_failure", "SRC_LOCAL_heart_failure_diet"],
        "acceptable_knowledge_domains": ["patient_education"],
        "modality": None,
        "difficulty": "easy",
        "keywords": ["sodium", "diet", "weight", "fluid", "heart failure"],
        "notes": "Patient-facing self-management."
    },
    {
        "case_id": "TC12_PNEUMONIA_PATIENT_WARNINGS",
        "query": "When to seek urgent emergency care for worsening pneumonia and chest pain",
        "expected_conditions": ["Pneumonia"],
        "expected_source_types": ["patient_education"],
        "acceptable_source_ids": ["SRC_LOCAL_MedlinePlus_Pneumonia", "SRC_LOCAL_pneuomonia"],
        "acceptable_knowledge_domains": ["patient_education"],
        "modality": None,
        "difficulty": "easy",
        "keywords": ["emergency", "chest pain", "shortness of breath", "fever", "cough"],
        "notes": "Patient red flags."
    },
    {
        "case_id": "TC13_HYDROPNEUMOTHORAX_CXR",
        "query": "Air fluid level in pleural space on upright chest X-ray indicating hydropneumothorax",
        "expected_conditions": ["Pneumothorax", "Pleural_Effusion"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Pneumothorax", "SRC_LOCAL_Pleural_Effusion"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "medium",
        "keywords": ["air fluid level", "hydropneumothorax", "pleural", "hemopneumothorax"],
        "notes": "Combined pleural pathology."
    },
    {
        "case_id": "TC14_ATELECTASIS_VS_PNEUMONIA",
        "query": "Radiological differentiation between pulmonary atelectasis volume loss and airspace pneumonia consolidation",
        "expected_conditions": ["Pneumonia", "Atelectasis"],
        "expected_source_types": ["reference"],
        "acceptable_source_ids": ["SRC_LOCAL_Consolidation", "SRC_LOCAL_basic_interpretation"],
        "acceptable_knowledge_domains": ["clinical_references"],
        "modality": "CXR",
        "difficulty": "hard",
        "keywords": ["volume loss", "mediastinal shift", "atelectasis", "consolidation", "air bronchogram"],
        "notes": "Key chest X-ray differential."
    },
    {
        "case_id": "TC15_KIDNEY_STONE_CT",
        "query": "Non-contrast CT abdomen and pelvis sensitivity for acute ureteral calculus and hydronephrosis",
        "expected_conditions": ["Kidney_Stones"],
        "expected_source_types": ["reference", "guideline", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_Kidney_Stones", "SRC_LOCAL_AUA_Kidney_Stones_Guideline"],
        "acceptable_knowledge_domains": ["clinical_references", "guidelines", "cases"],
        "modality": "CT",
        "difficulty": "medium",
        "keywords": ["calculus", "hydronephrosis", "computed tomography", "ureteral", "stone"],
        "notes": "Urolithiasis gold standard imaging."
    },
    {
        "case_id": "TC16_TENSION_PNEUMO_DECOMPRESSION",
        "query": "Immediate needle decompression landmarks for clinical tension pneumothorax prior to chest tube",
        "expected_conditions": ["Pneumothorax"],
        "expected_source_types": ["reference", "guideline"],
        "acceptable_source_ids": ["SRC_LOCAL_Pneumothorax"],
        "acceptable_knowledge_domains": ["clinical_references", "guidelines"],
        "modality": None,
        "difficulty": "medium",
        "keywords": ["decompression", "intercostal", "tension", "needle", "thoracostomy"],
        "notes": "Emergency life-saving procedure."
    },
    {
        "case_id": "TC17_CARDIOMEGALY_CTR",
        "query": "Cardiothoracic ratio greater than 0.5 on PA chest radiograph indicating cardiomegaly",
        "expected_conditions": ["Cardiomegaly", "Heart_Failure"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_basic_interpretation", "SRC_LOCAL_Heart_Failure"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "easy",
        "keywords": ["cardiothoracic ratio", "cardiomegaly", "heart", "enlargement", "silhouette"],
        "notes": "Cardiac enlargement measurement."
    },
    {
        "case_id": "TC18_EMPHYSEMA_HYPERINFLATION",
        "query": "Flattened diaphragms, increased retrosternal clear space, and hyperlucency on CXR in emphysema",
        "expected_conditions": ["COPD"],
        "expected_source_types": ["reference", "cases"],
        "acceptable_source_ids": ["SRC_LOCAL_COPD", "SRC_LOCAL_basic_interpretation"],
        "acceptable_knowledge_domains": ["clinical_references", "cases"],
        "modality": "CXR",
        "difficulty": "medium",
        "keywords": ["hyperinflation", "flattened", "diaphragm", "retrosternal", "emphysema"],
        "notes": "Obstructive hyperinflation signs."
    },
    {
        "case_id": "TC19_PARAPNEUMONIC_DRAINAGE_PH",
        "query": "Pleural fluid pH below 7.2 and glucose level indicating complicated parapneumonic effusion",
        "expected_conditions": ["Pleural_Effusion", "Pneumonia"],
        "expected_source_types": ["reference", "guideline"],
        "acceptable_source_ids": ["SRC_LOCAL_Pleural_Effusion"],
        "acceptable_knowledge_domains": ["clinical_references", "guidelines"],
        "modality": None,
        "difficulty": "hard",
        "keywords": ["ph", "glucose", "complicated", "drainage", "empyema", "parapneumonic"],
        "notes": "Laboratory criteria for chest tube placement."
    },
    {
        "case_id": "TC20_COPD_OXYGEN_THERAPY",
        "query": "Long-term home oxygen therapy indications in chronic COPD and target SpO2 levels",
        "expected_conditions": ["COPD"],
        "expected_source_types": ["guideline", "patient_education"],
        "acceptable_source_ids": ["SRC_LOCAL_MedlinePlus_COPD", "SRC_LOCAL_GOLD_COPD_Guideline"],
        "acceptable_knowledge_domains": ["guidelines", "patient_education"],
        "modality": None,
        "difficulty": "medium",
        "keywords": ["oxygen", "saturation", "hypoxemia", "copd", "therapy"],
        "notes": "Hypoxemia management in chronic lung disease."
    },
    {
        "case_id": "TC21_LUNG_CANCER_STAGING_CT",
        "query": "Chest and upper abdominal CT staging criteria for non-small cell lung cancer mediastinal lymphadenopathy",
        "expected_conditions": ["Lung_Cancer"],
        "expected_source_types": ["guideline", "reference"],
        "acceptable_source_ids": ["SRC_LOCAL_NCCN_NSCLC_Guideline"],
        "acceptable_knowledge_domains": ["guidelines", "clinical_references"],
        "modality": "CT",
        "difficulty": "hard",
        "keywords": ["mediastinal", "lymph node", "staging", "computed tomography", "cancer"],
        "notes": "NCCN staging protocols."
    },
    {
        "case_id": "TC22_HEART_FAILURE_WARNINGS",
        "query": "Heart failure decompensation red flags sudden weight gain and worsening orthopnea",
        "expected_conditions": ["Heart_Failure"],
        "expected_source_types": ["patient_education"],
        "acceptable_source_ids": ["SRC_LOCAL_living_with_heart_failure", "SRC_LOCAL_heart_failure_discharge"],
        "acceptable_knowledge_domains": ["patient_education"],
        "modality": None,
        "difficulty": "easy",
        "keywords": ["weight gain", "orthopnea", "swelling", "shortness of breath", "warning signs"],
        "notes": "Patient early intervention signals."
    }
]
