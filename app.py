import streamlit as st
import pandas as pd
import time
import random

# --- Page Configuration ---
st.set_page_config(page_title="MedAI Diagnostic System", page_icon="⚕️", layout="wide")

# --- State Management for Past Patients ---
if "patient_history" not in st.session_state:
    st.session_state.patient_history = []

# --- Constants & Clinical Data ---
SYMPTOM_CATEGORIES = {
    "Cardiovascular": ["chest pain", "palpitations", "shortness of breath", "leg swelling", "dizziness", "syncope"],
    "Respiratory": ["cough", "wheezing", "hemoptysis", "pleuritic pain", "dyspnea", "sputum production"],
    "Neurological": ["headache", "seizures", "memory loss", "tremor", "weakness", "numbness", "vision changes"],
    "Gastrointestinal": ["nausea", "vomiting", "diarrhea", "abdominal pain", "bloating", "blood in stool", "jaundice"],
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

# --- Sidebar: Past Patients Dashboard ---
with st.sidebar:
    st.header("🗂️ Past Patients Diagnosis")
    st.markdown("---")
    
    if not st.session_state.patient_history:
        st.info("No past patient records found in this session.")
    else:
        for i, record in enumerate(reversed(st.session_state.patient_history)):
            with st.expander(f"Patient {len(st.session_state.patient_history) - i}: {record['diagnosis']}", expanded=(i==0)):
                st.markdown(f"**Severity:** {record['severity'].upper()}")
                st.markdown(f"**Demographics:** {record['age']} yrs | {record['sex']}")
                st.markdown(f"**Symptoms:** {', '.join(record['symptoms']) if record['symptoms'] else 'None'}")
                st.markdown(f"**Confidence:** {record['confidence']}%")
                st.caption(f"Time: {record['time']}")

# --- Main Interface ---
st.title("⚕️ MedAI Diagnostic Assessment System")
st.markdown("Enter patient metrics below to generate a highly technical differential diagnosis matrix.")

tab_symp, tab_vitals, tab_patient = st.tabs(["🦠 Symptoms", "🫀 Vital Signs", "📋 Patient Profile"])

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

with tab_patient:
    st.subheader("Demographics & History")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=35)
    with p_col2:
        sex = st.selectbox("Biological Sex", ["Male", "Female", "Other"])
    notes = st.text_area("Clinical Notes / Past Medical History", height=150, placeholder="e.g., known diabetic, recent travel...")

# --- Mock Engine Logic ---
def generate_mock_data(symptoms, vitals):
    # Determines severity based on basic input heuristics
    is_critical = vitals["Heart Rate (bpm)"] > 130 or vitals["O2 Saturation (%)"] < 90 or "chest pain" in symptoms
    is_moderate = len(symptoms) > 2 or vitals["Temperature (°C)"] > 38.5
    
    if is_critical:
        primary = "Acute Cardiopulmonary Distress"
        severity = "critical"
        confidence = random.randint(85, 95)
        icd = "R07.4"
        actions = ["Immediate ER transfer", "Start supplemental oxygen", "Continuous ECG monitoring"]
    elif is_moderate:
        primary = "Acute Viral Infection / Inflammation"
        severity = "moderate"
        confidence = random.randint(75, 88)
        icd = "B97.89"
        actions = ["Schedule outpatient lab work", "Prescribe antipyretics", "Monitor vitals every 4 hours"]
    else:
        primary = "Idiopathic Mild Syndrome"
        severity = "low"
        confidence = random.randint(60, 80)
        icd = "R68.89"
        actions = ["Discharge with instructions", "Rest and hydration"]

    return {
        "primaryDiagnosis": {"name": primary, "icdCode": icd, "confidence": confidence, "severity": severity, "category": "General"},
        "differentialDiagnoses": [
            {"name": "Secondary Bacterial Pathogen", "probability": confidence - 15, "notes": "Rule out via cultures"},
            {"name": "Stress-Induced Somatization", "probability": confidence - 35, "notes": "Diagnosis of exclusion"}
        ],
        "riskFactors": ["Age-related factors", "Recent exposure risks"],
        "recommendedTests": [
            {"test": "Complete Blood Count (CBC)", "priority": "urgent" if is_critical else "routine", "reason": "Baseline infectious markers"},
            {"test": "Comprehensive Metabolic Panel", "priority": "routine", "reason": "Organ function review"}
        ],
        "clinicalSummary": f"Patient presents with {len(symptoms)} reported symptoms and variations in resting vitals requiring assessment.",
        "immediateActions": actions,
        "prognosis": "Favorable with immediate compliance to the recommended medical pathway.",
        "specialistReferral": "Cardiology" if is_critical else "General Medicine",
        "redFlags": ["Abnormal vital ranges detected"] if is_critical or is_moderate else ["None observed"],
        "disclaimer": "This AI analysis is a localized mock demonstration for educational purposes only."
    }

# --- Execution UI ---
st.markdown("---")
if st.button("▶ Run AI Diagnostic Matrix", type="primary", use_container_width=True):
    if not selected_symptoms and not notes:
        st.warning("Please enter at least one symptom or clinical note to proceed.")
        st.stop()

    with st.spinner("Analyzing patient vector data via Localized Neural Mock Engine..."):
        time.sleep(2) # Simulates processing time
        
        data = generate_mock_data(selected_symptoms, vital_inputs)
        
        # Save to History
        import datetime
        st.session_state.patient_history.append({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "diagnosis": data["primaryDiagnosis"]["name"],
            "severity": data["primaryDiagnosis"]["severity"],
            "confidence": data["primaryDiagnosis"]["confidence"],
            "age": age,
            "sex": sex,
            "symptoms": selected_symptoms
        })
        
        # Render Technical Dashboard
        st.success("✅ Analysis Complete")
        
        pd_data = data["primaryDiagnosis"]
        st.markdown(f"### 🛑 Primary Diagnosis: {pd_data['name']}")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("ICD-10 Code", pd_data["icdCode"])
        m_col2.metric("AI Confidence", f"{pd_data['confidence']}%")
        m_col3.metric("Severity", pd_data['severity'].upper())
        m_col4.metric("Category", pd_data["category"])
        
        st.progress(pd_data['confidence'] / 100)
        st.info(f"**Clinical Summary:** {data['clinicalSummary']}")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("⚖️ Differential Diagnoses")
            st.dataframe(pd.DataFrame(data["differentialDiagnoses"]), use_container_width=True, hide_index=True)
            st.error("**🚨 Red Flags Identified:**\n- " + "\n- ".join(data["redFlags"]))
            st.warning("**⚡ Immediate Clinical Actions:**\n- " + "\n- ".join(data["immediateActions"]))

        with col_right:
            st.subheader("🧪 Recommended Investigations")
            st.dataframe(pd.DataFrame(data["recommendedTests"]), use_container_width=True, hide_index=True)
            st.subheader("📊 Risk Factors")
            st.write(", ".join([f"`{rf}`" for rf in data["riskFactors"]]))
            st.markdown(f"**Specialist Referral:** {data['specialistReferral']}")
            st.markdown(f"**Prognosis:** {data['prognosis']}")
            
        st.caption(f"⚕️ Disclaimer: {data['disclaimer']}")