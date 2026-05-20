import streamlit as st
import json
import datetime
from anthropic import Anthropic

# --- Page Configuration ---
st.set_page_config(page_title="MedAI Diagnostic System", page_icon="⚕️", layout="wide")

# --- Constants & Prompts ---
SYSTEM_PROMPT = """You are MedAI, a compassionate AI health assistant. Your job is to explain health assessments in plain, simple language that any person — with no medical background — can fully understand.

CRITICAL RULES:
- Never use medical jargon without immediately explaining it in brackets
- Write as if explaining to a worried friend, not a doctor
- Be honest but kind and reassuring where appropriate
- Always emphasize that this is for educational understanding only

Respond ONLY with a valid JSON object (no markdown, no backticks):

{
  "headline": "One sentence that tells the patient exactly what's happening in plain English",
  "whatIsHappening": "2-3 sentences explaining the likely condition as if to a non-medical person. Use everyday language.",
  "whyYouFeelThisWay": "1-2 sentences explaining WHY these symptoms occur in the body, in simple terms.",
  "howSeriousIsThis": {
    "level": "not urgent|needs attention|see doctor soon|go to ER now",
    "plainExplanation": "One sentence explaining what this urgency level means for them today"
  },
  "primaryCondition": {
    "name": "Condition name",
    "simpleExplanation": "What this condition actually is in one simple sentence",
    "icdCode": "ICD-10 code"
  },
  "otherPossibilities": [
    { "name": "Condition", "simpleName": "What to call it in plain terms", "chance": "low|medium|high", "oneLineExplanation": "Simple one-line explanation" }
  ],
  "whatToDoNow": [
    { "action": "Specific action", "reason": "Why this helps, in plain terms", "urgency": "right now|today|this week|when convenient" }
  ],
  "warningSignsToWatch": [
    { "sign": "Warning sign in plain language", "meaning": "What this sign means if it appears" }
  ],
  "testsYouMayNeed": [
    { "testName": "Test name", "plainName": "What most people call it", "whyNeeded": "In plain terms, why this test helps", "urgency": "urgent|soon|routine" }
  ],
  "lifestyleAdvice": ["Simple, actionable tip 1", "tip 2", "tip 3"],
  "whoToSee": {
    "specialist": "Type of doctor",
    "plainExplanation": "What this type of doctor does and why they're the right person"
  },
  "goodNews": "One encouraging, honest sentence about the outlook",
  "importantReminder": "Always include: This assessment is for educational purposes only. Please see a real doctor for proper diagnosis and treatment."
}"""

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
    st.session_state.patient_profile = {"name": "", "age": 35, "sex": "Female", "background": "", "notes": ""}
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# --- Helper Functions ---
def clear_form():
    st.session_state.symptoms = []
    st.session_state.vitals = {k: v["default"] for k, v in VITAL_RANGES.items()}
    st.session_state.patient_profile = {"name": "", "age": 35, "sex": "Female", "background": "", "notes": ""}
    st.session_state.current_result = None

def build_prompt():
    v = st.session_state.vitals
    p = st.session_state.patient_profile
    s = st.session_state.symptoms
    
    abnormal = []
    for k, val in v.items():
        cfg = VITAL_RANGES[k]
        if val < cfg["normal"][0] or val > cfg["normal"][1]:
            abnormal.append(f'{cfg["label"]}: {val} {cfg["unit"]} — ABNORMAL')
            
    symptoms_text = ", ".join(s) if s else "None selected"
    abnormal_text = "FLAGGED ABNORMAL VITALS:\n" + "\n".join(abnormal) if abnormal else "All vitals are within normal range."
    
    return f"""Patient: {p['name'] or 'Anonymous'}, {p['age']} years old, {p['sex']}
Background: {p['background'] or 'Not provided'}
Additional notes: {p['notes'] or 'None'}

Symptoms reported: {symptoms_text}

Vital signs:
- Heart rate: {v['heartRate']} bpm
- Blood pressure: {v['bloodPressureSys']}/{v['bloodPressureDia']} mmHg
- Temperature: {v['temperature']}°C
- Oxygen level: {v['oxygenSat']}%
- Breathing rate: {v['respiratoryRate']}/min

{abnormal_text}

Please provide a plain-language assessment that this patient can fully understand."""

# --- Rendering the Plain Result UI ---
def render_plain_result(result):
    urgency = result.get("howSeriousIsThis", {})
    level = urgency.get("level", "not urgent")
    
    # 1. Headline Urgency Banner
    if level == "go to ER now":
        st.error(f"🚨 **EMERGENCY (Go to ER Now):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    elif level == "see doctor soon":
        st.warning(f"⚠️ **SEE DOCTOR SOON (24-48 hrs):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    elif level == "needs attention":
        st.warning(f"❗ **NEEDS ATTENTION (This Week):** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
    else:
        st.success(f"✅ **NO RUSH:** {result.get('headline')}\n\n*{urgency.get('plainExplanation')}*")
        
    # 2. What's Happening & Why
    st.markdown("### 🔍 What's Likely Happening")
    st.write(result.get("whatIsHappening"))
    st.info(f"**Why you feel this way:** {result.get('whyYouFeelThisWay')}")
    
    # 3. Primary Condition
    pc = result.get("primaryCondition", {})
    st.markdown("### 🩺 Most Likely Condition")
    st.markdown(f"**{pc.get('name')}** (ICD-10: `{pc.get('icdCode', 'N/A')}`)")
    st.write(pc.get("simpleExplanation"))
    
    # 4. Other Possibilities
    others = result.get("otherPossibilities", [])
    if others:
        with st.expander("Other possibilities the doctor may consider"):
            for o in others:
                st.markdown(f"- **{o.get('simpleName') or o.get('name')}** ({o.get('chance')} chance): {o.get('oneLineExplanation')}")

    col1, col2 = st.columns(2)
    # 5. What to do now & Lifestyle
    with col1:
        st.markdown("### ⚡ What To Do Right Now")
        for a in result.get("whatToDoNow", []):
            st.markdown(f"- **{a.get('action')}** ({a.get('urgency')}): *{a.get('reason')}*")
            
        lifestyle = result.get("lifestyleAdvice", [])
        if lifestyle:
            st.markdown("### 🏡 Simple Home Tips")
            for tip in lifestyle:
                st.markdown(f"- {tip}")
                
    # 6. Tests & Who to see
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
            
    # 7. Red Flags & Good News
    flags = result.get("warningSignsToWatch", [])
    if flags:
        st.error("**⚠️ Warning Signs — Go to ER if you notice these:**\n" + "\n".join([f"- **{w.get('sign')}**: {w.get('meaning')}" for w in flags]))
        
    if result.get("goodNews"):
        st.success(f"**The Good News:** {result.get('goodNews')}")
        
    st.caption(f"⚕️ {result.get('importantReminder')}")

# --- Application Layout ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Anthropic API Key", type="password", help="Required to run the analysis engine.")
    st.divider()
    
    st.header("🗂️ Navigation")
    view = st.radio("Select View:", ["➕ New Assessment", "🏥 Patient Records"])

if view == "➕ New Assessment":
    col_input, col_summary = st.columns([1.5, 1], gap="large")
    
    with col_input:
        tab_symp, tab_vitals, tab_profile = st.tabs(["🦠 Symptoms", "🫀 Vitals", "📋 Profile"])
        
        with tab_symp:
            st.subheader("Presenting Symptoms")
            for cat, syms in SYMPTOM_CATEGORIES.items():
                selections = st.multiselect(cat, syms, default=[s for s in st.session_state.symptoms if s in syms], key=f"ms_{cat}")
                # Update global state silently
                for s in syms:
                    if s in selections and s not in st.session_state.symptoms:
                        st.session_state.symptoms.append(s)
                    elif s not in selections and s in st.session_state.symptoms:
                        st.session_state.symptoms.remove(s)
            
            custom = st.text_input("Add custom symptom (press enter)")
            if custom and custom not in st.session_state.symptoms:
                st.session_state.symptoms.append(custom)
                
        with tab_vitals:
            st.subheader("Vital Signs")
            for key, cfg in VITAL_RANGES.items():
                st.session_state.vitals[key] = st.slider(
                    cfg["label"], 
                    min_value=float(cfg["min"]), max_value=float(cfg["max"]),
                    value=float(st.session_state.vitals[key]), step=float(cfg["step"]),
                    help=f"Normal: {cfg['normal'][0]} - {cfg['normal'][1]} {cfg['unit']}"
                )
                
        with tab_profile:
            st.subheader("Demographics & History")
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
            if not api_key:
                st.error("Please enter your Anthropic API Key in the sidebar.")
            elif not st.session_state.symptoms and not st.session_state.patient_profile["notes"]:
                st.warning("Please select at least one symptom or add notes to proceed.")
            else:
                with st.spinner("Analyzing your symptoms and vitals..."):
                    try:
                        client = Anthropic(api_key=api_key)
                        response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1500,
                            system=SYSTEM_PROMPT,
                            messages=[{"role": "user", "content": build_prompt()}]
                        )
                        raw_text = response.content[0].text.strip()
                        # Clean up markdown
                        if "```json" in raw_text:
                            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in raw_text:
                            raw_text = raw_text.split("```")[1].split("```")[0].strip()
                            
                        st.session_state.current_result = json.loads(raw_text)
                    except Exception as e:
                        st.error(f"Analysis Failed: {str(e)}")

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
                st.session_state.patients.insert(0, record)
                st.success("Saved to database!")

        if st.button("🗑️ Clear & Start Over", use_container_width=True):
            clear_form()
            st.rerun()

    # Render Result if present
    if st.session_state.current_result:
        st.divider()
        render_plain_result(st.session_state.current_result)

else:
    # Patient Records View
    st.header("🏥 Patient Records Database")
    
    if not st.session_state.patients:
        st.info("No records yet. Run an assessment and save it to start building the database.")
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
                st.subheader(f"📋 {selected_record['name']} ({selected_record['age']}{selected_record['sex'][0]})")
                st.caption(f"Recorded at: {selected_record['savedAt']}")
                if selected_record['symptoms']:
                    st.write(f"**Symptoms:** {', '.join(selected_record['symptoms'])}")
                st.divider()
                render_plain_result(selected_record['result'])