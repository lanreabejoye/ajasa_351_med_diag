import streamlit as st
import datetime
import time

# --- Page Configuration ---
st.set_page_config(page_title="MedAI Diagnostic System", page_icon="⚕️", layout="wide")

# --- Constants & Clinical Data ---
SYMPTOM_CATEGORIES = {
    "Heart & Chest": ["chest pain", "palpitations", "shortness of breath", "leg swelling", "dizziness", "fainting", "high blood pressure"],
    "Breathing": ["cough", "wheezing", "coughing blood", "chest tightness", "difficulty breathing", "noisy breathing", "phlegm/mucus"],
    "Brain & Nerves": ["headache", "seizures", "memory problems", "shaking/tremor", "weakness", "numbness/tingling", "blurry vision"],
    "Stomach & Gut": ["nausea", "vomiting", "diarrhea", "stomach pain", "bloating", "blood in stool", "yellow skin/eyes"],
    "Joints & Muscles": ["joint pain", "muscle weakness", "back pain", "stiffness", "swollen joints", "can't move well"],
    "Skin": ["rash", "itching", "skin sores", "hair loss", "nail changes", "skin color change"],
    "Hormones & Energy": ["tiredness/fatigue", "weight changes", "very thirsty", "urinating often", "feeling too hot", "feeling too cold"],
    "General": ["fever", "chills", "night sweats", "extreme fatigue", "unexplained weight loss", "no appetite", "generally unwell"]
}

VITAL_RANGES = {
    "heartRate": {"min": 40, "max": 180, "normal": [60, 100], "unit": "bpm", "label": "Heart Rate", "step": 1, "default": 75},
    "bloodPressureSys": {"min": 70, "max": 220, "normal": [90, 120], "unit": "mmHg", "label": "Systolic (Top) Blood Pressure", "step": 1, "default": 120},
    "bloodPressureDia": {"min": 40, "max": 140, "normal": [60, 80], "unit": "mmHg", "label": "Diastolic (Bottom) Blood Pressure", "step": 1, "default": 80},
    "temperature": {"min": 34.0, "max": 42.0, "normal": [36.1, 37.2], "unit": "°C", "label": "Body Temperature", "step": 0.1, "default": 37.0},
    "oxygenSat": {"min": 70, "max": 100, "normal": [95, 100], "unit": "%", "label": "Oxygen Level (SpO₂)", "step": 1, "default": 98},
    "respiratoryRate": {"min": 8, "max": 40, "normal": [12, 20], "unit": "/min", "label": "Breathing Rate", "step": 1, "default": 16}
}

# --- Session State Initialization ---
if "patients" not in st.session_state:
    st.session_state.patients = []
if "symptoms" not in st.session_state:
    st.session_state.symptoms = []
if "vitals" not in st.session_state:
    st.session_state.vitals = {k: v["default"] for k, v in VITAL_RANGES.items()}
if "patient_profile" not in st.session_state:
    st.session_state.patient_profile = {"name": "Fasasi Suliamon", "age": 21, "sex": "Male", "background": "", "notes": ""}
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# --- Helper Functions ---
def clear_form():
    st.session_state.symptoms = []
    st.session_state.vitals = {k: v["default"] for k, v in VITAL_RANGES.items()}
    st.session_state.patient_profile = {"name": "", "age": 35, "sex": "Female", "background": "", "notes": ""}
    st.session_state.current_result = None

def generate_mock_assessment(symptoms, vitals):
    """Localized logic engine that mimics the LLM JSON output structure."""
    time.sleep(1.5)  # Simulate AI processing time
    
    is_critical = vitals.get("heartRate", 75) > 130 or vitals.get("oxygenSat", 98) < 92 or "chest pain" in symptoms
    is_moderate = len(symptoms) >= 3 or vitals.get("temperature", 37.0) > 38.0

    if is_critical:
        level = "go to ER now"
        headline = "Your vital signs and symptoms need immediate medical evaluation."
        happening = "Your body is showing signs of significant stress, likely affecting your heart or lungs. This combination of symptoms can sometimes point to a serious condition that needs immediate checks."
        cond_name = "Cardiopulmonary Distress"
        cond_simple = "Your heart and lungs are struggling to keep up with your body's current demands."
        icd = "R07.4"
        actions = [{"action": "Go to the nearest Emergency Room", "reason": "To get immediate baseline tests like an ECG and blood work.", "urgency": "right now"}]
        specialist = "Emergency Physician"
        spec_desc = "Doctors trained to quickly diagnose and stabilize sudden, severe illnesses."
    elif is_moderate:
        level = "see doctor soon"
        headline = "You have signs of a moderate infection or illness."
        happening = "Your body is fighting off an illness, which is raising your temperature and causing general discomfort. It appears to be a systemic viral or bacterial response."
        cond_name = "Acute Viral/Bacterial Infection"
        cond_simple = "A common infection that is causing widespread physical symptoms."
        icd = "B97.89"
        actions = [{"action": "Schedule a doctor's appointment", "reason": "To get a proper diagnosis and possibly prescription medication to help you fight it.", "urgency": "today"}]
        specialist = "Primary Care Physician"
        spec_desc = "Your main doctor who handles general illnesses and coordinates your overall care."
    else:
        level = "not urgent"
        headline = "Your symptoms appear mild and likely manageable at home."
        happening = "You are experiencing minor symptoms that don't immediately raise major red flags based on your vitals. This is often caused by minor stress, fatigue, or a very mild bug."
        cond_name = "Mild Idiopathic Symptoms"
        cond_simple = "Minor symptoms without a severe underlying cause."
        icd = "R68.89"
        actions = [{"action": "Rest and hydrate", "reason": "Giving your immune system time to recover naturally without intervention.", "urgency": "when convenient"}]
        specialist = "General Practitioner"
        spec_desc = "A general doctor you can see if things don't improve over a few days of rest."

    return {
        "headline": headline,
        "whatIsHappening": happening,
        "whyYouFeelThisWay": "When the body is under stress or fighting an illness, it releases chemicals that can cause fatigue, pain, and fluctuations in your normal vital signs.",
        "howSeriousIsThis": {
            "level": level,
            "plainExplanation": f"Based on the data provided, the triage system classifies this as: {level.upper()}."
        },
        "primaryCondition": {
            "name": cond_name,
            "simpleExplanation": cond_simple,
            "icdCode": icd
        },
        "otherPossibilities": [
            {"name": "Stress/Fatigue Syndrome", "simpleName": "Physical Stress", "chance": "medium", "oneLineExplanation": "Your body's physical reaction to being tired or run down."},
            {"name": "Dehydration", "simpleName": "Low Fluids", "chance": "low", "oneLineExplanation": "Not having enough water in your system."}
        ],
        "whatToDoNow": actions,
        "warningSignsToWatch": [
            {"sign": "Sudden sharp chest pain", "meaning": "Could indicate a sudden cardiovascular issue."},
            {"sign": "Difficulty breathing even when resting", "meaning": "Your lungs might be compromised."}
        ],
        "testsYouMayNeed": [
            {"testName": "Complete Blood Count", "plainName": "Basic Blood Test", "whyNeeded": "To check for infection or anemia.", "urgency": "routine"},
            {"testName": "Comprehensive Metabolic Panel", "plainName": "Metabolic Panel", "whyNeeded": "Checks your basic kidney and liver function.", "urgency": "routine"}
        ],
        "lifestyleAdvice": ["Drink plenty of fluids today", "Get at least 8 hours of continuous sleep", "Monitor your temperature daily"],
        "whoToSee": {
            "specialist": specialist,
            "plainExplanation": spec_desc
        },
        "goodNews": "Your body is designed to signal when something is wrong so you can take action early.",
        "importantReminder": "This assessment is a localized mock demonstration for educational purposes only. Please see a real doctor for proper diagnosis and treatment."
    }

# --- Rendering the Plain Result UI ---
def render_plain_result(result):
    urgency = result.get("howSeriousIsThis", {})
    level = urgency.get("level", "not urgent")
    
    if level == "go to ER now":
        st.error(f"🚨 **EMERGENCY (Go to ER Now):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    elif level == "see doctor soon":
        st.warning(f"⚠️ **SEE DOCTOR SOON (24-48 hrs):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    elif level == "needs attention":
        st.warning(f"❗ **NEEDS ATTENTION (This Week):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    else:
        st.success(f"✅ **NO RUSH:** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
        
    st.markdown("### 🔍 What's Likely Happening")
    st.write(result.get("whatIsHappening"))
    st.info(f"**Why you feel this way:** {result.get('whyYouFeelThisWay')}")
    
    pc = result.get("primaryCondition", {})
    st.markdown("### 🩺 Most Likely Condition")
    st.markdown(f"**{pc.get('name')}** (ICD-10: `{pc.get('icdCode', 'N/A')}`)")
    st.write(pc.get("simpleExplanation"))
    
    others = result.get("otherPossibilities", [])
    if others:
        with st.expander("Other possibilities the doctor may consider"):
            for o in others:
                st.markdown(f"- **{o.get('simpleName') or o.get('name')}** ({o.get('chance')} chance): {o.get('oneLineExplanation')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚡ What To Do Right Now")
        for a in result.get("whatToDoNow", []):
            st.markdown(f"- **{a.get('action')}** ({a.get('urgency')}): *{a.get('reason')}*")
            
        lifestyle = result.get("lifestyleAdvice", [])
        if lifestyle:
            st.markdown("### 🏡 Simple Home Tips")
            for tip in lifestyle:
                st.markdown(f"- {tip}")
                
    with col2:
        tests = result.get("testsYouMayNeed", [])
        if tests:
            st.markdown("### 🧪 Tests Your Doctor Might Order")
            for t in tests:
                st.markdown(f"- **{t.get('plainName') or t.get('testName')}** ({t.get('urgency')}): *{t.get('whyNeeded')}*")
                
        who = result.get("whoToSee")
        if who:
            st.markdown("### 👨‍⚕️ Who To See")
            st.markdown(f"**{who.get('specialist')}**: {who.get('plainExplanation')}")
            
    flags = result.get("warningSignsToWatch", [])
    if flags:
        st.error("**⚠️ Warning Signs — Go to ER if you notice these:**\n" + "\n".join([f"- **{w.get('sign')}**: {w.get('meaning')}" for w in flags]))
        
    if result.get("goodNews"):
        st.success(f"**The Good News:** {result.get('goodNews')}")
        
    st.caption(f"⚕️ {result.get('importantReminder')}")


# --- Sidebar Dashboard (Persistently Visible) ---
with st.sidebar:
    st.title("⚕️ MedAI Dashboard")
    st.caption("Standalone Clinical Triage Engine")
    st.divider()
    
    st.header("🗂️ Patient Credentials")
    if not st.session_state.patients:
        st.info("No credentials recorded yet. Run an assessment and save it to build your patient list here.")
    else:
        # Loops through all saved patients and displays their credentials directly in the sidebar
        for i, record in enumerate(st.session_state.patients):
            panel_title = f"📋 {record['name']} ({record['age']}{record['sex'][0]})"
            with st.expander(panel_title, expanded=(i==0)):
                st.write(f"**Medical Bio:** *{record['background'] if record['background'] else 'None provided'}*")
                st.write(f"**Symptoms:** {', '.join(record['symptoms']) if record['symptoms'] else 'None'}")
                if record.get("result"):
                    urgency = record["result"]["howSeriousIsThis"]["level"]
                    st.markdown(f"**Urgency:** `{urgency.upper()}`")
                    st.markdown(f"**Diagnosis:** {record['result']['primaryCondition']['name']}")
                st.caption(f"Saved: {record['savedAt']}")

    st.divider()
    st.header("🧭 Navigation")
    view = st.radio("Select Interface:", ["➕ New Assessment", "🏥 Patient Records Database"])


# --- Main Application Header (Persistently Visible) ---
st.title("⚕️ MedAI Diagnostic Assistant")
st.markdown("**Overview:** A clinical-grade triage system that translates patient symptoms and vitals into structured, plain-language medical assessments. Built for localized, standalone demonstrations.")
st.divider()


# --- Split Views ---
if view == "➕ New Assessment":
    st.subheader("New Patient Assessment")
    st.write("") # Spacer

    col_input, col_summary = st.columns([1.5, 1], gap="large")

    with col_input:
        tab_symp, tab_vitals, tab_profile = st.tabs(["🦠 Symptoms", "🫀 Vitals", "📋 Profile"])
        
        with tab_symp:
            st.markdown("##### Presenting Symptoms")
            for cat, syms in SYMPTOM_CATEGORIES.items():
                selections = st.multiselect(cat, syms, default=[s for s in st.session_state.symptoms if s in syms], key=f"ms_{cat}")
                for s in syms:
                    if s in selections and s not in st.session_state.symptoms:
                        st.session_state.symptoms.append(s)
                    elif s not in selections and s in st.session_state.symptoms:
                        st.session_state.symptoms.remove(s)
            
            custom = st.text_input("Add custom symptom (press enter)")
            if custom and custom not in st.session_state.symptoms:
                st.session_state.symptoms.append(custom)
                
        with tab_vitals:
            st.markdown("##### Vital Signs")
            for key, cfg in VITAL_RANGES.items():
                st.session_state.vitals[key] = st.slider(
                    cfg["label"], 
                    min_value=float(cfg["min"]), max_value=float(cfg["max"]),
                    value=float(st.session_state.vitals[key]), step=float(cfg["step"]),
                    help=f"Normal: {cfg['normal'][0]} - {cfg['normal'][1]} {cfg['unit']}"
                )
                
        with tab_profile:
            st.markdown("##### Demographics & History")
            p1, p2 = st.columns(2)
            st.session_state.patient_profile["name"] = p1.text_input("Patient Name", value=st.session_state.patient_profile["name"], placeholder="Jane Doe")
            st.session_state.patient_profile["age"] = p2.number_input("Age", min_value=1, max_value=120, value=st.session_state.patient_profile["age"])
            st.session_state.patient_profile["sex"] = p1.selectbox("Biological Sex", ["Female", "Male", "Other"], index=["Female", "Male", "Other"].index(st.session_state.patient_profile["sex"]))
            st.session_state.patient_profile["background"] = st.text_area("Medical Background", value=st.session_state.patient_profile["background"], placeholder="e.g. has diabetes, takes BP medication...")
            st.session_state.patient_profile["notes"] = st.text_area("How are you feeling?", value=st.session_state.patient_profile["notes"], placeholder="Describe what's happening in your own words...")

    with col_summary:
        st.markdown("### 📊 Assessment Summary")
        st.markdown(f"**Patient:** {st.session_state.patient_profile['name'] or 'Anonymous'} ({st.session_state.patient_profile['age']} {st.session_state.patient_profile['sex'][0]})")
        st.markdown(f"**Symptoms:** {len(st.session_state.symptoms)} selected")
        abnormals = len([k for k, v in st.session_state.vitals.items() if v < VITAL_RANGES[k]["normal"][0] or v > VITAL_RANGES[k]["normal"][1]])
        st.markdown(f"**Abnormal Vitals:** {abnormals} flagged")
        
        st.divider()
        
        if st.button("▶ Run AI Assessment", type="primary", use_container_width=True):
            if not st.session_state.symptoms and not st.session_state.patient_profile["notes"]:
                st.warning("Please select at least one symptom or add notes to proceed.")
            else:
                with st.spinner("Processing clinical metrics through localized neural engine..."):
                    st.session_state.current_result = generate_mock_assessment(
                        st.session_state.symptoms, 
                        st.session_state.vitals
                    )

        if st.session_state.current_result:
            if st.button("💾 Save to Patient Records", use_container_width=True):
                record = {
                    "id": datetime.datetime.now().isoformat(),
                    "name": st.session_state.patient_profile["name"] or "Anonymous Patient",
                    "age": st.session_state.patient_profile["age"],
                    "sex": st.session_state.patient_profile["sex"],
                    "background": st.session_state.patient_profile["background"],
                    "notes": st.session_state.patient_profile["notes"],
                    "symptoms": list(st.session_state.symptoms),
                    "vitals": dict(st.session_state.vitals),
                    "result": dict(st.session_state.current_result),
                    "savedAt": datetime.datetime.now().strftime("%d %b %Y, %H:%M")
                }
                # Add to the top of the list so it appears instantly in the sidebar
                st.session_state.patients.insert(0, record)
                st.success("Credentials saved to the left dashboard!")

        if st.button("🗑️ Clear & Start Over", use_container_width=True):
            clear_form()
            st.rerun()

    # Render Result if present at the bottom of the main screen
    if st.session_state.current_result:
        st.divider()
        render_plain_result(st.session_state.current_result)

else:
    st.subheader("Manage Saved Patient Records")
    
    if not st.session_state.patients:
        st.info("No records yet. Switch to the 'New Assessment' interface to analyze and save patient data.")
    else:
        col_list, col_detail = st.columns([1, 2], gap="large")
        
        with col_list:
            st.write(f"**Saved Patients ({len(st.session_state.patients)})**")
            selected_record_id = st.radio(
                "Select Record:", 
                options=[p["id"] for p in st.session_state.patients],
                format_func=lambda x: [p["name"] for p in st.session_state.patients if p["id"] == x][0] + " - " + [p["savedAt"] for p in st.session_state.patients if p["id"] == x][0]
            )
            
            if st.button("Delete Selected Patient", type="secondary"):
                st.session_state.patients = [p for p in st.session_state.patients if p["id"] != selected_record_id]
                st.rerun()
                
        with col_detail:
            selected_record = next((p for p in st.session_state.patients if p["id"] == selected_record_id), None)
            if selected_record:
                st.markdown(f"### 📋 {selected_record['name']} ({selected_record['age']}{selected_record['sex'][0]})")
                st.caption(f"Recorded at: {selected_record['savedAt']}")
                if selected_record['symptoms']:
                    st.write(f"**Symptoms:** {', '.join(selected_record['symptoms'])}")
                st.divider()
                render_plain_result(selected_record['result'])