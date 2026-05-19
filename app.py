import streamlit as st
import anthropic
import json
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="MedAI Diagnostic System", page_icon="⚕️", layout="wide")

# --- Constants & Clinical Data ---
SYSTEM_PROMPT = """You are MedAI, a clinical-grade AI diagnostic assistant. You analyze patient symptoms and medical metrics with precision.
When given symptoms or metrics, you must respond with a JSON object ONLY (no markdown formatting outside the JSON block).
Schema:
{
  "primaryDiagnosis": { "name": "Disease Name", "icdCode": "ICD-10 Code", "confidence": 0-100, "severity": "low|moderate|high|critical", "category": "category" },
  "differentialDiagnoses": [ { "name": "Condition", "probability": 0-100, "notes": "brief clinical reason" } ],
  "riskFactors": ["factor1", "factor2"],
  "recommendedTests": [ { "test": "Test Name", "priority": "urgent|routine|optional", "reason": "why" } ],
  "clinicalSummary": "2-3 sentence clinical summary",
  "immediateActions": ["action1", "action2"],
  "prognosis": "Brief prognosis statement",
  "specialistReferral": "Which specialist and urgency level",
  "redFlags": ["warning sign 1", "warning sign 2"],
  "disclaimer": "This AI analysis is for educational purposes only and must not replace professional medical diagnosis."
}"""

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

# --- Sidebar configuration ---
with st.sidebar:
    st.header("⚙️ System Configuration")
    api_key = st.text_input("Anthropic API Key", type="password", help="Enter your Claude API key to power the diagnostic engine.")
    st.markdown("---")
    st.markdown("**Model Engine:** Claude 3.5 Sonnet\n\n**Mode:** Clinical Triage & Assessment")

st.title("⚕️ MedAI Diagnostic Assessment System")
st.markdown("Enter patient metrics below to generate a highly technical differential diagnosis matrix.")

# --- UI Layout (Tabs) ---
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
    notes = st.text_area("Clinical Notes / Past Medical History", height=150, placeholder="e.g., known diabetic, recent travel, current medications...")

# --- Engine Logic ---
st.markdown("---")
if st.button("▶ Run AI Diagnostic Matrix", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ Please enter your Anthropic API Key in the sidebar to run the analysis.")
        st.stop()
        
    if not selected_symptoms and not notes:
        st.warning("Please enter at least one symptom or clinical note to proceed.")
        st.stop()

    # 1. Flag Abnormal Vitals
    abnormal_vitals = []
    for label, val in vital_inputs.items():
        normal = VITAL_RANGES[label]["normal"]
        if val < normal[0] or val > normal[1]:
            abnormal_vitals.append(f"{label}: {val} (Abnormal)")

    # 2. Build the Prompt
    prompt = f"""
    Patient Profile: Age {age}, Sex: {sex}
    Clinical Notes: {notes if notes else 'None'}
    
    Presenting Symptoms: {', '.join(selected_symptoms) if selected_symptoms else 'None reported'}
    
    Vital Signs:
    {json.dumps(vital_inputs, indent=2)}
    Abnormal Vitals Flagged: {', '.join(abnormal_vitals) if abnormal_vitals else 'None - All within normal limits'}
    
    Provide a comprehensive clinical assessment.
    """

    with st.spinner("Analyzing patient vector data via Claude 3.5 Sonnet..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            raw_text = response.content[0].text
            # Clean up potential markdown formatting around the JSON
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
                
            data = json.loads(raw_text.strip())
            
            # --- Render Technical Dashboard ---
            st.success("✅ Analysis Complete")
            
            # Primary Diagnosis
            pd_data = data["primaryDiagnosis"]
            st.markdown(f"### 🛑 Primary Diagnosis: {pd_data['name']}")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("ICD-10 Code", pd_data.get("icdCode", "N/A"))
            m_col2.metric("AI Confidence", f"{pd_data['confidence']}%")
            m_col3.metric("Severity", pd_data['severity'].upper())
            m_col4.metric("Category", pd_data.get("category", "N/A"))
            
            st.progress(pd_data['confidence'] / 100)
            
            st.info(f"**Clinical Summary:** {data['clinicalSummary']}")
            
            # Two-Column Technical Layout
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("⚖️ Differential Diagnoses")
                diff_df = pd.DataFrame(data["differentialDiagnoses"])
                st.dataframe(diff_df, use_container_width=True, hide_index=True)
                
                if data.get("redFlags"):
                    st.error("**🚨 Red Flags Identified:**\n- " + "\n- ".join(data["redFlags"]))
                    
                if data.get("immediateActions"):
                    st.warning("**⚡ Immediate Clinical Actions:**\n- " + "\n- ".join(data["immediateActions"]))

            with col_right:
                st.subheader("🧪 Recommended Investigations")
                tests_df = pd.DataFrame(data["recommendedTests"])
                st.dataframe(tests_df, use_container_width=True, hide_index=True)
                
                st.subheader("📊 Risk Factors")
                st.write(", ".join([f"`{rf}`" for rf in data["riskFactors"]]))
                
                st.markdown(f"**Specialist Referral:** {data.get('specialistReferral', 'None indicated')}")
                st.markdown(f"**Prognosis:** {data.get('prognosis', 'Pending further investigation')}")
                
            st.caption(f"⚕️ Disclaimer: {data['disclaimer']}")

        except Exception as e:
            st.error(f"API Error or JSON Parsing Error: {str(e)}")