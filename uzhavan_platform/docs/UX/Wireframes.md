# UZHAVAN AI — Wireframes

**Device:** Redmi 10, 6.5" screen, 2400×1080px, ~405 ppi
**Design unit:** dp (density-independent pixels)
**Canvas width reference:** ~393dp (standard Flutter logical width)
**Min touch target:** 48×48 dp
**Min body font:** 16sp

All wireframes are 393dp wide × 852dp tall (standard mobile canvas).

---

## Screen 1 — Splash / Loading

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│                                     │
│           🌾                        │
│        [wheat stalk icon]           │
│           80×80 dp                  │
│                                     │
│         உழவன் AI                   │
│    [24sp, Noto Sans Tamil Bold]     │
│                                     │
│    Tamil Nadu Farmers' AI Guide     │
│    [14sp, Roboto, grey #757575]     │
│                                     │
│                                     │
│    ━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│    [linear progress, green #2E7D32] │
│                                     │
│                                     │
│                                     │
└─────────────────────────────────────┘
```
**Notes:**
- Full-screen green (#2E7D32) background with white elements in production
- Progress bar animates while JWT token is validated
- Auto-navigates: token valid → Home; no token → Phone Input

---

## Screen 2 — Phone Input (OTP Request)

```
┌─────────────────────────────────────┐
│  ←                                  │  ← back (hidden on first screen)
├─────────────────────────────────────┤
│                                     │
│  🌾 உழவன் AI                       │
│  [20sp Tamil Bold, top-left]        │
│                                     │
│  உங்கள் மொபைல் எண்ணை              │
│  உள்ளிடுங்கள்                       │
│  [18sp Tamil, #212121]              │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🇮🇳 +91  │  98765 43210    │   │
│  │  flag+code │  10-digit input │   │
│  │  56dp tall  [16sp Roboto]   │   │
│  └─────────────────────────────┘   │
│  [#2E7D32 bottom border when focus]│
│                                     │
│  ┌─────────────────────────────┐   │
│  │      OTP அனுப்பு           │   │
│  │    [16sp Tamil Bold]        │   │
│  │    56dp tall, full-width    │   │
│  │    #2E7D32 green fill       │   │
│  └─────────────────────────────┘   │
│                                     │
│  உங்கள் தொலைபேசி எண்ணுக்கு       │
│  OTP அனுப்பப்படும்                 │
│  [12sp Tamil, grey #757575]         │
│                                     │
└─────────────────────────────────────┘
```
**Notes:**
- Country code +91 is prefilled and non-editable (India only in V0.3)
- Numeric keyboard auto-opens on field focus
- Button disabled until 10 digits entered (no validation error needed — button simply stays grey)
- Error state: "தவறான எண். மீண்டும் முயற்சிக்கவும்." [14sp, #D32F2F red] below field
- Rate limit state: "அதிக முயற்சிகள். 45 நிமிடம் பிறகு முயற்சிக்கவும்." [14sp amber]

---

## Screen 3 — OTP Verification

```
┌─────────────────────────────────────┐
│  ←                                  │
├─────────────────────────────────────┤
│                                     │
│  OTP உறுதிப்படுத்தல்               │
│  [20sp Tamil Bold]                  │
│                                     │
│  98765 43210 என்ற எண்ணுக்கு        │
│  OTP அனுப்பப்பட்டது                │
│  [16sp Tamil, #424242]              │
│                                     │
│  ┌────┐  ┌────┐  ┌────┐           │
│  │  3 │  │  _ │  │    │           │
│  └────┘  └────┘  └────┘           │
│  ┌────┐  ┌────┐  ┌────┐           │
│  │    │  │    │  │    │           │
│  └────┘  └────┘  └────┘           │
│  [6 boxes, 52×56dp each, 8dp gap]  │
│  [active box: green border 2dp]    │
│  [filled box: grey bg #F5F5F5]     │
│                                     │
│  ┌─────────────────────────────┐   │
│  │       உறுதிப்படுத்து       │   │
│  │    [disabled until 6 digits]│   │
│  └─────────────────────────────┘   │
│                                     │
│  OTP届 கிடைக்கவில்லையா?           │
│  மீண்டும் அனுப்பு (4:32)           │
│  [14sp, countdown timer, grey]     │
│  [becomes tappable green at 0:00]  │
│                                     │
└─────────────────────────────────────┘
```
**Notes:**
- Auto-advances cursor to next box after each digit
- Paste from SMS clipboard auto-fills all 6 boxes
- Wrong OTP: red border on all boxes + "தவறான OTP. மீண்டும் முயற்சிக்கவும்." [14sp red]
- Expired: "OTP காலாவதியாகிவிட்டது. மீண்டும் கோரவும்." + resend button highlighted immediately

---

## Screen 4 — Profile Setup

```
┌─────────────────────────────────────┐
│  ←      படி 1/2                    │
│         [linear progress bar 50%]   │
├─────────────────────────────────────┤
│                                     │
│  உங்களைப் பற்றி சொல்லுங்கள்       │
│  [20sp Tamil Bold]                  │
│                                     │
│  பெயர்                             │
│  [14sp Tamil, label, #616161]       │
│  ┌─────────────────────────────┐   │
│  │  முருகன்                   │   │
│  │  [16sp Noto Tamil]         │   │
│  │  [56dp tall input]         │   │
│  └─────────────────────────────┘   │
│                                     │
│  மாவட்டம்                          │
│  ┌─────────────────────────────┐   │
│  │  தஞ்சாவூர்           ▼    │   │
│  │  [dropdown, 56dp tall]     │   │
│  └─────────────────────────────┘   │
│                                     │
│  முதன்மை பயிர்                     │
│  ┌─────────────────────────────┐   │
│  │  நெல்                ▼    │   │
│  └─────────────────────────────┘   │
│                                     │
│  மொழி விருப்பம்                    │
│  ● தமிழ்    ○ English              │
│  [radio buttons, 48dp tap area]    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │        தொடரவும்            │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```
**Notes:**
- District dropdown: alphabetically sorted Tamil names, 38 districts
- Crop dropdown: 50 crops in Tamil, most common at top (நெல், வாழை, தக்காளி...)
- All labels in Tamil; no English required for this screen

---

## Screen 5 — Farm Setup

```
┌─────────────────────────────────────┐
│  ←      படி 2/2                    │
│         [linear progress bar 100%]  │
├─────────────────────────────────────┤
│                                     │
│  உங்கள் நிலம் பற்றி சொல்லுங்கள்  │
│  [20sp Tamil Bold]                  │
│                                     │
│  நிலத்தின் பெயர் (விருப்பமானது)    │
│  ┌─────────────────────────────┐   │
│  │  முதல் நிலம்               │   │
│  └─────────────────────────────┘   │
│                                     │
│  பரப்பளவு                          │
│  ┌──────────────┐  ┌───────────┐  │
│  │  1.8         │  │ ஹெக்டேர் ▼│  │
│  │  [numeric]   │  │ [unit sel]│  │
│  └──────────────┘  └───────────┘  │
│  [unit: ஏக்கர் / ஹெக்டேர்]        │
│                                     │
│  மண் வகை                           │
│  ┌─────────────────────────────┐   │
│  │  வண்டல் மண்           ▼   │   │
│  └─────────────────────────────┘   │
│                                     │
│  நீர்ப்பாசன முறை                   │
│  ┌─────────────────────────────┐   │
│  │  கால்வாய்             ▼   │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │        முடித்தது           │   │
│  └─────────────────────────────┘   │
│                                     │
│  இதை பின்னர் சேர்க்கலாம்          │
│  [14sp, tappable grey, skip option]│
└─────────────────────────────────────┘
```
**Notes:**
- Area unit toggle: ஏக்கர் / ஹெக்டேர் — converts value automatically
- Skip link: navigates to Home without farm — chat still works, weather uses district
- Soil type dropdown: 10 types from database, Tamil names
- Irrigation: கால்வாய், குழாய் கிணறு, மழை, தொட்டி, நிலத்தடி நீர்

---

## Screen 6 — Home Screen

```
┌─────────────────────────────────────┐
│  உழவன் AI              [profile👤] │
│  [20sp Tamil Bold, #2E7D32]         │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🌤 தஞ்சாவூர்              │   │ ← WeatherCard
│  │  32°C    மழை இல்லை        │   │
│  │                             │   │
│  │  நாளை: 🌧 18மிமீ மழை     │   │
│  │  ⚠️ இன்று நீர்ப்பாசனம்    │   │
│  │     தேவையில்லை             │   │
│  │              [#FFF8E1 bg]   │   │
│  └─────────────────────────────┘   │
│                                     │
│  இன்று என்ன செய்வது?               │ ← CTA header
│  [18sp Tamil Bold]                  │
│                                     │
│  ┌────────────┐  ┌────────────┐   │
│  │  💬         │  │  📷        │   │ ← Quick actions
│  │  கேள்வி    │  │  நோய்     │   │
│  │  கேளுங்கள் │  │  கண்டறி  │   │
│  │ [56dp tall] │  │ [56dp tall]│   │
│  └────────────┘  └────────────┘   │
│                                     │
│  சமீபத்திய உரையாடல்கள்             │
│  [16sp Tamil Bold, #424242]         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🌾 நெல் இலை மஞ்சள்...    │   │
│  │  நேற்று · 3 செய்திகள்     │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  🌧 நீர்ப்பாசனம் கேள்வி... │   │
│  │  2 நாட்கள் முன்பு          │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│  🏠 Home │ 💬 Chat │ 📷 │ 📋 History │ 👤 │
│  [48dp tab bar, active tab green]   │
└─────────────────────────────────────┘
```
**Notes:**
- WeatherCard tappable → Weather Detail screen
- Quick action buttons: 156dp wide each, 8dp gap, 56dp tall
- Recent conversations: max 2 shown, "மேலும் பார்க்க" link → History tab
- If no conversations yet: "உங்கள் முதல் கேள்வி கேளுங்கள்!" with arrow to chat button

---

## Screen 7 — Chat Screen

```
┌─────────────────────────────────────┐
│  ←  உழவன் AI         [Tamil|Eng]  │
├─────────────────────────────────────┤
│                                     │
│  [messages scroll area]             │
│                                     │
│              ┌─────────────────┐   │
│              │ நெல் இலைகள்    │   │ ← User bubble
│              │ மஞ்சளாக        │   │   right-aligned
│              │ மாறுகின்றன     │   │   #2E7D32 bg
│              │ என்ன செய்வது?  │   │   white text
│              │         14:32  │   │
│              └─────────────────┘   │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ [UZHAVAN] 🌾 advisory        │ │ ← AI bubble
│  │                               │ │   left-aligned
│  │ நைட்ரஜன் பற்றாக்குறையே      │ │   white bg
│  │ முக்கிய காரணம். TNAU         │ │   grey border
│  │ பரிந்துரைப்படி 25 கிலோ      │ │
│  │ யூரியா/ஏக்கர் தெளிக்கவும். │ │
│  │                               │ │
│  │ ┌───────────────────────────┐ │ │ ← Source card
│  │ │ 🟢 TNAU நெல் சாகுபடி    │ │ │
│  │ │    கையேடு               │ │ │
│  │ │    87% நம்பகத்தன்மை      │ │ │
│  │ │    agritech.tnau.ac.in ↗ │ │ │
│  │ └───────────────────────────┘ │ │
│  │                               │ │
│  │ ❓ அடுத்து கேளுங்கள்:        │ │ ← Suggestion chips
│  │ [யூரியா அளவு?] [எப்போது?]   │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌── Streaming AI message ────────┐ │
│  │ [UZHAVAN]                      │ │ ← Streaming bubble
│  │ மழைக்கு பிறகு தெளிக்கவும்▌   │ │   cursor blinks
│  └────────────────────────────────┘ │
│                                     │
├─────────────────────────────────────┤
│  ┌─────────────────────────┐ [📷][➤]│
│  │ உங்கள் கேள்வி...       │       │ ← Input bar
│  │ [16sp Tamil, 56dp tall] │       │   ➤ = 48×48dp
│  └─────────────────────────┘       │
└─────────────────────────────────────┘
```
**Notes:**
- Intent chip on AI messages: 🌾 advisory / 🌦 weather / 🔬 disease / 📋 scheme
- Source card: confidence dot 🟢≥0.70 / 🟡0.50-0.69 / 🟠0.35-0.49; entire card tappable
- Suggestion chips: horizontal scroll if > 2 chips; min 48dp height
- Camera icon in input bar → goes to Camera screen (disease detection)
- Streaming: text appends character by character; auto-scroll unless user scrolled up
- No-answer state: grey icon + "மன்னிக்கவும், பதில் கிடைக்கவில்லை. BAO-ஐ தொடர்பு கொள்ளுங்கள்."

---

## Screen 8 — Chat History

```
┌─────────────────────────────────────┐
│  ←  உரையாடல் வரலாறு               │
├─────────────────────────────────────┤
│                                     │
│  இன்று                             │
│  [14sp Tamil Bold, #757575]         │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🌾 நெல் இலை மஞ்சள்...    │   │ ← Session card
│  │  இன்று 14:32 · 3 செய்திகள்│   │   72dp tall
│  └─────────────────────────────┘   │
│                                     │
│  நேற்று                            │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🌧 நீர்ப்பாசன ஆலோசனை     │   │
│  │  நேற்று 09:15 · 5 செய்திகள்│   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  🔬 வாழை இலைப்புள்ளி...   │   │
│  │  நேற்று 07:41 · 2 செய்திகள்│   │
│  └─────────────────────────────┘   │
│                                     │
│  இந்த வாரம்                        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  📋 PM-KISAN பயன்...       │   │
│  │  திங்கள் 11:20 · 4 செய்திகள்   │
│  └─────────────────────────────┘   │
│                                     │
│  [scroll for more]                  │
│                                     │
│  [empty state if no history:]       │
│  🌱 இன்னும் உரையாடல் இல்லை       │
│  கீழே உள்ள கேள்வி பொத்தானை       │
│  தட்டுங்கள்                        │
└─────────────────────────────────────┘
```
**Notes:**
- Session cards: icon reflects dominant intent (🌾 advisory, 🌧 weather, 🔬 disease, 📋 scheme)
- Date grouping: இன்று, நேற்று, இந்த வாரம், முந்தைய
- Tap → ChatSession screen showing full message thread

---

## Screen 9 — Disease Camera Screen

```
┌─────────────────────────────────────┐
│  ✕                                  │ ← close button, 48×48dp
│  [white on black/camera preview]    │
│                                     │
│                                     │
│  ┌───────────────────────────────┐ │
│  │                               │ │ ← Camera viewfinder
│  │                               │ │   fills most of screen
│  │    [live camera preview]      │ │
│  │                               │ │
│  │     ┌─────────────┐          │ │ ← Focus guide frame
│  │     │             │          │ │   dashed green rectangle
│  │     │  leaf here  │          │ │
│  │     │             │          │ │
│  │     └─────────────┘          │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  இலையை சதுரத்தில் வையுங்கள்       │
│  [14sp Tamil white, centre]         │
│                                     │
│         ┌──────────────┐           │
│         │      📷      │           │ ← Capture button
│         │   [80dp dia] │           │   white circle, green icon
│         └──────────────┘           │
│                                     │
│  [gallery] [flash toggle]           │ ← 48×48dp each
└─────────────────────────────────────┘
```
**Notes:**
- Full-screen camera — no bottom nav visible
- Focus guide: animated green dashed rectangle, helps farmer centre the leaf
- Gallery button: allows uploading existing photo (for Lakshmi who may have already photographed)
- Flash: auto by default; toggle to on/off
- After capture: brief white flash, then immediately transitions to Analyzing screen

---

## Screen 10 — Disease Analyzing Screen

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│      [circular progress ring]       │
│         #2E7D32 green, 80dp         │
│         animating, 72%              │
│                                     │
│     பகுப்பாய்வு செய்கிறோம்...      │
│     [18sp Tamil Bold, white/#212121]│
│                                     │
│     சில நொடிகள் காத்திருங்கள்       │
│     [14sp Tamil, grey]              │
│                                     │
│     ─────────────────────────       │
│                                     │
│     🌾 TNAU வேளாண் ஆலோசனை:        │
│                                     │
│     "நோய் கண்டறிவதில் 70%-க்கும்  │ ← Rotating Tamil farming tip
│      அதிகமான நேரங்களில் ஆரம்ப     │   changes every 3 seconds
│      கண்டறிதலே சிறந்தது."          │
│                                     │
│     [thumbnail of captured image]   │ ← Small preview, 80×80dp
│     [bottom-right corner]           │
│                                     │
│                                     │
└─────────────────────────────────────┘
```
**Notes:**
- Image thumbnail confirms the right photo was captured
- Rotating tips from TNAU in Tamil (5 pre-loaded tips, no network required for tips)
- If analysis takes > 8 seconds: add "கொஞ்சம் நேரம் ஆகும்..." below progress
- On network error: "இணைப்பு இல்லை. Wi-Fi அல்லது மொபைல் டேட்டா இயக்கவும்." + retry button

---

## Screen 11 — Disease Result Screen

```
┌─────────────────────────────────────┐
│  ←  நோய் கண்டறிதல்                │
├─────────────────────────────────────┤
│                                     │
│  [captured leaf thumbnail, 120dp]   │
│                                     │
│  தக்காளி ஆரம்ப கருகல் நோய்        │ ← Disease name Tamil
│  [20sp Tamil Bold, #212121]         │   24sp, prominent
│  Tomato Early Blight                │ ← English secondary
│  [14sp Roboto, grey]                │
│                                     │
│  ┌──────────┐  ┌──────────────┐    │
│  │ 🔴 அதிகம்│  │ 87% நம்பகம் │    │ ← Severity + confidence
│  │ [chip]   │  │ [chip]       │    │   48dp tall each
│  └──────────┘  └──────────────┘    │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  ▼ அரசு பரிந்துரை (TNAU)          │ ← Accordion 1: Chemical
│  [16sp Tamil Bold, expanded]        │
│                                     │
│    மாங்கோஸேப் 75 WP @ 2.5 g/L     │
│    தண்ணீர் கலந்து தெளிக்கவும்      │
│    [16sp Tamil]                     │
│                                     │
│  ▶ இயற்கை முறை                    │ ← Accordion 2: Biological
│  [collapsed, tap to expand]         │
│                                     │
│  ▶ பண்ணை முறை                     │ ← Accordion 3: Cultural
│                                     │
│  ┌─────────────────────────────┐   │
│  │  🟢 TNAU Plant Protection  │   │ ← Source card
│  │     Manual — Ch. 4         │   │
│  │     agritech.tnau.ac.in ↗  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   AI-யிடம் மேலும் கேளுங்கள் │   │ ← Secondary CTA → Chat
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```
**Notes:**
- Severity chip colors: 🔴 Very High (#D32F2F), 🟠 High (#E64A19), 🟡 Medium (#F57C00), 🟢 None (#388E3C)
- If confidence < 40%: no severity chip; show "நிச்சயமில்லை — வேளாண் அலுவலரிடம் காட்டுங்கள்" in amber
- Accordion: chemical treatment expanded by default; others collapsed (most farmers want chemical first)
- Source card: tappable → opens TNAU page in browser

---

## Screen 12 — Settings Screen

```
┌─────────────────────────────────────┐
│  ←  அமைப்புகள்                    │
├─────────────────────────────────────┤
│                                     │
│  [profile avatar initials, 64dp]    │
│  முருகன்                           │
│  +91 98765 43210                    │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  மொழி                              │
│  ● தமிழ்    ○ English              │
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  என் நிலம்                         │
│  ┌─────────────────────────────┐   │
│  │ முதல் நிலம்         ✏️    │   │ ← Edit farm
│  │ 1.8 ஹெக்., வண்டல், கால்வாய்│   │
│  └─────────────────────────────┘   │
│  [+ நிலம் சேர்க்கவும்]             │ ← Add farm (max 3)
│                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                     │
│  பதிப்பு: v0.3.0                   │
│  உழவன் AI © 2026                   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    வெளியேறு                │   │ ← Logout, #D32F2F text
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```
**Notes:**
- Language toggle immediately updates all app text (no app restart)
- Farm list limited to 3 in V0.3
- Logout: confirmation dialog in Tamil before clearing token
