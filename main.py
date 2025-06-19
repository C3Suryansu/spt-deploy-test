# streamlit_app.py  (two-page flow)
import streamlit as st
from pydantic import BaseModel, ValidationError
from typing import Optional

# -------- helpers -------- #
def goto(page: str):
    st.session_state.page = page


if "page" not in st.session_state:
    st.session_state.page = "info"

# -------- salary model & logic (unchanged) -------- #
class SalaryInput(BaseModel):
    working: bool
    relevant_degree: Optional[bool] = None
    ds_projects: Optional[bool] = None
    skills_rating: int = 0
    college_tier: str
    certifications: bool
    location: Optional[str] = None
    domain: Optional[str] = None
    current_company: Optional[str] = None
    data_related: Optional[bool] = None
    yo_experience: int = 0
    interested_in_ds: Optional[bool] = None


def calculate_salary(data: SalaryInput):
    def modifiers() -> int:
        pct = 0
        pct += 15 if data.college_tier == "tier1" else (-10 if data.college_tier == "tier3" else 0)
        pct += 5 if data.certifications else 0
        pct += 10 if data.location == "metro" else 0
        pct += 10 if data.domain in ["tech", "bfsi"] else 0
        if data.working:
            pct += 20 if data.current_company == "top_mnc" else (-10 if data.current_company == "service_small" else 0)
        return pct

    mod = modifiers()
    # … (same branching as before) …
    # --- Freshers ---
    if not data.working:
        if not data.relevant_degree:
            base = (2.5, 4)
        elif not data.ds_projects:
            base = (3, 5)
        elif data.skills_rating >= 3:
            base = (4, 8)
        else:
            base = (3, 6)
        final = tuple(round(x * (1 + mod / 100), 2) for x in base)
        return {"final": final, "mod": mod}

    # --- Working, non-data role ---
    if not data.data_related:
        if not data.interested_in_ds:
            base = (3, 6)
        elif data.skills_rating >= 3:
            base = (4, 9)
        else:
            base = (3, 6)
        final = tuple(round(x * (1 + mod / 100), 2) for x in base)
        return {"final": final, "mod": mod}

    # --- Working, data-related role ---
    if data.yo_experience > 2 and data.skills_rating >= 4:
        return {"hike": "30–35 % (Data Science)", "mod": mod}
    if (data.yo_experience > 2 and data.skills_rating < 4) or (
        data.yo_experience <= 2 and data.skills_rating >= 4
    ):
        return {"hike": "20–25 % (Business Analytics)", "mod": mod}

    base = (3, 6)
    final = tuple(round(x * (1 + mod / 100), 2) for x in base)
    return {"final": final, "mod": mod}


# -------- UI -------- #
st.set_page_config(page_title="Salary Predictor", page_icon="💰", layout="centered")

# == Page 1 : Personal info + working status ==
if st.session_state.page == "info":
    st.title("Candidate Information")

    with st.form("info_form"):
        name  = st.text_input("Full Name")
        email = st.text_input("E-mail")
        phone = st.text_input("Contact Number")

        working_choice = st.radio(
            "Current employment status",
            options=[True, False],
            format_func=lambda x: "Working" if x else "Not Working",
            horizontal=True,
        )

        submitted = st.form_submit_button("Next ➜")

    if submitted:
        if not (name and email and phone):
            st.warning("Please fill in all the fields.")
        else:
            st.session_state.personal = {
                "name": name,
                "email": email,
                "phone": phone,
                "working": working_choice,
            }
            goto("predict")

# == Page 2 : Prediction form ==
elif st.session_state.page == "predict":
    p = st.session_state.personal
    st.markdown(
        f"**Name:** {p['name']} &nbsp;&nbsp; **Email:** {p['email']} "
        f"&nbsp;&nbsp; **Phone:** {p['phone']} &nbsp;&nbsp; "
        f"**Status:** {'Working' if p['working'] else 'Not Working'}"
    )
    st.button("⬅ Back", on_click=goto, args=("info",))

    st.title("💰 Salary Prediction Tool")

    # sidebar form
    with st.sidebar:
        st.header("Candidate Details")

        # working status comes from page 1
        working = p["working"]

        # ask freshers-only fields
        relevant_degree = st.checkbox("Has Relevant Degree?") if not working else None
        ds_projects     = st.checkbox("Data-Science Projects Done?") if not working else None

        skills_rating   = st.slider("Skills Rating (1–5)", 1, 5, 3)
        college_tier    = st.selectbox("College Tier", ["tier1", "tier2", "tier3"])
        certifications  = st.checkbox("Any Certifications?")
        
        location        = None # st.selectbox("Location", ["metro", "non-metro"])
        domain          = None # st.selectbox("Domain", ["tech", "bfsi", "other"])
        current_company = None
        data_related    = None
        yo_experience   = 0
        interested_in_ds= None

        if working:
            current_company = st.selectbox(
                "Current Company Type", ["", "top_mnc", "startup", "service_small"], index=0
            )
            data_related = st.checkbox("Current Role is Data-Related?")
            yo_experience = st.number_input("Years of Experience", min_value=0, step=1)
            if not data_related:
                interested_in_ds = st.checkbox("Interested in DS Transition?")

    # ---- Predict button ----
    if st.button("Predict", type="primary"):
        try:
            payload = SalaryInput(
                working=working,
                relevant_degree=relevant_degree,
                ds_projects=ds_projects,
                skills_rating=skills_rating,
                college_tier=college_tier,
                certifications=certifications,
                location=location,
                domain=domain,
                current_company=current_company or None,
                data_related=data_related,
                yo_experience=yo_experience,
                interested_in_ds=interested_in_ds,
            )
            result = calculate_salary(payload)

            st.subheader("Result")
            if "final" in result:
                low, high = result["final"]
                st.success(
                    f"Estimated range: **₹ {low} LPA – ₹ {high} LPA**  \n"
                    f"Expected Roles: DA and BA \n"
                    f"\n Journey in 3 years: Can go to {round(low*2.5,2)} LPA – ₹ {round(high*2.3,2)} LPA*"
                )
            else:
                st.success(
                    f"Suggested hike: **{result['hike']}**  \n"
                    f"Expected Roles: BA and DS \n%" 
                )
        except ValidationError as ve:
            st.error("Invalid input: " + ve.errors()[0]["msg"])
