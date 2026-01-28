# SafeNest AI  
## Intelligent Onboarding Questionnaire  
**Structured Data Collection for Core Intelligence Functions**

---

## 0. Design Philosophy

SafeNest AI onboarding is not a form — it is a **data intelligence layer**.

Each question is designed to:
- Improve AI defect detection accuracy
- Contextualize risk scoring
- Enable future prediction and explanation
- Reduce false positives and negatives
- Build long-term housing intelligence datasets

Questions are **progressive, adaptive, and role-aware**.

---

## 1. Universal Entry (All Users)

### Purpose
Establish user identity, intent, and session context.

### 1.1 User Role Selection
**Question:**   
are you ?

**Options:**
- Buyer / Renter
- Professional Inspector
- Builder / Developer
- Property Manager / Housing Authority
- Insurance Provider / Regulator

**Stored Fields:**
- user_type
- onboarding_version
- session_start_timestamp

---

### 1.2 Session Intent
**Question:**  
What is your primary goal today?

**Options:**
- Evaluate property safety
- Perform a professional inspection
- Monitor multiple properties
- Assess compliance or insurance risk

**Stored Fields:**
- session_intent

---

## 2. Property Context (All Users)

### Purpose
Ground AI analysis in the physical and environmental reality of the building.

---

### 2.1 Property Identification
**Questions:**
- Property type  
  - Apartment
  - Independent house
  - Villa
  - Under-construction project
  - Commercial property

- Ownership status  
  - Owned
  - Rented
  - Under evaluation

**Stored Fields:**
- property_type
- ownership_status

---

### 2.2 Construction & Age
**Questions:**
- Construction stage  
  - Planning
  - Under construction
  - Newly built
  - Occupied

- Building age  
  - < 1 year  
  - 1–5 years  
  - 5–15 years  
  - 15+ years

**Stored Fields:**
- construction_stage
- building_age_bucket

---

### 2.3 Location & Environment
**Questions:**
- City / Region
- Local environment (optional)
  - Coastal
  - Flood-prone
  - High humidity
  - Dry / arid

**Derived Fields:**
- climate_zone
- environmental_risk_profile

---

## 3. Buyer / Renter Questionnaire

### Purpose
Predict future maintenance, safety, and financial risk.

---

### 3.1 Decision Context
**Questions:**
- Are you buying or renting?
- Expected duration of stay  
  - < 1 year
  - 1–3 years
  - 3+ years

**Stored Fields:**
- transaction_type
- stay_duration

---

### 3.2 Occupant Profile
**Questions:**
Who will occupy the property? (Multiple allowed)
- Children
- Elderly
- Persons with disabilities
- Single occupant
- Family

**Stored Fields:**
- occupant_profile

---

### 3.3 Risk Sensitivity
**Questions:**
- What matters most to you?
  - Safety
  - Maintenance cost
  - Long-term durability
  - Resale value

- Risk tolerance
  - Conservative
  - Balanced
  - Aggressive

**Stored Fields:**
- risk_priority_vector
- risk_tolerance

---

## 4. Professional Inspector Questionnaire

### Purpose
Calibrate AI confidence, workflow, and validation depth.

---

### 4.1 Professional Background
**Questions:**
- Certification level
- Years of experience
- Primary inspection scope
  - Pre-purchase
  - Pre-handover
  - Periodic maintenance
  - Compliance audit

**Stored Fields:**
- certification_level
- years_experience
- inspection_scope

---

### 4.2 Inspection Style
**Questions:**
- Preferred inspection method
  - Visual-only
  - Instrument-assisted
  - Compliance-focused

- Desired AI assistance level
  - Suggest-only
  - Auto-tag + review
  - Full automation with alerts

**Stored Fields:**
- inspection_method
- ai_assistance_level

---

## 5. Builder / Developer Questionnaire

### Purpose
Enable early defect prevention and trend forecasting.

---

### 5.1 Project Details
**Questions:**
- Project size
  - < 10 units
  - 10–50 units
  - 50+ units

- Current phase
  - Foundation
  - Structural
  - Finishing
  - Handover

**Stored Fields:**
- project_size_bucket
- project_phase

---

### 5.2 Business Priorities
**Questions:**
- Primary concern
  - Compliance
  - Cost control
  - Timeline adherence
  - Brand reputation

**Stored Fields:**
- builder_priority_vector

---

## 6. Property Manager / Housing Authority Questionnaire

### Purpose
Detect systemic risk across property portfolios.

---

### 6.1 Portfolio Overview
**Questions:**
- Portfolio size
- Asset age distribution
- Maintenance strategy
  - Reactive
  - Preventive
  - Predictive

**Stored Fields:**
- portfolio_size
- maintenance_strategy

---

### 6.2 Reporting Needs
**Questions:**
- Reporting frequency
  - Monthly
  - Quarterly
  - On-demand

**Stored Fields:**
- reporting_frequency

---

## 7. Insurance Provider / Regulator Questionnaire

### Purpose
Support standardized underwriting and compliance reporting.

---

### 7.1 Risk Policy
**Questions:**
- Coverage region
- Risk tolerance
  - Conservative
  - Standard
  - Aggressive

**Stored Fields:**
- coverage_region
- insurer_risk_tolerance

---

### 7.2 Output Requirements
**Questions:**
What outputs are required?
- Numeric risk score
- Risk explanation
- Evidence package
- Historical trend data

**Stored Fields:**
- required_output_formats

---

## 8. Data Augmentation & Document Uploads

### Purpose
Enhance AI accuracy and legal defensibility.

---

### 8.1 Optional Document Uploads
**Supported Documents:**
- Floor plans
- Blueprints
- Structural drawings
- Electrical & plumbing layouts
- Past inspection reports
- Completion certificates

**Stored Fields:**
- document_type
- document_version
- linked_property_id
- upload_timestamp

---

## 9. AI Readiness Summary (User-Facing)

### Purpose
Build trust and explain how AI will operate.

**System Output Example:**
> “SafeNest AI will prioritize electrical and moisture-related risks, apply conservative scoring, and flag low-confidence findings for human verification.”

---

## 10. Intelligence Outcomes Enabled

### Short-Term
- Higher detection accuracy
- Context-aware scoring
- Clear explanations

### Long-Term
- Region-specific defect prediction
- Climate-linked failure forecasting
- Portfolio-level risk intelligence
- Continuous AI improvement via feedback

---

## 11. Data Governance & Ethics

- Minimal data collection
- Role-based access control
- Consent-driven uploads
- Time-limited retention policies
- Full auditability of AI decisions

---

## 12. Closing Note

SafeNest AI onboarding is designed to **teach the system how to think before it analyzes**.  
This ensures safer decisions, explainable outcomes, and trustworthy intelligence at scale.
