# SafeNest AI  
## Product Requirements Document (PRD)

---

## 1. Product Overview

### Product Name
**SafeNest AI**

### Tagline
*See the invisible risks before you move in.*

### Product Type
AI-powered residential inspection intelligence platform  
(Web + Mobile: Android & iOS)

### Primary Platforms
- **Web:** Next.js (React)  
- **Mobile:** React Native  
- **Optional Web UI:** Vue (admin / analytics extensions)

### Backend & Intelligence
- **Snowflake** (single source of truth)
- **Snowflake Cortex AI (AI SQL)**
- **Snowpark (Python)**
- **External open datasets / pre-trained models (CV & structural analysis)**

---

## 2. Problem Statement

Residential safety inspections today are:
- Manual
- Subjective
- Non-predictive
- Poorly standardized

Photos, videos, documents, and notes exist — but **no intelligence layer connects them**.

This leads to:
- Unsafe housing decisions
- Surprise repair costs
- Legal disputes
- Poor regulatory visibility

---

## 3. Goals & Success Metrics

### Primary Goals
1. Automatically detect construction defects from images, video, and documents
2. Quantify safety risk (room-level & property-level)
3. Generate explainable, evidence-backed AI reports
4. Support both **quick inspections** and **deep professional inspections**
5. Scale securely across users, devices, and data volumes

### Success Metrics
- Defect detection precision > 85%
- Inspection time reduced by ≥ 5×
- User trust score (confidence + explanation clarity)
- System scalability (10k+ inspections/day)
- Zero critical security incidents

---

## 4. Target Users

- Buyers / Renters (B2C)
- Professional Inspectors (B2B)
- Builders & Developers (B2B)
- Property Managers (B2B)
- Insurance & Regulators (B2B / Gov)

---

## 5. Visual Identity & Design System

### Color Scheme (Antigravity Theme)
- **Primary:** Luminating deep blue (#0A1AFF range)
- **Secondary:** Matte black (#0B0B0B)
- **Accent:** Gold gradient edge lines
- **Highlight:** Neon yellow / cyan glow
- **UI Effects:** Subtle emissive gradients, rim lighting, soft bloom

### Design Language
- Premium futuristic SaaS
- High contrast, dark-first UI
- Cinematic transitions
- Minimal text, strong visual hierarchy

---

## 6. App Entry & Loading Experience

### Loading Animation (Looped)

**Purpose:** Establish trust, premium feel, and brand identity

**Specifications:**
- Aspect Ratio: 16:9
- Resolution: 4K
- FPS: 60
- Duration: 2.5s
- Loop: Seamless infinite
- Background: Transparent

**Visual Elements:**
- Rounded neon progress bar (bottom center)
- AI construction mascot running on progress bar
- Blue rim lighting, emissive reflections
- Pixar-level polish

**Constraints:**
- No visible loop cut
- No motion jitter
- Perfect alpha transparency
- Stable UI geometry


**PROMPT:**
{
  "video_settings": {
    "aspect_ratio": "16:9",
    "resolution": "4K",
    "fps": 60,
    "duration_seconds": 2.5,
    "loop": true,
    "background": "transparent"
  },

  "style": {
    "visual_tone": "premium futuristic SaaS UI",
    "lighting": "cinematic blue rim light",
    "render_quality": "pixar-level polish",
    "materials": [
      "glossy plastic",
      "soft metal",
      "neon emissive surfaces"
    ]
  },

  "start_frame": {
    "timestamp": "00:00:00",
    "scene_description": "A dark futuristic UI space with a transparent background. A rounded progress bar sits centered horizontally near the bottom of the frame. The bar is empty with matte black edges and a faint blue ambient glow beneath it. An AI construction mascot character enters from the left edge, already mid-run on top of the progress bar, holding a metallic spanner. The character’s legs are in the first phase of a looping sprint cycle, helmet slightly bobbing, subtle blue rim light outlining the body."
  },

  "animation_sequence": {
    "progress_bar": {
      "position": "bottom_center",
      "shape": "rounded_rectangle",
      "border_color": "matte_black",
      "fill_gradient": "neon_blue_to_cyan",
      "animation": {
        "type": "linear_fill",
        "from": 0,
        "to": 100,
        "effects": [
          "soft inner shimmer wave",
          "gentle glow pulse every 12 frames"
        ]
      }
    },

    "character": {
      "model": "cute professional AI construction robot",
      "motion": {
        "type": "looped_run_cycle",
        "speed": "consistent",
        "path": "left_to_right_aligned_with_progress",
        "secondary_motion": [
          "helmet_micro_bounce",
          "spanner_swing",
          "subtle body lean forward"
        ]
      },
      "lighting": {
        "rim_light": "electric_blue",
        "reflections": "progress_bar_emission"
      }
    }
  },

  "end_frame": {
    "timestamp": "00:00:02.5",
    "scene_description": "The scene visually matches the starting frame. The progress bar has smoothly completed its fill and softly reset back to empty without any jump cut. The blue glow intensity matches the start frame exactly. The AI mascot is again positioned entering from the left edge in the same running pose and animation phase as the first frame, holding the spanner with identical limb positions, lighting, and motion state, ensuring a seamless infinite loop."
  },

  "loop_constraints": {
    "match_start_end_pose": true,
    "match_lighting_state": true,
    "match_progress_bar_state": true,
    "no_visible_cut": true,
    "no_motion_jitter": true
  },

  "quality_controls": [
    "subpixel motion accuracy",
    "cinematic easing",
    "no ghosting",
    "no edge artifacts",
    "perfect alpha transparency",
    "stable UI geometry"
  ]
}
 charcter - @CH.png

---

## 7. Core User Flow

### 7.1 App Launch
1. Loading animation
2. Transition into onboarding

---

## 8. Onboarding Flow (Core Intelligence Setup)

### Step 1 – User Role Selection
(from onboarding questionnaire)

- Buyer / Renter
- Inspector
- Builder / Developer
- Property Manager
- Insurance / Regulator

### Step 2 – Session Intent
- Quick safety check
- Full inspection
- Compliance / reporting
- Portfolio monitoring

> These two steps are **mandatory** and gate all logic.

---

## 9. Scan Selection Screen

### Screen: **Inspection Mode Selection**

Two primary CTAs:

#### Option A — Quick Scan
**For fast, surface-level analysis**

#### Option B — Deep Scan
**For full intelligence & prediction**

Smooth animated transition with mascot guide pointing options.

---

## 10. Quick Scan Requirements

### Camera & Media Input
- Live camera capture (photo or video)
- Record video inspection
- Upload media:
  - Images up to **10 MB**
  - Videos up to **100 MB**

### Supported Inputs
- JPG / PNG
- MP4 / MOV
- Multiple files per session

### AI Behavior
- Fast defect detection
- Conservative scoring
- Limited prediction
- No extended questionnaires

### Output
- Instant risk score
- Highlighted defects
- Short explanation

---

## 11. Deep Scan Requirements

### Questionnaire Continuation
- Resume onboarding questionnaire where left off
- Ask:
  - Property context
  - Usage & occupancy
  - Risk tolerance
  - Environmental factors

### Document Upload (Mandatory)
- Floor plans
- Blueprints
- Electrical layouts
- Structural drawings
- Previous inspection reports
- Certificates & permits

### AI Camera Scan
- Guided capture per room
- Overlay hints (future AR)
- Required angles & coverage

### AI Behavior
- Multi-modal fusion (image + text + docs)
- Structural integrity inference
- Lifespan & degradation prediction
- Confidence-aware risk modeling

---

## 12. AI Analysis & Intelligence Engine

### AI Stack

#### Snowflake Cortex AI
- Image classification (crack, damp, wiring, corrosion)
- Text entity extraction
- Captioning & bounding boxes
- AI SQL execution

#### Snowpark (Python)
- Risk aggregation logic
- Bayesian / weighted scoring
- Time-to-failure modeling

#### External Models (Free / Open)
- Structural crack classification models
- Moisture & mold detection datasets
- Civil engineering degradation datasets

All outputs are **stored and versioned in Snowflake**.

---

## 13. Risk Scoring System

### Room-Level Score
defect_severity × confidence × room_importance × environment_factor

### Property-Level Score
- Max-risk bias OR
- Weighted average (configurable)

### Output
- Score (0–100)
- Risk category
- Explanation
- Evidence references

---

## 14. Dashboard Requirements

### Design
- Dark premium UI
- Interactive cards
- Smooth scroll-based transitions
- Button-triggered animated navigation

### Features
- Risk score visualization
- Defect heatmaps
- Evidence gallery
- Confidence indicators
- Mascot guide for actions

---

## 15. Backend & Data Architecture

### Core Storage
- Snowflake (structured + unstructured)
- External stages (S3 / GCS / Azure)

### Pipelines
- Snowpipe (ingestion)
- Dynamic Tables (AI enrichment)
- Streams & Tasks (CDC where needed)

### Security
- RBAC
- Row-level security
- Column masking
- Encrypted media access
- Audit logs

---

## 16. Scalability Requirements

- Stateless frontend
- Horizontally scalable APIs
- Async AI processing
- Batch inference support
- Multi-region Snowflake readiness

---

## 17. Sensor & IoT (Phase 2+)

### Supported Sensors
- Moisture
- Temperature / humidity
- Vibration
- Electrical load

### Integration
- Mobile gateway
- Secure API ingest
- Correlation with inspection data

---

## 18. Non-Functional Requirements

- App response < 200ms for UI
- AI result latency:
  - Quick Scan: < 30s
  - Deep Scan: < 2–5 min
- 99.9% uptime
- Offline-first mobile capture

---

## 19. Risks & Mitigation

| Risk | Mitigation |
|----|----|
| AI false positives | Confidence + human review |
| High AI cost | Batch + caching |
| Data privacy | Consent & masking |
| Sensor noise | Cross-validation |

---

## 20. Final Product Positioning

SafeNest AI is not an inspection app.  
It is a **residential safety intelligence system** that combines AI, data, sensors, and human expertise to predict risk — not just report defects.

---

## 21. One-Line Summary

**“SafeNest AI turns inspection data into trusted, explainable, and predictive safety decisions — across web, mobile, and scale.”**
