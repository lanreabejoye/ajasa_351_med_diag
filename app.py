import streamlit as st
import pandas as pd
import time
import random
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="MedAI Diagnostic System", page_icon="⚕️", layout="wide")

# --- State Management for Past Patients (The Memory Engine) ---
if "patient_history" not in st.session_state:
    st.session_state.patient_history = []

# --- Constants & Clinical Data ---
SYMPTOM_CATEGORIES = {
    "Cardiovascular": ["chest pain", "palpitations", "shortness of breath", "leg swelling", "dizziness", "syncope", "hypertension"],
    "Respiratory": ["cough", "wheezing", "hemoptysis", "pleuritic pain", "dyspnea", "stridor", "sputum production"],
    "Neurological": ["headache", "seizures", "memory loss", "tremor", "weakness", "numbness", "vision changes"],
    "Gastrointestinal": ["nausea", "vomiting", "diarrhea", "abdominal pain", "bloating", "blood in stool", "jaundice"],
    "Musculoskeletal": ["joint pain", "muscle weakness", "back pain", "stiffness", "swelling", "limited range of motion"],
    "Dermatological": ["rash", "itching", "skin lesions", "hair loss", "nail changes", "skin discoloration"],
    "Endocrine": ["fatigue", "weight changes", "excessive thirst", "frequent urination", "heat intolerance", "cold intolerance"],
    "General": ["fever", "chills", "night sweats", "fatigue", "weight loss", "loss of appetite", "malaise"]
}

VITAL_RANGES = {
    "Heart Rate (bpm)": {"min": 40, "max": 180, "normal": [60, 100], "default": 75},
    "Systolic BP (mmHg)": {"min": 70, "max": 220, "normal": [90, 120], "default": 120},
    "Diastolic BP (mmHg)": {"min": 40, "max": 140, "normal": [60, 80], "default": 80},
    "Temperature (°C)": {"min": 34.0, "max": 42.0, "normal": [36.1, 37.2], "default": 37.0},
    "O2 Saturation (%)": {"min": 70, "max": 100, "normal": [95, 100], "default": 98},
    "Respiratory Rate (/min)": {"min": 8, "max": 40, "normal": [12, 20], "default": 16}
}

# --- Sidebar: Past Patients Dashboard (Left Menu) ---
with st.sidebar:
    st.header("🗂️ Clinical Chart Dashboard")
    st.markdown("### Past Patients Records")
    st.markdown("---")
    
    if not st.session_state.patient_history:
        st.info("No clinical charts recorded in this active session.")
    else:
        # Loop through saved patients and display their credentials
        for i, record in enumerate(reversed(st.session_state.patient_history)):
            panel_title = f"📋 {record['name']} ({record['age']}{record['sex'][0]})"
            with st.expander(panel_title, expanded=(i==0)):
                st.markdown(f"**Dx:** `{record['diagnosis']}`")
                st.markdown(f"**Severity:** {record['severity'].upper()}")
                st.markdown(f"**Biography:** *{record['biography']}*")
                if record['notes']:
                    st.markdown(f"**Clinical Notes:** {record['notes']}")
                st.markdown(f"**Symptoms Assessed:** {', '.join(record['symptoms']) if record['symptoms'] else 'None'}")
                st.markdown(f"**AI Confidence:** {record['confidence']}%")
                st.caption(f"Logged at: {record['time']}")

# --- Main Interface ---
st.title("⚕️ MedAI Diagnostic Assessment System")
st.markdown("Enter patient metrics below to generate a localized differential diagnosis matrix.")

tab_symp, tab_vitals, tab_patient = st.tabs(["🦠 Symptoms", "🫀 Vital Signs", "📋 Patient Profile"])

# --- Tab 1: Symptoms ---
selected_symptoms = []
with tab_symp:
    st.subheader("Presenting Symptoms")
    cols = st.columns(3)
    for i, (category, symptoms) in enumerate(SYMPTOM_CATEGORIES.items()):
        with cols[i % 3]:
            selections = st.multiselect(category, symptoms, key=category)
            selected_symptoms.extend(selections)
    
    custom_symp = st.text_input("Additional custom symptoms (comma separated):")
    if custom_symp:
        selected_symptoms.extend([s.strip() for s in custom_symp.split(",") if s.strip()])

# --- Tab 2: Vitals ---
vital_inputs = {}
with tab_vitals:
    st.subheader("Clinical Vitals")
    v_cols = st.columns(2)
    for i, (label, config) in enumerate(VITAL_RANGES.items()):
        with v_cols[i % 2]:
            step = 0.1 if "Temperature" in label else 1
            vital_inputs[label] = st.slider(
                label, 
                min_value=float(config["min"]), 
                max_value=float(config["max"]), 
                value=float(config["default"]), 
                step=float(step),
                help=f"Normal Range: {config['normal'][0]} - {config['normal'][1]}"
            )

# --- Tab 3: Patient Profile (With Custom Names and Biographies) ---
with tab_patient:
    st.subheader("Demographics, Biography & History")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        patient_name = st.text_input("Patient Full Name", value="Jane Doe", placeholder="Enter patient identification name")
        age = st.number_input("Age", min_value=1, max_value=120, value=35)
    with p_col2:
        sex = st.selectbox("Biological Sex", ["Female", "Male", "Other"])
        patient_bio = st.text_area("Patient Biography / Medical Background", height=68, 
                                   value="Non-smoker, active lifestyle, history of controlled hypertension.",
                                   placeholder="Brief overview of history, habits, or pre-existing background...")
        
    notes = st.text_area("Current Presentation Notes", height=100, placeholder="e.g., sudden onset of complaints, timeline of severe presentation...")

# --- Mock AI Engine Logic ---
def generate_mock_data(symptoms, vitals):
    is_critical = vitals["Heart Rate (bpm)"] > 130 or vitals["O2 Saturation (%)"] < 90 or "chest pain" in symptoms
    is_moderate = len(symptoms) > 2 or vitals["Temperature (°C)"] > 38.5
    
    if is_critical:
        primary = "Acute Cardiopulmonary Distress"
        severity = "critical"
        confidence = random.randint(85, 95)
        icd = "R07.4"
        actions = ["Immediate emergency department transfer", "Initialize localized oxygen supplementation protocol", "Continuous telemetry monitoring"]
    elif is_moderate:
        primary = "Acute Viral Infection / Systemic Inflammation"
        severity = "moderate"
        confidence = random.randint(75, 88)
        icd = "B97.89"
        actions = ["Order targeted blood pathology panel", "Prescribe localized antipyretics", "Re-evaluate vital metrics q.i.d."]
    else:
        primary = "Idiopathic Mild Presentation"
        severity = "low"
        confidence = random.randint(60, 80)
        icd = "R68.89"
        actions = ["Discharge to home care with explicit warning parameters", "Recommend fluid optimization and clinical rest"]

    return {
        "primaryDiagnosis": {"name": primary, "icdCode": icd, "confidence": confidence, "severity": severity, "category": "General Clinical"},
        "differentialDiagnoses": [
            {"name": "Secondary Bacterial Pathogen", "probability": max(10, confidence - 15), "notes": "Rule out via metabolic culture assessment"},
            {"name": "Stress-Induced Somatization", "probability": max(5, confidence - 35), "notes": "Diagnosis of exclusion following clinical baseline checks"}
        ],
        "riskFactors": ["Epidemiological exposure risks", "Vital metric variance metrics"],
        "recommendedTests": [
            {"test": "Complete Blood Count (CBC) with Differential", "priority": "urgent" if is_critical else "routine", "reason": "Assess baseline infectious and hematological vectors"},
            {"test": "Comprehensive Metabolic Panel (CMP)", "priority": "routine", "reason": "Review hepatic and renal metabolic performance"}
        ],
        "clinicalSummary": f"Patient presents with {len(symptoms)} distinct clinical symptom indices alongside acute vital tracking variations.",
        "immediateActions": actions,
        "prognosis": "Favorable outcome anticipated given rapid adherence to standard clinical protocols.",
        "specialistReferral": "Cardiovascular Medicine" if is_critical else "Internal Medicine Core",
        "redFlags": ["Critical physical indices identified"] if is_critical or is_moderate else ["No immediate critical flags flagged"],
        "disclaimer": "This analytical view operates on localized mock parameters and functions exclusively for deployment evaluation."
    }

# --- Execution UI ---
st.markdown("---")
if st.button("▶ Run AI Diagnostic Matrix", type="primary", use_container_width=True):
    if not selected_symptoms and not notes:
        st.warning("Please toggle presenting symptoms or input current clinical notes to continue evaluation.")
        st.stop()

    with st.spinner("Processing clinical metrics through localized calculation matrices..."):
        time.sleep(1.5)  # Natural diagnostic processing lag
        
        data = generate_mock_data(selected_symptoms, vital_inputs)
        
        # Save enriched profile directly into session history
        st.session_state.patient_history.append({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "name": patient_name if patient_name.strip() else "Anonymous Patient",
            "biography": patient_bio if patient_bio.strip() else "No medical biography provided.",
            "notes": notes,
            "diagnosis": data["primaryDiagnosis"]["name"],
            "severity": data["primaryDiagnosis"]["severity"],
            "confidence": data["primaryDiagnosis"]["confidence"],
            "age": age,
            "sex": sex,
            "symptoms": selected_symptoms
        })
        
        # --- Render Current Diagnostic Results Dashboard ---
        st.success("✅ Assessment Finalized")
        
        pd_data = data["primaryDiagnosis"]
        st.markdown(f"### 🛑 Primary Assessment: {pd_data['name']}")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("ICD-10 Mapping", pd_data["icdCode"])
        m_col2.metric("AI Statistical Confidence", f"{pd_data['confidence']}%")
        m_col3.metric("Triage Severity Status", pd_data['severity'].upper())
        m_col4.metric("Diagnostic Categorization", pd_data["category"])
        
        st.progress(pd_data['confidence'] / 100)
        st.info(f"**Clinical Summary Statement:** {data['clinicalSummary']}")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("⚖️ Differential Matrix")
            st.dataframe(pd.DataFrame(data["differentialDiagnoses"]), use_container_width=True, hide_index=True)
            st.error("**🚨 Identified Red Flags:**\n- " + "\n- ".join(data["redFlags"]))
            st.warning("**⚡ Prescribed Emergency Interventions:**\n- " + "\n- ".join(data["immediateActions"]))

        with col_right:
            st.subheader("🧪 Suggested Lab Orders")
            st.dataframe(pd.DataFrame(data["recommendedTests"]), use_container_width=True, hide_index=True)
            st.subheader("📊 Dynamic Risk Coefficients")
            st.write(", ".join([f"`{rf}`" for rf in data["riskFactors"]]))
            st.markdown(f"**Specialist Pathway:** {data['specialistReferral']}")
            st.markdown(f"**Expected Prognosis:** {data['prognosis']}")
            
        st.caption(f"⚕️ Verification Notice: {data['disclaimer']}")