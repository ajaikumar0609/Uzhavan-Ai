"""
TNAU treatment guidance keyed to model label names from
linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
"""

GUIDANCE: dict[str, dict] = {
    # ─── APPLE ────────────────────────────────────────────────────────
    "Apple Scab": {
        "pathogen": "Venturia inaequalis (Fungal)",
        "symptoms": "Olive-green to black velvety spots on leaves and fruit; early defoliation.",
        "severity": "High",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Carbendazim 50 WP @ 1 g/L; Difenconazole 25 EC @ 0.5 mL/L — spray at green tip and petal fall stage.",
        "biological": "Bacillus subtilis-based biocontrol (Serenade); copper-based sprays in early season.",
        "cultural": "Remove and destroy fallen leaves; avoid overhead irrigation; use resistant varieties; dormant pruning for air circulation.",
    },
    "Apple With Black Rot": {
        "pathogen": "Botryosphaeria obtusa (Fungal)",
        "symptoms": "Purple to brown spots on leaves; fruit rot starting at calyx end; twig cankers.",
        "severity": "High",
        "chemical": "Captan 50 WP @ 2 g/L; Thiophanate-methyl 70 WP @ 1 g/L — spray at pink and petal-fall stage.",
        "biological": "Trichoderma harzianum application on pruning wounds.",
        "cultural": "Prune and destroy dead wood; remove mummified fruit; avoid wounding; keep orchard clean.",
    },
    "Cedar Apple Rust": {
        "pathogen": "Gymnosporangium juniperi-virginianae (Fungal)",
        "symptoms": "Orange-yellow spots on upper leaf surface; tube-like spore horns on lower surface.",
        "severity": "Medium",
        "chemical": "Myclobutanil 20 EW @ 0.5 mL/L; Propiconazole 25 EC @ 0.75 mL/L — preventive sprays from pink stage.",
        "biological": "Remove nearby cedar/juniper host plants (alternate host elimination).",
        "cultural": "Remove cedar or juniper trees within 300 m; use rust-resistant apple varieties.",
    },
    "Healthy Apple": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "Continue standard IPM practices.",
        "cultural": "Maintain balanced fertilization; prune annually; monitor for early signs.",
    },

    # ─── BLUEBERRY ────────────────────────────────────────────────────
    "Healthy Blueberry Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Maintain soil pH 4.5–5.5; adequate drainage; weed control.",
    },

    # ─── CHERRY ───────────────────────────────────────────────────────
    "Cherry With Powdery Mildew": {
        "pathogen": "Podosphaera clandestina (Fungal)",
        "symptoms": "White powdery growth on young leaves; distorted leaves; early defoliation.",
        "severity": "Medium",
        "chemical": "Wettable sulphur 80 WP @ 3 g/L; Triadimefon 25 WP @ 0.5 g/L — spray at bud burst and every 10 days.",
        "biological": "Potassium bicarbonate 5 g/L; neem oil 2% spray.",
        "cultural": "Prune for air circulation; avoid overhead irrigation; remove infected shoots; balanced nitrogen.",
    },
    "Healthy Cherry Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Maintain proper pruning; monitor for brown rot during wet periods.",
    },

    # ─── CORN / MAIZE ─────────────────────────────────────────────────
    "Corn (Maize) With Cercospora And Gray Leaf Spot": {
        "pathogen": "Cercospora zeae-maydis (Fungal)",
        "symptoms": "Rectangular tan to grey lesions with yellow borders running parallel to leaf veins.",
        "severity": "High",
        "chemical": "Propiconazole 25 EC @ 1 mL/L; Azoxystrobin 23 SC @ 1 mL/L — spray at 8-leaf stage if >5% leaf area affected.",
        "biological": "Bacillus subtilis-based product; crop rotation breaks disease cycle.",
        "cultural": "Resistant varieties (CO6 for TN); crop rotation; deep ploughing; avoid maize-on-maize; remove crop debris.",
    },
    "Corn (Maize) With Common Rust": {
        "pathogen": "Puccinia sorghi (Fungal)",
        "symptoms": "Small brick-red oval pustules scattered on both leaf surfaces; severe infection causes premature drying.",
        "severity": "Medium",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Propiconazole 25 EC @ 1 mL/L — spray at first appearance.",
        "biological": "No effective biocontrol available; crop rotation and resistant varieties preferred.",
        "cultural": "Grow resistant varieties; early sowing to avoid peak rust season; remove volunteer maize plants.",
    },
    "Corn (Maize) With Northern Leaf Blight": {
        "pathogen": "Exserohilum turcicum (Fungal)",
        "symptoms": "Large cigar-shaped grey-green to tan lesions 5–15 cm long on lower leaves; spreading upward.",
        "severity": "High",
        "chemical": "Tebuconazole 25.9 EC @ 1 mL/L; Azoxystrobin 23 SC @ 1 mL/L — spray when lesions first appear on lower leaves.",
        "biological": "Trichoderma viride seed treatment; resistant hybrids preferred.",
        "cultural": "Resistant varieties (check ICAR-IIMR recommendations); crop rotation; remove residue; avoid excessive nitrogen.",
    },
    "Healthy Corn (Maize) Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Maintain balanced NPK; monitor for Fall Armyworm (Spodoptera frugiperda) which is high-risk in TN.",
    },

    # ─── GRAPE ────────────────────────────────────────────────────────
    "Grape With Black Rot": {
        "pathogen": "Guignardia bidwellii (Fungal)",
        "symptoms": "Reddish-brown circular leaf spots with black pycnidia; shrivelled mummified fruit (black rot).",
        "severity": "Very High",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Myclobutanil 10 WP @ 0.5 g/L — apply at bud break, before and after bloom.",
        "biological": "Bacillus amyloliquefaciens product; copper-based fungicides pre-bloom.",
        "cultural": "Remove mummified berries and infected canes in winter; improve air circulation; control weeds; avoid wetting foliage.",
    },
    "Grape With Esca (Black Measles)": {
        "pathogen": "Phaeomoniella chlamydospora + Phaeoacremonium spp. (Fungal wood rot)",
        "symptoms": "Tiger-stripe leaf discolouration; premature defoliation; dark-brown streaking in wood when cut; fruit with dark speckling (black measles).",
        "severity": "Very High",
        "chemical": "No curative chemical; Fosetyl-aluminium 80 WP as protective treatment in vines at risk.",
        "biological": "Trichoderma harzianum wound treatment on pruning cuts.",
        "cultural": "Double-pruning technique; avoid large pruning wounds; seal wounds with wound paste; remove severely infected vines; avoid water stress.",
    },
    "Grape With Isariopsis Leaf Spot": {
        "pathogen": "Isariopsis clavispora / Pseudocercospora vitis (Fungal)",
        "symptoms": "Angular brown spots with grey-white centre on upper leaf surface; brownish mycelium on lower surface.",
        "severity": "Medium",
        "chemical": "Copper oxychloride 50 WP @ 3 g/L; Mancozeb 75 WP @ 2.5 g/L.",
        "biological": "Neem-based spray as preventive; copper fungicides compatible with IPM.",
        "cultural": "Remove infected leaves; improve air circulation; balanced potassium fertilization.",
    },
    "Healthy Grape Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Schedule preventive sprays against downy mildew and powdery mildew during monsoon.",
    },

    # ─── ORANGE ───────────────────────────────────────────────────────
    "Orange With Citrus Greening": {
        "pathogen": "Candidatus Liberibacter asiaticus — transmitted by Asian citrus psyllid (Bacterial/Vector)",
        "symptoms": "Asymmetric (blotchy) mottle yellowing; misshapen bitter fruit; starch accumulation; green fruit staying green at calyx end.",
        "severity": "Very High",
        "chemical": "Control vector: Imidacloprid 17.8 SL @ 0.5 mL/L or Dimethoate 30 EC @ 2 mL/L for psyllid. No curative chemical for the bacteria.",
        "biological": "Tamarixia radiata parasitoid of psyllid; release in young orchards.",
        "cultural": "Use certified disease-free nursery stock; rogue infected trees; control psyllid population; quarantine new plant material; nutritional sprays (Zn, Mn, Mg) for symptomatic trees.",
    },

    # ─── PEACH ────────────────────────────────────────────────────────
    "Peach With Bacterial Spot": {
        "pathogen": "Xanthomonas arboricola pv. pruni (Bacterial)",
        "symptoms": "Water-soaked angular spots on leaves with yellow halo; defoliation; sunken scabby spots on fruit.",
        "severity": "High",
        "chemical": "Copper hydroxide 77 WP @ 3 g/L; Streptomycin sulphate + Tetracycline — spray preventively from shuck split to harvest.",
        "biological": "No effective biocontrol; copper-based bactericides are the main tool.",
        "cultural": "Windbreaks reduce spread; resistant varieties; avoid overhead irrigation; remove infected shoots; balanced nitrogen.",
    },
    "Healthy Peach Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Monitor for peach leaf curl during bud swell period; single copper spray at leaf drop effective.",
    },

    # ─── BELL PEPPER ──────────────────────────────────────────────────
    "Bell Pepper With Bacterial Spot": {
        "pathogen": "Xanthomonas campestris pv. vesicatoria (Bacterial)",
        "symptoms": "Small water-soaked spots on leaves and fruit; spots turn brown with yellow halo; scabby corky spots on fruit.",
        "severity": "High",
        "chemical": "Copper oxychloride 50 WP @ 3 g/L; Streptomycin sulphate 20 SP @ 1 g/L + Copper @ 3 g/L — spray at first symptom and every 7-10 days.",
        "biological": "Pseudomonas fluorescens 0.5% foliar spray as preventive.",
        "cultural": "Use certified disease-free seed; drip irrigation instead of overhead; crop rotation (3-4 years); remove infected plant debris; avoid transplanting in rain.",
    },
    "Healthy Bell Pepper Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Monitor for thrips (TSWV vector) and CMV aphid vectors; use reflective mulch.",
    },

    # ─── POTATO ───────────────────────────────────────────────────────
    "Potato With Early Blight": {
        "pathogen": "Alternaria solani (Fungal)",
        "symptoms": "Dark brown concentric ring spots (target board) on older leaves; defoliation from bottom upward; tuber lesion possible.",
        "severity": "Medium",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Chlorothalonil 75 WP @ 2 g/L; Azoxystrobin 23 SC @ 1 mL/L — start sprays at 30 DAS.",
        "biological": "Bacillus subtilis product; Trichoderma viride soil treatment.",
        "cultural": "Certified seed; crop rotation 3 years; remove crop debris; balanced N (excess N worsens disease); avoid overhead irrigation.",
    },
    "Potato With Late Blight": {
        "pathogen": "Phytophthora infestans (Oomycete)",
        "symptoms": "Water-soaked pale green to brown lesions on leaf margins; white sporulation on underside in humid conditions; tuber rot with reddish-brown discolouration.",
        "severity": "Very High",
        "chemical": "Metalaxyl + Mancozeb 72 WP @ 2.5 g/L; Cymoxanil + Mancozeb 72 WP @ 2.5 g/L; Dimethomorph 50 WP @ 1 g/L — spray every 7 days under high humidity (>85%).",
        "biological": "Copper-based fungicides; Pseudomonas fluorescens as preventive (limited efficacy).",
        "cultural": "Use certified seed potato; plant on well-drained ridges; earthing up; destroy volunteer plants; haulm destruction before harvest; avoid excessive irrigation.",
    },
    "Healthy Potato Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Monitor weather — late blight risk rises above 90% humidity + 15-25°C; initiate preventive spray programme if blightcast warning issued.",
    },

    # ─── RASPBERRY / STRAWBERRY / BLUEBERRY ─────────────────────────
    "Healthy Raspberry Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Maintain trellising; annual cane renewal; monitor for botrytis in wet seasons.",
    },
    "Healthy Soybean Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "Rhizobium seed treatment essential; Trichoderma soil application.",
        "cultural": "Monitor for soybean rust (Phakopsora pachyrhizi) — spray Tebuconazole if detected.",
    },
    "Squash With Powdery Mildew": {
        "pathogen": "Podosphaera xanthii (Fungal)",
        "symptoms": "White powdery spots on upper leaf surface; leaves turn yellow and dry; reduced fruit size.",
        "severity": "Medium",
        "chemical": "Wettable sulphur 80 WP @ 3 g/L; Carbendazim 50 WP @ 1 g/L; Myclobutanil 10 WP @ 0.5 g/L.",
        "biological": "Neem oil 2% spray; potassium bicarbonate 5 g/L; Ampelomyces quisqualis based product.",
        "cultural": "Resistant varieties; avoid over-head irrigation; proper spacing; remove infected leaves; balanced nitrogen (excess N increases susceptibility).",
    },
    "Strawberry With Leaf Scorch": {
        "pathogen": "Diplocarpon earlianum (Fungal)",
        "symptoms": "Small dark purple to red spots on leaves; spots enlarge with white centre and red border; leaf edges appear scorched.",
        "severity": "Medium",
        "chemical": "Captan 50 WP @ 2 g/L; Myclobutanil 10 WP @ 0.5 g/L — spray every 10 days from emergence.",
        "biological": "Trichoderma harzianum application; remove infected leaves.",
        "cultural": "Avoid overhead irrigation; remove old infected leaves after harvest; ensure good air circulation; do not crowd plants.",
    },
    "Healthy Strawberry Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Monitor for grey mould (Botrytis cinerea) during wet or humid periods.",
    },

    # ─── TOMATO ───────────────────────────────────────────────────────
    "Tomato With Bacterial Spot": {
        "pathogen": "Xanthomonas perforans / X. euvesicatoria (Bacterial)",
        "symptoms": "Small water-soaked spots on leaves and fruit; spots with yellow halo turn dark brown; defoliation; scabby fruit lesions.",
        "severity": "High",
        "chemical": "Copper oxychloride 50 WP @ 3 g/L; Kasugamycin 3 SL @ 2 mL/L — spray at 10-day intervals.",
        "biological": "Pseudomonas fluorescens 0.5% foliar spray; avoid copper-resistant strains.",
        "cultural": "Certified disease-free seedlings; drip irrigation; staking to improve airflow; crop rotation; remove plant debris; avoid transplanting in wet conditions.",
    },
    "Tomato With Early Blight": {
        "pathogen": "Alternaria solani (Fungal)",
        "symptoms": "Concentric ring (target board) dark brown spots on older leaves; yellowing around lesions; collar rot at soil level.",
        "severity": "High",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Chlorothalonil 75 WP @ 2 g/L; Azoxystrobin 23 SC @ 1 mL/L — start at 30-35 DAS.",
        "biological": "Bacillus subtilis 1% spray; Trichoderma viride soil drench.",
        "cultural": "Crop rotation (3 years); staking; balanced NPK; mulching to prevent soil splash; remove lower infected leaves; use TNAU-recommended varieties (CO3, PKM1).",
    },
    "Tomato With Late Blight": {
        "pathogen": "Phytophthora infestans (Oomycete)",
        "symptoms": "Large water-soaked irregular brown lesions on leaves; white sporulation on underside; brown lesions on stems; fruit rot.",
        "severity": "Very High",
        "chemical": "Metalaxyl 8% + Mancozeb 64% WP @ 2.5 g/L; Cymoxanil + Mancozeb 72 WP @ 2.5 g/L — spray every 7 days during wet/cool weather.",
        "biological": "Copper hydroxide 77 WP as protective spray; Bacillus subtilis as early intervention.",
        "cultural": "Stake plants; avoid overhead irrigation; avoid high humidity conditions; crop rotation; early morning irrigation only; remove and destroy infected plants.",
    },
    "Tomato With Leaf Mold": {
        "pathogen": "Passalora fulva / Fulvia fulva (Fungal)",
        "symptoms": "Pale green-yellow spots on upper leaf surface; olive-green to brown velvety mold on lower surface; leaf curl and drop.",
        "severity": "Medium",
        "chemical": "Chlorothalonil 75 WP @ 2 g/L; Tebuconazole 25 EC @ 1 mL/L; Copper oxychloride 50 WP @ 3 g/L.",
        "biological": "Trichoderma asperellum 0.5% spray.",
        "cultural": "Reduce humidity in greenhouses; improve ventilation; avoid overcrowding; remove infected leaves; drip irrigation; grow resistant varieties.",
    },
    "Tomato With Septoria Leaf Spot": {
        "pathogen": "Septoria lycopersici (Fungal)",
        "symptoms": "Small circular spots with dark border and white centre with small black dots (pycnidia); starts on lower leaves; severe defoliation.",
        "severity": "High",
        "chemical": "Mancozeb 75 WP @ 2.5 g/L; Chlorothalonil 75 WP @ 2 g/L; Myclobutanil 10 WP @ 0.5 g/L — spray every 10 days.",
        "biological": "Bacillus subtilis-based product; copper-based sprays.",
        "cultural": "Crop rotation (3 years); avoid overhead irrigation; stake plants; remove and bury infected plant material; weed control (nightshade weeds are hosts).",
    },
    "Tomato With Spider Mites Or Two-Spotted Spider Mite": {
        "pathogen": "Tetranychus urticae (Mite)",
        "symptoms": "Fine webbing on underside of leaves; stippling/bronzing of leaves; severe infestation causes leaf drop; tiny moving dots visible with lens.",
        "severity": "High",
        "chemical": "Spiromesifen 240 SC @ 0.75 mL/L; Abamectin 1.8 EC @ 0.5 mL/L; Dicofol 18.5 EC @ 2 mL/L — alternate chemicals to avoid resistance.",
        "biological": "Predatory mite Phytoseiulus persimilis release; Neoseiulus californicus; Verticillium lecanii spray.",
        "cultural": "Avoid water stress (mites thrive in dry conditions); spray water jets on underside of leaves; remove heavily infested leaves; avoid pyrethroid insecticides (they kill predatory mites).",
    },
    "Tomato With Target Spot": {
        "pathogen": "Corynespora cassiicola (Fungal)",
        "symptoms": "Brown circular spots with concentric rings and yellow halo on leaves; defoliation; lesions on stem and fruit.",
        "severity": "Medium",
        "chemical": "Azoxystrobin 23 SC @ 1 mL/L; Tebuconazole 25 EC @ 1 mL/L; Mancozeb 75 WP @ 2.5 g/L.",
        "biological": "Trichoderma viride-based product.",
        "cultural": "Staking for air circulation; avoid overhead irrigation; crop rotation; remove infected leaves; avoid dense planting.",
    },
    "Tomato Yellow Leaf Curl Virus": {
        "pathogen": "Tomato Yellow Leaf Curl Virus — TYLCV (transmitted by Bemisia tabaci whitefly)",
        "symptoms": "Severe upward curling and yellowing of leaves; stunted plant; flower drop; no/very few fruits.",
        "severity": "Very High",
        "chemical": "Control vector whitefly: Imidacloprid 17.8 SL @ 0.5 mL/L; Thiamethoxam 25 WG @ 0.3 g/L; Spiromesifen 240 SC @ 0.75 mL/L — spray on seedlings and early crop.",
        "biological": "Encarsia formosa parasitoid; yellow sticky traps @ 25/ha.",
        "cultural": "Grow TYLCV-tolerant varieties (e.g. Sakthi; SVPTT1); use 40-mesh insect-proof net nursery; rogue infected plants immediately; reflective silver mulch; remove weed hosts.",
    },
    "Tomato Mosaic Virus": {
        "pathogen": "Tomato Mosaic Virus — ToMV / Tobacco Mosaic Virus — TMV (contact/sap transmission)",
        "symptoms": "Light and dark green mosaic mottling on leaves; leaf distortion; stunting; reduced and malformed fruit.",
        "severity": "High",
        "chemical": "No curative chemical available. Control aphid vectors: Imidacloprid 17.8 SL @ 0.3 mL/L.",
        "biological": "Mineral oil spray to suppress aphid transmission; no effective biocontrol for the virus.",
        "cultural": "Wash hands with soap before handling plants; sterilise tools; remove and destroy infected plants; control aphid vectors; certified virus-free seed; avoid tobacco products near plants.",
    },
    "Healthy Tomato Plant": {
        "pathogen": None,
        "symptoms": "No disease detected.",
        "severity": "None",
        "chemical": "No treatment required.",
        "biological": "No intervention needed.",
        "cultural": "Implement preventive spray calendar; monitor for whitefly (TYLCV vector) and thrips (TSWV vector); use yellow sticky traps.",
    },
}

# Supported crops extracted from model labels
SUPPORTED_CROPS = sorted({
    "Apple", "Blueberry", "Cherry", "Corn (Maize)", "Grape",
    "Orange", "Peach", "Bell Pepper", "Potato", "Raspberry",
    "Soybean", "Squash", "Strawberry", "Tomato",
})

# All disease labels from the model (not healthy states)
SUPPORTED_DISEASES = sorted([
    label for label in GUIDANCE.keys()
    if "Healthy" not in label
])


def get_guidance(disease_label: str) -> dict:
    key = disease_label.strip()
    return GUIDANCE.get(key, {
        "pathogen": "Unknown",
        "symptoms": "Refer to TNAU crop protection manual for details.",
        "severity": "Unknown",
        "chemical": "Consult your nearest Krishi Vigyan Kendra (KVK) or block agriculture officer.",
        "biological": "Apply general biocontrol practices; Trichoderma and Pseudomonas as preventive.",
        "cultural": "Crop rotation; remove infected plant material; balanced nutrition.",
    })


def estimate_severity(confidence: float, disease_label: str) -> str:
    if "Healthy" in disease_label:
        return "None"
    base = GUIDANCE.get(disease_label, {}).get("severity", "Unknown")
    if confidence < 0.40:
        return "Low (uncertain prediction)"
    return base
