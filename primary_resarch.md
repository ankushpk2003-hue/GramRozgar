

# Primary Research & Competitor Gap Analysis

## 1. Overview
This document outlines the primary research conducted for **GramRozgar** (SIH26091). It evaluates existing government platforms, identifies critical functional and accessibility gaps, and demonstrates why a hyper-local, voice-assisted decision support system is necessary for rural micro-entrepreneurs.

---

## 2. Competitive Landscape: Existing Platforms


![alt text](image.png)




| Feature / Metric | JanSamarth Portal | MUDRA / Udyam Portal | GramRozgar (Our Solution) |
| :--- | :--- | :--- | :--- |
| **Primary Focus** | Loan application & scheme discovery aggregator | Micro-enterprise registration & loan discovery | Business viability assessment & financial decision support |
| **Market Intelligence** | None (Assumes applicant knows business demand) | None | **5–10 km radius scan** using Panchayat GIS & ISRO Bhuvan data |
| **Financial Engine** | Static forms / Standard bank calculations | Static forms | **Deterministic Python Engine** (isolated math, no AI hallucinations) |
| **User Interface** | Web forms (Requires high digital literacy) | Desktop/Mobile portal | **BHASHINI Voice AI & IVR** (Works in regional dialects on feature phones) |
| **Core Value Proposition** | "Can I get a loan?" | "How do I register?" | **"Should I take this loan?"** |

---

## 3. Key Gaps in Existing Platforms

### Gap 1: Administrative Gateway vs. Feasibility Advisor
* **Current State:** Portals like JanSamarth focus heavily on processing paperwork and connecting borrowers to banks.
* **Problem:** They do not evaluate whether a micro-enterprise (e.g., a poultry farm or retail store) is viable in that specific village.
* **Our Solution:** GramRozgar conducts hyper-local demand scans before an applicant takes on debt.

### Gap 2: High Digital & Language Barriers
* **Current State:** Existing portals require smartphones/desktops, PDF document uploads, and navigation through complex English/Hindi forms.
* **Problem:** Rural micro-entrepreneurs and first-time borrowers often face digital literacy challenges.
* **Our Solution:** A voice-first IVR flow using BHASHINI speech-to-text, allowing users to interact in their native dialects using basic feature phones.

### Gap 3: Lack of Financial Transparency & Guidance
* **Current State:** Existing calculators provide raw interest rates without explaining margin money requirements, subsidy lock-in periods, or real repayment burdens.
* **Problem:** Uninformed borrowing leads to high NPA (Non-Performing Asset) risks and financial distress.
* **Our Solution:** Deterministic rule engines that compute exact subsidy breakdowns (e.g., PMEGP 15%–35% margin money) and present clear repayment roadmaps.

---

## 4. Benchmark Scheme Implementation
For our prototype, we selected the **Prime Minister’s Employment Generation Programme (PMEGP)** as the baseline model. 

* **Structured Data:** The complete rule set, eligibility matrix, document list, and subsidy structures have been serialized into JSON format (`data/schemes/pmegp_scheme.json`).
* **Deterministic Logic:** The calculations follow strict percentage matrices based on rural/urban locations and special categories (SC/ST/OBC/Women) to prevent AI math errors.

---

## 5. References
* **JanSamarth National Portal:** [https://www.jansamarth.in](https://www.jansamarth.in)
* **KVIC PMEGP Portal:** [https://www.kviconline.gov.in/pmegpeportal](https://www.kviconline.gov.in/pmegpeportal)
* **MUDRA Scheme Details:** [https://www.mudra.org.in](https://www.mudra.org.in)

## 6. Why GramRozgar Works: Core Value Validation

### A. Technical Viability: Zero Math Hallucinations
* **The Problem:** Generative AI models (LLMs) frequently hallucinate numbers, making them unreliable for calculating loan interest, debt-to-income ratios, or project margins[cite: 1].
* **Why GramRozgar Works:** GramRozgar separates LLM reasoning from financial calculations[cite: 1]. The LLM (Gemini) handles natural language understanding and user intent, while a deterministic Python rule engine executes all financial math using exact government scheme formulas[cite: 1].

### B. Ground-Level Feasibility: Hyper-Local GIS Data vs. Guesswork
* **The Problem:** Current platforms approve loans based solely on credit score or document validity, leading to high default rates when local market demand is insufficient[cite: 1].
* **Why GramRozgar Works:** By integrating ISRO Bhuvan, Panchayat GIS boundaries, and market data within a 5–10 km radius, the platform assesses existing competition and consumer density before an entrepreneur takes debt[cite: 1].

### C. Inclusivity: Feature Phone & Dialect Accessibility
* **The Problem:** Over 50% of rural micro-entrepreneurs do not use smartphones or high-speed internet, locking them out of web-based portals like JanSamarth[cite: 1].
* **Why GramRozgar Works:** Using a BHASHINI-powered ASR/TTS voice pipeline integrated with IVR, users can interact via standard voice calls in local dialects without needing a smartphone or desktop interface[cite: 1].

### D. Governance & Risk Mitigation for Lenders
* **The Problem:** Banks face high Non-Performing Asset (NPA) risks in rural lending due to poor project vetting.
* **Why GramRozgar Works:** The two-step Panchayat verification layer combined with evidence-backed feasibility checks gives financial institutions higher confidence during loan appraisal[cite: 1].