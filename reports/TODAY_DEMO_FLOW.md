# UZHAVAN AI — Executive Demo Script & Presentation Flow

**Date:** 2026-09-26  
**Audience:** Technical Leadership, Stakeholders & Agricultural Domain Evaluators  
**App Target:** Uzhavan AI Android Client (Flutter 3.38 / Dart 3.10) running on Android 13 (Pixel 6)  
**Backend:** FastAPI Async Gateway (`:8000`), PostgreSQL 16, Redis 7  

---

## 1. Problem Statement

Smallholder farmers in Tamil Nadu face four critical information barriers:
1. **Fragmented Intelligence:** Weather forecasts, mandi prices, soil health records, and government welfare schemes reside in separate, non-mobile-friendly portals.
2. **Language & Literacy Gaps:** Official agricultural advisories are rarely presented in colloquial Tamil with localized agronomic context.
3. **Delayed Disease Diagnostics:** Crop fungal infections (such as Tikka leaf spot and Rust in groundnut) spread rapidly, often misidentified by farmers as nutrient stress until crop loss occurs.
4. **Lack of Truthful Safety Gates:** Consumer AI tools hallucinate remedies or present experimental computer vision models as infallible truth, leading farmers to purchase improper agrochemicals.

**Uzhavan AI** was built to solve these challenges with an honest, safety-first agricultural intelligence platform.

---

## 2. UZHAVAN AI Overview

**UZHAVAN AI** is an AI operating system tailored specifically for Tamil Nadu farmers.
- **Core Principles:**
  - **Zero Fabrication:** If an AI model is not independently validated on field data, the system honestly displays "Under Validation" rather than hallucinating answers.
  - **Bilingual by Design:** Complete, native toggle between Tamil (`தமிழ்`) and English across all UI elements, data sources, and voice prompts.
  - **Grounded Data:** Over 1,000,000 live AGMARKNET mandi records, 136 state/central schemes, and real Soil Health Card sample distributions.
  - **Modular Microservices:** Riverpod Flutter mobile client, FastAPI gateway with SSE streaming, and containerized ML pipelines.

---

## 3. Login & Authentication Flow

### Demo Steps:
1. Open the **Uzhavan AI** application on the Android device.
2. Observe the clean Sign-In screen with the top-right language switcher (`தமிழ் ↔ English`).
3. Enter a standard 10-digit Indian mobile number (e.g. `9876542222`).
4. Tap **"OTP அனுப்பு"** (Send OTP).
5. Point out the instant OTP transmission and security guardrail:
   - *Technical highlight:* Protected by Redis rate limiting with a 60-second cooldown per telephone number.
6. Enter the 6-digit OTP received from the verification channel (`978932`).
7. Tap **"Verify"**.
8. If this is a first-time user, the onboarding screen prompts for **Farmer Name**, **District** (dropdown of all 38 Tamil Nadu districts), and **Preferred Language**.
9. Tap **"Continue"**. The session is securely persisted via encrypted JWT tokens.

---

## 4. Home Dashboard

### Demo Steps:
1. Upon login, the user lands on the **Home Dashboard**.
2. **Current Weather Snapshot:**
   - Shows today's weather for the farmer's registered district (e.g. *Ariyalur: Overcast, Max 36.2 °C, Min 26.2 °C, Rain 0 mm, 10% Chance*).
   - Displays clear source attribution: *Open-Meteo numerical model*.
3. **Latest Observed Mandi Prices Ticker:**
   - Displays live cards for key crops in the farmer's local Uzhavar Sandhai / Regulated Market:
     - **Onion (Bellary):** ₹6,250 / quintal
     - **Coconut:** ₹6,250 / quintal
     - **Tomato (Deshi):** ₹3,300 / quintal
4. **Bottom Navigation Bar:**
   - Intuitive 5-tab layout: **Home**, **Assistant**, **Scan**, **Market**, **More**.

---

## 5. Weather Intelligence

### Demo Steps:
1. Tap the Weather Card on Home or navigate to **More → Weather**.
2. **Current Conditions:**
   - Displays real-time temperature (`33.1 °C`), "Feels like" index (`35.7 °C`), humidity (`45%`), wind speed (`17.4 km/h`), and precipitation.
3. **7-Day Agronomic Forecast:**
   - Scroll through daily forecasts with weather condition icons (Thunderstorm, Light drizzle, Overcast).
   - Highlights rainfall probability and expected millimeter volume, critical for irrigation planning.
4. **Data Integrity Note:**
   - Clear banner stating that data is derived from Open-Meteo numerical weather simulations, recommending district administration alerts for severe weather.

---

## 6. Market Prices (Mandi Intelligence)

### Demo Steps:
1. Tap the **Market** tab on the bottom navigation bar.
2. **Interactive 90-Day Trend Chart:**
   - Tap any commodity (e.g., **Coconut** or **Groundnut**).
   - An interactive time-series chart renders 90 days of modal prices recorded at the local market (e.g., *Ariyalur Uzhavar Sandhai*).
   - Visual trend line shows price volatility between ₹5,000 and ₹7,000/quintal.
3. **Filtering & Search:**
   - Switch between commodity chips (*Banana, Black gram, Brinjal, Cotton, Groundnut, Paddy, Sugarcane*).
   - Change district to view neighbouring APMC mandis.
4. **Transparency Guardrail:**
   - Explicit disclaimer: *"Prices are past observations. UZHAVAN gives no price forecast or speculative selling advice."*

---

## 7. Government Schemes Catalog

### Demo Steps:
1. Navigate to **More → Government schemes**.
2. **Comprehensive Repository:**
   - 136 active welfare programs loaded directly from PostgreSQL.
3. **Categorization:**
   - Filter by **All**, **Central**, or **State** schemes.
   - Filter by target crop using the crop selector.
4. **Scheme Cards:**
   - Highlight major programs:
     - *Agriculture Infrastructure Fund (AIF)* — 3% interest subvention for post-harvest management.
     - *Kisan Credit Card (KCC)* — Concessional institutional credit.
     - *Mission for Integrated Development of Horticulture (MIDH)*.
     - *National Agriculture Market (e-NAM)*.
   - Tapping a scheme reveals department contacts, subsidy percentages, and eligibility criteria.

---

## 8. Soil Intelligence & Health Cards

### Demo Steps:
1. Navigate to **More → Soil**.
2. **Regional Soil Taxonomy:**
   - Displays verified soil types for the district (e.g. *Red Loamy, Alluvium* in Ariyalur) grounded in Tamil Nadu Agriculture Department (*Tamil Mannvalam*) records.
3. **District Nutrient Status (SHC Data):**
   - Displays actual Soil Health Card RKVY cycle data across 100 sample benchmarks:
     - **Nitrogen (N):** Low (100% of samples) $\rightarrow$ Demonstrates urgent need for green manuring.
     - **Phosphorus (P):** Medium (100% of samples).
     - **Potassium (K):** Medium (99%), Low (1%).
     - **Organic Carbon (OC):** Low (99%).
     - **pH & Salinity:** Neutral 42%, Alkaline 58%; NonSaline 100%.

---

## 9. Satellite Crop Monitoring

### Demo Steps:
1. Navigate to **More → Satellite**.
2. **Demonstrate Safety-First Architecture:**
   - Screen renders **"Satellite intelligence under validation"**.
   - Transparently details the 4 required production gates:
     - ❌ *Data licence: Not passed yet*
     - ❌ *Units verified: Not passed yet*
     - ℹ️ *Geographic scope: Cauvery Delta only*
     - ℹ️ *Independent evaluation: baseline only (val, 14 plots)*
   - Explain to stakeholders: *Uzhavan AI refuses to display unvalidated vegetation indices (NDVI) that could mislead crop insurance claims.*

---

## 10. Crop Disease Intelligence (M4)

### Demo Steps:
1. Tap the **Scan** tab in the center of the bottom navigation bar.
2. Select target crop: **Groundnut**.
   - Note the helpful guardrail: *"Paddy scanning is not offered yet"*.
3. Tap **"Take photo"** or **"From gallery"** to pick a crop leaf image.
4. Preview the leaf thumbnail on screen.
5. Tap **"Scan leaf"** (Upload).
6. **Observation:**
   - The backend validates image type, dimensions, and size ($<10$ MB).
   - The scan event is automatically logged into the farmer's diary.
   - The UI displays an honest **"Validated disease model unavailable"** status with advice to contact the local agricultural extension officer.
   - Emphasize to evaluators: *Rather than emitting an unreliable prediction, the system strictly halts until M4 v2 validation passes.*

---

## 11. Farmer Field Diary

### Demo Steps:
1. Navigate to **More → Farm diary**.
2. Observe the automatic audit log created from the previous disease scan (`kind: scan, "scan submitted"`).
3. Tap **"+ Add entry"**.
4. Select category: **Note** (or Observation / Expense / Income).
5. Type an entry: *"Applied bio-fertilizer to groundnut crop"*.
6. Tap **"Save"**.
7. Observe immediate persistence to the PostgreSQL database and dynamic UI rendering with date stamp (`2026-09-26`).

---

## 12. System Architecture

Present the technical architecture diagram to the audience:

```
┌────────────────────────────────────────────────────────┐
│                   Flutter Client                       │
│    (Riverpod, Offline State, Bilingual TA/EN, Audio)   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON / SSE (10.0.2.2:8000)
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Gateway                       │
│  - JWT Auth & Rate Limiter   - Envelope Serializer     │
│  - Weather Aggregator        - Market AGMARKNET Engine │
│  - Safety Gate Interceptor   - Diary Event Dispatcher  │
└─────────────┬─────────────┬─────────────┬──────────────┘
              │             │             │
    ┌─────────▼──┐   ┌──────▼─────┐   ┌───▼──────────────┐
    │ PostgreSQL │   │   Redis    │   │  Open-Meteo API  │
    │  (20 Rel)  │   │ Rate-Limit │   │ (Live Numerical) │
    └────────────┘   │   Cache    │   └──────────────────┘
                     └────────────┘
```

---

## 13. Current M4 Validation Status

Explain the results of the M4 v1 audit conducted today:
- **Baseline Model:** MobileNetV4 Conv-Small trained on 29,160 multi-crop images.
- **In-Domain Validation Accuracy:** $98.7\%$.
- **External Field Cross-Source Evaluation (West Bengal, $N=1,695$):**
  - Fungal Rust Recall: **$72.50\%$**
  - Tikka Leaf Spot Coarse Accuracy: **$96.76\%$**
  - Healthy Leaf Recall: **$0.0017$** (1 out of 600)
- **Root Cause Identified:**
  - 85.3% of external healthy leaves co-locate with "Nutrient Deficiency" in embedding space because VIT-C training data segregated chlorotic leaves into nutrient deficiency, starving the healthy class to only 6.77% of training samples.
  - The model did not fail on biology; it failed on an incompatible taxonomy definition.

---

## 14. Future M4 v2 Roadmap

Outline the exact pre-training fixes engineered today for M4 v2:
1. **Consolidated 3-Class Taxonomy (Option D):**
   - Merge `nutrient_deficiency` into `healthy` (1,948 balanced training images).
   - Merge `early_leaf_spot` and `late_leaf_spot` into `tikka_leaf_spot` (1,560 balanced training images).
   - Retain `rust` (702 training images).
2. **Calibrated Out-of-Distribution Rejection:**
   - Threshold $\tau = 0.70$ eliminates false alarms on unmodeled diseases (*Alternaria*, *Rosette*) with $68.8\%$ rejection and $0.1\%$ false rejection on true crops.
3. **Training Execution:**
   - Retraining will proceed in the dedicated v2 development area following stakeholder milestone approval.
