-- ============================================================
-- UZHAVAN AI — Seed Data (Migration 002)
-- Populated from TNAU Agritech Portal knowledge
-- Run after 001_initial_schema.sql
-- ============================================================

-- ─── CROPS ──────────────────────────────────────────────────

INSERT INTO crops (english_name, tamil_name, scientific_name, category, sub_category, season_type, duration_days_min, duration_days_max, water_requirement_mm, soil_ph_min, soil_ph_max, expected_yield_kg_ha, source) VALUES
('Rice', 'நெல்', 'Oryza sativa', 'Cereal', 'Kharif/Rabi', 'Multiple seasons', 100, 160, 1200, 5.5, 7.0, 5000, 'TNAU'),
('Maize', 'மக்காசோளம்', 'Zea mays', 'Cereal', 'Kharif/Rabi', 'Multiple seasons', 90, 100, 600, 5.5, 7.5, 7000, 'TNAU'),
('Sorghum', 'சோளம்', 'Sorghum bicolor', 'Cereal', 'Kharif', 'Kharif', 90, 120, 400, 6.0, 8.0, 3000, 'TNAU'),
('Finger Millet', 'கேழ்வரகு', 'Eleusine coracana', 'Cereal', 'Minor Millet', 'Kharif', 90, 120, 450, 5.0, 7.5, 2500, 'TNAU'),
('Pearl Millet', 'கம்பு', 'Pennisetum glaucum', 'Cereal', 'Minor Millet', 'Kharif', 75, 90, 350, 5.5, 7.5, 2000, 'TNAU'),
('Wheat', 'கோதுமை', 'Triticum aestivum', 'Cereal', 'Rabi', 'Rabi', 110, 130, 500, 6.0, 7.5, 3500, 'TNAU'),
('Kodo Millet', 'வரகு', 'Paspalum scrobiculatum', 'Cereal', 'Minor Millet', 'Kharif', 100, 120, 350, 5.5, 7.5, 1500, 'TNAU'),
('Little Millet', 'சாமை', 'Panicum sumatrense', 'Cereal', 'Minor Millet', 'Kharif', 75, 90, 300, 5.0, 7.0, 1200, 'TNAU'),
('Foxtail Millet', 'தினை', 'Setaria italica', 'Cereal', 'Minor Millet', 'Kharif', 75, 90, 300, 5.5, 7.0, 1500, 'TNAU'),
('Barnyard Millet', 'குதிரைவாலி', 'Echinochloa frumentacea', 'Cereal', 'Minor Millet', 'Kharif', 65, 80, 250, 5.0, 7.5, 1200, 'TNAU'),
('Proso Millet', 'பனிவரகு', 'Panicum miliaceum', 'Cereal', 'Minor Millet', 'Kharif', 60, 75, 250, 5.5, 7.5, 1000, 'TNAU'),
('Pigeonpea', 'துவரை', 'Cajanus cajan', 'Pulse', NULL, 'Kharif', 150, 240, 500, 6.0, 7.5, 1500, 'TNAU'),
('Chickpea', 'கொண்டைக்கடலை', 'Cicer arietinum', 'Pulse', NULL, 'Rabi', 90, 120, 350, 6.0, 8.0, 1200, 'TNAU'),
('Urad (Blackgram)', 'உளுந்து', 'Vigna mungo', 'Pulse', NULL, 'Multiple seasons', 65, 75, 400, 5.5, 7.5, 1000, 'TNAU'),
('Moong (Greengram)', 'பசிப்பயறு', 'Vigna radiata', 'Pulse', NULL, 'Multiple seasons', 60, 70, 350, 6.0, 7.5, 900, 'TNAU'),
('Cowpea', 'தட்டைப்பயறு', 'Vigna unguiculata', 'Pulse', NULL, 'Kharif', 60, 80, 400, 6.0, 7.5, 1000, 'TNAU'),
('Horsegram', 'கொள்ளு', 'Macrotyloma uniflorum', 'Pulse', NULL, 'Rabi', 90, 110, 300, 5.5, 7.5, 800, 'TNAU'),
('Fieldbean (Soybean)', 'சோயாபீன்', 'Glycine max', 'Pulse', NULL, 'Kharif', 90, 110, 600, 6.0, 7.5, 2000, 'TNAU'),
('Groundnut', 'வேர்கடலை', 'Arachis hypogaea', 'Oilseed', NULL, 'Multiple seasons', 90, 120, 500, 5.5, 7.5, 2500, 'TNAU'),
('Sesame', 'எள்', 'Sesamum indicum', 'Oilseed', NULL, 'Kharif', 75, 90, 350, 6.0, 7.5, 600, 'TNAU'),
('Sunflower', 'சூரியகாந்தி', 'Helianthus annuus', 'Oilseed', NULL, 'Multiple seasons', 90, 100, 600, 6.0, 7.5, 2000, 'TNAU'),
('Castor', 'ஆமணக்கு', 'Ricinus communis', 'Oilseed', NULL, 'Annual', 150, 180, 400, 5.0, 7.5, 1500, 'TNAU'),
('Safflower', 'குங்குமப்பூ', 'Carthamus tinctorius', 'Oilseed', NULL, 'Rabi', 110, 130, 350, 6.0, 8.0, 1000, 'TNAU'),
('Mustard', 'கடுகு', 'Brassica juncea', 'Oilseed', NULL, 'Rabi', 90, 110, 400, 6.0, 7.5, 1200, 'TNAU'),
('Cotton', 'பருத்தி', 'Gossypium hirsutum', 'Fibre', NULL, 'Kharif', 160, 200, 700, 6.0, 8.0, 2500, 'TNAU'),
('Jute', 'சணல்', 'Corchorus olitorius', 'Fibre', NULL, 'Kharif', 100, 120, 800, 6.0, 7.5, 3000, 'TNAU'),
('Sugarcane', 'கரும்பு', 'Saccharum officinarum', 'Sugar', NULL, 'Annual', 300, 360, 1800, 6.5, 8.0, 100000, 'TNAU'),
('Banana', 'வாழை', 'Musa paradisiaca', 'Fruit', NULL, 'Annual', 270, 330, 1200, 6.0, 7.5, 40000, 'TNAU'),
('Coconut', 'தேங்காய்', 'Cocos nucifera', 'Plantation', NULL, 'Perennial', 1825, 3650, 1500, 5.5, 8.0, 15000, 'TNAU'),
('Mango', 'மாம்பழம்', 'Mangifera indica', 'Fruit', NULL, 'Perennial', 1825, 3650, 1000, 5.5, 7.5, 20000, 'TNAU'),
('Guava', 'கொய்யா', 'Psidium guajava', 'Fruit', NULL, 'Perennial', 730, 1825, 800, 5.0, 7.5, 25000, 'TNAU'),
('Sapota', 'சப்போட்டா', 'Manilkara zapota', 'Fruit', NULL, 'Perennial', 1095, 3650, 900, 6.0, 8.0, 20000, 'TNAU'),
('Papaya', 'பப்பாளி', 'Carica papaya', 'Fruit', NULL, 'Annual/Biennial', 270, 360, 1200, 6.0, 7.5, 50000, 'TNAU'),
('Tomato', 'தக்காளி', 'Solanum lycopersicum', 'Vegetable', NULL, 'Multiple seasons', 90, 120, 600, 6.0, 7.5, 25000, 'TNAU'),
('Onion', 'வெங்காயம்', 'Allium cepa', 'Vegetable', NULL, 'Rabi', 90, 120, 400, 6.0, 7.5, 20000, 'TNAU'),
('Brinjal (Eggplant)', 'கத்தரிக்காய்', 'Solanum melongena', 'Vegetable', NULL, 'Multiple seasons', 120, 150, 500, 5.5, 7.5, 30000, 'TNAU'),
('Chilli', 'மிளகாய்', 'Capsicum annuum', 'Vegetable', NULL, 'Multiple seasons', 120, 180, 600, 6.0, 7.5, 15000, 'TNAU'),
('Okra (Bhendi)', 'வெண்டை', 'Abelmoschus esculentus', 'Vegetable', NULL, 'Multiple seasons', 55, 65, 600, 6.0, 7.5, 10000, 'TNAU'),
('Moringa (Drumstick)', 'முருங்கை', 'Moringa oleifera', 'Vegetable', 'Tree vegetable', 'Perennial', 210, 365, 400, 6.0, 8.0, 40000, 'TNAU'),
('Turmeric', 'மஞ்சள்', 'Curcuma longa', 'Spice', NULL, 'Annual', 270, 300, 1200, 6.0, 7.5, 15000, 'TNAU'),
('Ginger', 'இஞ்சி', 'Zingiber officinale', 'Spice', NULL, 'Annual', 180, 210, 1500, 5.5, 7.5, 15000, 'TNAU'),
('Garlic', 'பூண்டு', 'Allium sativum', 'Spice', NULL, 'Rabi', 120, 150, 600, 6.0, 7.5, 8000, 'TNAU'),
('Jasmine', 'மல்லிகை', 'Jasminum sambac', 'Flower', NULL, 'Perennial', 180, 365, 800, 6.5, 7.5, 5000, 'TNAU'),
('Marigold', 'சாமந்தி', 'Tagetes erecta', 'Flower', NULL, 'Annual', 75, 90, 600, 5.5, 7.5, 15000, 'TNAU'),
('Anthurium', 'அந்துரியம்', 'Anthurium andraeanum', 'Flower', NULL, 'Perennial', 365, 730, 1200, 5.5, 6.5, 300000, 'TNAU'),
('Arecanut', 'பாக்கு', 'Areca catechu', 'Plantation', NULL, 'Perennial', 2555, 3650, 1500, 6.0, 8.0, 3000, 'TNAU'),
('Cashew', 'முந்திரி', 'Anacardium occidentale', 'Plantation', NULL, 'Perennial', 1095, 3650, 800, 5.0, 7.0, 1200, 'TNAU'),
('Tapioca (Cassava)', 'மரவள்ளி', 'Manihot esculenta', 'Root Crop', NULL, 'Annual', 270, 360, 1000, 5.5, 7.5, 25000, 'TNAU'),
('Napier Grass (Cumbu Napier)', 'கம்பு நேப்பியர்', 'Pennisetum purpureum × glaucum', 'Fodder', NULL, 'Perennial', 60, 75, 900, 5.5, 7.5, 250000, 'TNAU'),
('Lucerne', 'லூசர்ன்', 'Medicago sativa', 'Fodder', NULL, 'Rabi', 60, 80, 600, 6.5, 7.5, 40000, 'TNAU')
ON CONFLICT (english_name) DO NOTHING;

-- ─── FERTILIZERS ────────────────────────────────────────────

INSERT INTO fertilizers (name, tamil_name, type, n_percent, p_percent, k_percent, secondary_nutrients, form, application_method, recommended_dose_kg_ha, cost_per_kg_inr, notes, source) VALUES
('Urea', 'யூரியா', 'Chemical-N', 46.0, 0.0, 0.0, NULL, 'Granular', 'Broadcast / Split', '100-200', 6.50, 'Split into 3 doses for rice; avoid at waterlogged conditions', 'TNAU'),
('Ammonium Sulphate', 'அமோனியம் சல்பேட்', 'Chemical-N', 20.6, 0.0, 0.0, 'S: 24%', 'Granular', 'Broadcast', '250-500', 12.0, 'Provides nitrogen + sulphur; good for oilseeds; slightly acidifying', 'TNAU'),
('DAP (Diammonium Phosphate)', 'டி.ஏ.பி.', 'NP', 18.0, 46.0, 0.0, NULL, 'Granular', 'Basal application', '100-150', 27.0, 'High P content; basal only; popular for P-deficient soils', 'TNAU'),
('MOP (Muriate of Potash)', 'எம்.ஓ.பி.', 'Potassic', 0.0, 0.0, 60.0, NULL, 'Granular', 'Broadcast basal', '50-100', 20.0, 'For potassium deficiency; avoid in saline soils', 'TNAU'),
('SSP (Single Super Phosphate)', 'எஸ்.எஸ்.பி.', 'Phosphatic', 0.0, 16.0, 0.0, 'Ca: 21%; S: 12%', 'Granular/Powder', 'Basal broadcast', '250-375', 8.0, 'Also provides calcium and sulphur; good for legumes', 'TNAU'),
('NPK 17-17-17', 'என்.பி.கே 17-17-17', 'Complex NPK', 17.0, 17.0, 17.0, NULL, 'Granular', 'Basal / Top dress', '250-300', 22.0, 'Balanced nutrition; useful for transplanting; fertigation grade available', 'TNAU'),
('NPK 10-26-26', 'என்.பி.கே 10-26-26', 'Complex NPK', 10.0, 26.0, 26.0, NULL, 'Granular', 'Basal', '200-250', 24.0, 'High P and K formula; for vegetables and fruits', 'TNAU'),
('NPK 20-20-0', 'என்.பி.கே 20-20-0', 'Complex NPK', 20.0, 20.0, 0.0, NULL, 'Granular', 'Basal', '200-250', 20.0, 'No K content; use when potassium status is adequate', 'TNAU'),
('Zinc Sulphate (ZnSO4)', 'ஜிங்க் சல்பேட்', 'Micronutrient', 0.0, 0.0, 0.0, 'Zn: 21%; S: 11%', 'Granular/Powder', 'Basal / Foliar spray', '25', 35.0, 'Apply 25 kg/ha basal or 0.5% foliar spray; for Zinc deficiency common in TN soils', 'TNAU'),
('Ferrous Sulphate (FeSO4)', 'பெர்ரஸ் சல்பேட்', 'Micronutrient', 0.0, 0.0, 0.0, 'Fe: 19%; S: 11%', 'Granular/Powder', 'Foliar spray / Basal', '25', 20.0, '0.5% foliar spray for iron deficiency; common in calcareous soils', 'TNAU'),
('Manganese Sulphate (MnSO4)', 'மாங்கனீஸ் சல்பேட்', 'Micronutrient', 0.0, 0.0, 0.0, 'Mn: 27%', 'Powder', 'Foliar spray', '25', 30.0, '0.5% spray for manganese deficiency; mainly in organic-rich soils', 'TNAU'),
('Borax (Sodium Tetraborate)', 'போரக்ஸ்', 'Micronutrient', 0.0, 0.0, 0.0, 'B: 10.6%', 'Powder', 'Foliar spray / Soil', '10-15 for soil; 0.2% spray', 40.0, 'Critical for cotton and sunflower; soil application or 0.2% foliar spray', 'TNAU'),
('Gypsum (Calcium Sulphate)', 'ஜிப்சம்', 'Soil Amendment', 0.0, 0.0, 0.0, 'Ca: 23%; S: 18%', 'Powder', 'Broadcast soil', '400-500', 4.0, 'Reclaims alkaline/sodic soils; essential for groundnut pod filling; apply 400 kg/ha', 'TNAU'),
('Lime (Agricultural)', 'சுண்ணாம்பு', 'Soil Amendment', 0.0, 0.0, 0.0, 'Ca: 40%', 'Powder', 'Broadcast basal', '500-1000', 2.0, 'For acidic soils pH <5.5; raises pH; apply 6 months before sowing if possible', 'TNAU'),
('FYM (Farm Yard Manure)', 'தொழு உரம்', 'Organic', 0.5, 0.2, 0.5, 'Multiple micronutrients', 'Solid/Decomposed', 'Broadcast + incorporate', '10000-15000', 0.50, 'Well-decomposed; apply 4-6 weeks before planting; improves soil structure', 'TNAU'),
('Vermicompost', 'மண்புழு உரம்', 'Organic', 1.5, 0.5, 0.8, 'Humus + growth hormones', 'Granular', 'Basal / Row application', '2000-3000', 8.0, 'High quality organic matter; contains beneficial microorganisms; use 2-3 t/ha', 'TNAU'),
('Green Manure (Sesbania/Dhaincha)', 'பச்சை உரம்', 'Organic', 2.0, 0.3, 1.5, NULL, 'Living plant', 'Incorporate 30-45 DAS', '25 kg seeds/ha', 25.0, 'Sow 25 kg/ha; incorporate before flowering; adds 60-80 kg N/ha equivalent', 'TNAU'),
('Neem Cake', 'வேப்பம் புண்ணாக்கு', 'Organic', 5.2, 1.0, 1.4, 'Neem compounds: pest repellent', 'Granular/Powder', 'Basal / Root zone', '200-250', 15.0, 'Nitrification inhibitor - slows N loss; also controls soil pests; mix with urea', 'TNAU'),
('Rhizobium (Legume Biofertilizer)', 'ரைசோபியம்', 'Biofertilizer', 0.0, 0.0, 0.0, 'N-fixation: 50-100 kg N/ha', 'Liquid/Carrier', 'Seed treatment', '200 mL/kg seed', 100.0, 'Seed coat with rice gruel; must be crop-specific strain; not compatible with chemical fungicides', 'TNAU'),
('Azospirillum (N-Fixing)', 'அசோஸ்பிரில்லம்', 'Biofertilizer', 0.0, 0.0, 0.0, 'N-fixation: 20-40 kg N/ha', 'Liquid/Carrier', 'Seed treatment / Soil drench', '200 mL/kg seed or 2 L/ha', 100.0, 'For non-legumes especially rice, maize, sorghum; growth hormone production', 'TNAU'),
('Phosphobacteria (PSB)', 'பாஸ்போபாக்டீரியா', 'Biofertilizer', 0.0, 0.0, 0.0, 'P-solubilization: 20-30 kg P2O5/ha', 'Liquid/Carrier', 'Seed treatment / Soil drench', '200 mL/kg seed', 100.0, 'Solubilizes fixed phosphorus; use with reduced chemical P; effective in P-rich soils', 'TNAU'),
('Potassium Mobilizing Bacteria (KMB)', 'பொட்டாசியம் உரம்', 'Biofertilizer', 0.0, 0.0, 0.0, 'K-mobilization: 20-30 kg K/ha', 'Liquid', 'Seed treatment / Soil drench', '200 mL/kg seed', 120.0, 'Mobilizes K from soil minerals; reduce MOP by 30-50% with KMB application', 'TNAU'),
('VAM (Mycorrhizae)', 'வி.ஏ.எம். பூஞ்சை', 'Biofertilizer', 0.0, 0.0, 0.0, 'P, Zn, water uptake enhancement', 'Carrier/Powder', 'Soil application / Seedling dip', '5-10 kg/ha or 100 g/plant', 200.0, 'Symbiotic fungi; extends root network 10x; beneficial for low-P soils; do not use with fungicides', 'TNAU'),
('Trichoderma viride', 'ட்ரைக்கோடர்மா', 'Biofertilizer/Biocontrol', 0.0, 0.0, 0.0, 'Biocontrol against soil pathogens', 'Carrier/Powder', 'Seed treatment / Soil drench / FYM enrichment', '2-3 kg/ha or mix with FYM', 150.0, 'Controls Fusarium; Pythium; Rhizoctonia wilt; enrich in FYM before application', 'TNAU'),
('Pseudomonas fluorescens', 'சூடோமோனாஸ்', 'Biofertilizer/Biocontrol', 0.0, 0.0, 0.0, 'Biocontrol against leaf pathogens', 'Liquid/Carrier', 'Seed treatment / Foliar spray / Soil drench', '200 mL/kg seed or 0.5% foliar', 120.0, 'Effective against bacterial blight of rice; blast; wilt; growth promoter', 'TNAU')
ON CONFLICT (name) DO NOTHING;

-- ─── SOIL TYPES ─────────────────────────────────────────────

INSERT INTO soil_types (name, tamil_name, texture, ph_range_min, ph_range_max, water_holding_capacity, drainage, districts, suitable_crops, management_tips, source) VALUES
('Alluvial Soil', 'வண்டல் மண்', 'Loamy to clay loam', 6.5, 8.0, 'High', 'Moderate', ARRAY['Thanjavur','Tiruvarur','Nagapattinam','Mayiladuthurai','Ariyalur','Cuddalore'], ARRAY['Rice','Sugarcane','Banana','Coconut','Groundnut','Blackgram'], 'Apply gypsum 500 kg/ha if sodic; ensure drainage; add organic matter', 'TNAU'),
('Black Cotton Soil', 'கருப்பு மண்', 'Clay', 7.5, 9.0, 'Very High', 'Poor', ARRAY['Coimbatore','Erode','Salem','Namakkal','Karur'], ARRAY['Cotton','Sorghum','Sunflower','Chickpea','Blackgram'], 'Deep summer ploughing; gypsum 2 t/ha; broad bed furrow sowing', 'TNAU'),
('Red Laterite Soil', 'சிவப்பு களிமண்', 'Sandy loam to loam', 5.5, 7.0, 'Low to Medium', 'Good', ARRAY['Coimbatore','Erode','Tiruppur','Dharmapuri','Krishnagiri','Salem'], ARRAY['Maize','Groundnut','Ragi','Mango','Coconut','Tomato'], 'Lime 1-2 t/ha; FYM 10 t/ha; zinc sulphate 25 kg/ha regularly', 'TNAU'),
('Sandy Coastal Soil', 'மணல் மண்', 'Sandy', 5.5, 7.5, 'Very Low', 'Excellent', ARRAY['Ramanathapuram','Thoothukudi','Nagapattinam'], ARRAY['Coconut','Cashew','Casuarina','Groundnut','Pearl Millet'], 'Heavy organic matter; drip irrigation mandatory; slow-release fertilizers', 'TNAU'),
('Forest Laterite Soil', 'காட்டு களிமண்', 'Loam to clay loam', 4.5, 6.5, 'Medium', 'Good', ARRAY['Nilgiris','Kanyakumari','Dindigul'], ARRAY['Tea','Coffee','Cardamom','Pepper','Potato','Vegetables'], 'Lime 2 t/ha every 3 years; phosphate fertilizer; terracing on slopes', 'TNAU'),
('Deep Black Alluvial Soil', 'கரிசல் மண்', 'Heavy clay', 6.5, 8.5, 'Very High', 'Poor to Moderate', ARRAY['Thanjavur','Tiruvarur','Nagapattinam','Mayiladuthurai'], ARRAY['Rice','Sugarcane','Banana'], 'Field channels for drainage; gypsum 500 kg/ha; avoid deep tillage when wet', 'TNAU'),
('Sandy Loam', 'மணல் களிமண்', 'Sandy loam', 6.0, 7.5, 'Medium', 'Good', ARRAY['Madurai','Theni','Sivaganga','Pudukottai','Dindigul'], ARRAY['Banana','Cotton','Groundnut','Chilli','Vegetables','Pulses'], 'FYM 10 t/ha; split fertilizer; drip irrigation efficient', 'TNAU'),
('Red Sandy Loam', 'சிவப்பு மணல் களிமண்', 'Sandy loam', 6.0, 7.0, 'Low to Medium', 'Good', ARRAY['Virudhunagar','Ramanathapuram','Thoothukudi'], ARRAY['Groundnut','Cotton','Chilli','Sunflower','Millets'], 'Zinc sulphate 25 kg/ha basal; phosphate critical; FYM to improve water holding', 'TNAU'),
('Saline-Alkaline Soil', 'உவர் மண்', 'Clay to loam', 8.5, 10.0, 'High', 'Poor', ARRAY['Ramanathapuram','Nagapattinam','Thoothukudi'], ARRAY['Salt-tolerant Rice','Sesbania','Green Manure'], 'Gypsum 4-5 t/ha; good drainage; leaching before crop; green manure', 'TNAU'),
('Waterlogged Soil', 'சதுப்பு நிலம்', 'Clay', 6.5, 7.5, 'Saturated', 'Very Poor', ARRAY['Low-lying delta areas'], ARRAY['Deep-water Rice','Swamp Taro'], 'Sub-surface drainage; raised beds; Sesbania for reclamation', 'TNAU')
ON CONFLICT DO NOTHING;

-- ─── DISTRICT PROFILES (with geom centroids) ────────────────

INSERT INTO district_profiles (name, tamil_name, headquarters, agro_climatic_zone, area_sq_km, avg_rainfall_mm, major_crops, major_soil_type, river_basin, groundwater_status, agriculture_area_pct, notable_feature, geom, source) VALUES
('Ariyalur', 'அரியலூர்', 'Ariyalur', 'Cauvery Delta', 1949, 960, ARRAY['Rice','Sugarcane','Banana'], 'Black cotton / Alluvial', 'Cauvery', 'Semi-critical', 65, 'New district from Perambalur; rice dominant', ST_Point(79.0760, 11.1400), 'TN Agri Dept'),
('Chengalpattu', 'செங்கல்பட்டு', 'Chengalpattu', 'North Eastern', 2944, 1200, ARRAY['Rice','Groundnut','Vegetables'], 'Red laterite / Alluvial', 'Palar', 'Critical', 55, 'Suburban Chennai; vegetable supply hub', ST_Point(79.9764, 12.6927), 'TN Agri Dept'),
('Chennai', 'சென்னை', 'Chennai', 'North Eastern', 174, 1400, ARRAY['Urban horticulture'], 'Urban', 'Cooum/Adyar', 'Over-exploited', 2, 'State capital; very limited agriculture', ST_Point(80.2707, 13.0827), 'TN Agri Dept'),
('Coimbatore', 'கோயம்புத்தூர்', 'Coimbatore', 'Western', 4723, 700, ARRAY['Maize','Cotton','Coconut','Banana','Turmeric'], 'Red loam / Sandy loam', 'Noyyal', 'Critical', 60, 'Textile city; TNAU headquarters; major maize belt', ST_Point(76.9558, 11.0168), 'TN Agri Dept'),
('Cuddalore', 'கடலூர்', 'Cuddalore', 'Cauvery Delta', 3703, 1150, ARRAY['Rice','Sugarcane','Coconut'], 'Alluvial / Clay', 'Cauvery/Vellar', 'Semi-critical', 60, 'Major rice-producing delta district', ST_Point(79.7684, 11.7447), 'TN Agri Dept'),
('Dharmapuri', 'தர்மபுரி', 'Dharmapuri', 'North Western', 4497, 900, ARRAY['Maize','Groundnut','Mango','Tapioca'], 'Red laterite', 'Cauvery', 'Semi-critical', 65, 'Largest mango market in Tamil Nadu', ST_Point(78.1579, 12.1277), 'TN Agri Dept'),
('Dindigul', 'திண்டுக்கல்', 'Dindigul', 'Southern', 6266, 750, ARRAY['Banana','Groundnut','Maize','Vegetables'], 'Red laterite / Sandy loam', 'Amaravathi', 'Safe', 60, 'Lock and coffee trade; banana growing region', ST_Point(77.9803, 10.3624), 'TN Agri Dept'),
('Erode', 'ஈரோடு', 'Erode', 'Western', 5757, 750, ARRAY['Turmeric','Banana','Coconut','Maize','Sugarcane'], 'Red loam', 'Bhavani/Cauvery', 'Semi-critical', 65, 'Asia largest turmeric market; textile hub', ST_Point(77.7172, 11.3410), 'TN Agri Dept'),
('Kallakurichi', 'கள்ளக்குறிச்சி', 'Kallakurichi', 'Cauvery Delta', 3521, 1000, ARRAY['Rice','Sugarcane','Banana'], 'Alluvial', 'Gomukhi', 'Semi-critical', 60, 'New district 2019; rice and sugarcane belt', ST_Point(78.9637, 11.7383), 'TN Agri Dept'),
('Kanchipuram', 'காஞ்சிபுரம்', 'Kanchipuram', 'North Eastern', 1687, 1100, ARRAY['Rice','Groundnut','Silk'], 'Alluvial / Red', 'Palar', 'Critical', 55, 'Silk weaving; historical temple town', ST_Point(79.7036, 12.8185), 'TN Agri Dept'),
('Kanyakumari', 'கன்னியாகுமரி', 'Kanyakumari', 'High Rainfall', 1672, 1500, ARRAY['Coconut','Banana','Tapioca','Rice','Rubber'], 'Laterite', 'Thamirabarani', 'Safe', 70, 'Southernmost district; highest rainfall in TN', ST_Point(77.5385, 8.0883), 'TN Agri Dept'),
('Karur', 'கரூர்', 'Karur', 'Cauvery Delta', 2895, 850, ARRAY['Rice','Banana','Sugarcane'], 'Black cotton / Alluvial', 'Cauvery', 'Semi-critical', 60, 'Textile industry; banana and rice belt', ST_Point(78.0767, 10.9601), 'TN Agri Dept'),
('Krishnagiri', 'கிருஷ்ணகிரி', 'Krishnagiri', 'North Western', 5143, 900, ARRAY['Mango','Tomato','Maize','Groundnut'], 'Red laterite', 'Cauvery tributary', 'Safe', 65, 'Mango capital of Tamil Nadu; high altitude tomato', ST_Point(78.2137, 12.5186), 'TN Agri Dept'),
('Madurai', 'மதுரை', 'Madurai', 'Southern', 3741, 850, ARRAY['Rice','Banana','Cotton','Jasmine'], 'Sandy loam / Clay', 'Vaigai', 'Critical', 60, 'Temple city; jasmine flower market; banana hub', ST_Point(78.1198, 9.9252), 'TN Agri Dept'),
('Mayiladuthurai', 'மயிலாடுதுறை', 'Mayiladuthurai', 'Cauvery Delta', 1559, 1100, ARRAY['Rice','Banana'], 'Alluvial', 'Cauvery/Kollidam', 'Semi-critical', 70, 'Newest district 2021; intense rice cultivation', ST_Point(79.6472, 11.1035), 'TN Agri Dept'),
('Nagapattinam', 'நாகப்பட்டினம்', 'Nagapattinam', 'Cauvery Delta', 2716, 1150, ARRAY['Rice','Coconut','Banana'], 'Alluvial coastal', 'Cauvery', 'Safe', 65, 'Coastal district; rice belt', ST_Point(79.8454, 10.7672), 'TN Agri Dept'),
('Namakkal', 'நாமக்கல்', 'Namakkal', 'North Western', 3363, 850, ARRAY['Maize','Banana','Coconut','Poultry'], 'Red loam', 'Cauvery tributary', 'Semi-critical', 60, 'Largest poultry hub in India; maize for feed', ST_Point(78.1675, 11.2189), 'TN Agri Dept'),
('Nilgiris', 'நீலகிரி', 'Ooty', 'High Altitude', 2549, 1500, ARRAY['Tea','Coffee','Vegetables','Potato'], 'Laterite / Forest', 'Moyar/Bhavani', 'Safe', 55, 'High altitude zone; tea estates; vegetable hub', ST_Point(76.7337, 11.4102), 'TN Agri Dept'),
('Perambalur', 'பெரம்பலூர்', 'Perambalur', 'Cauvery Delta', 1752, 900, ARRAY['Rice','Sugarcane','Onion'], 'Black cotton / Sandy', 'Cauvery', 'Semi-critical', 60, 'Limestone quarries; rice and sugarcane belt', ST_Point(78.8795, 11.2332), 'TN Agri Dept'),
('Pudukottai', 'புதுக்கோட்டை', 'Pudukottai', 'Southern', 4663, 850, ARRAY['Rice','Cotton','Banana'], 'Sandy loam / Clay', 'Vellar', 'Safe', 60, 'Historical Pudukkottai state; semi-arid', ST_Point(78.8020, 10.3797), 'TN Agri Dept'),
('Ramanathapuram', 'ராமநாதபுரம்', 'Ramanathapuram', 'Southern', 4175, 800, ARRAY['Rice','Cotton','Chilli','Groundnut'], 'Sandy coastal', 'Pambar', 'Critical', 55, 'Coastal; Rameshwaram pilgrimage; pearl fishing', ST_Point(78.8308, 9.3639), 'TN Agri Dept'),
('Ranipet', 'ராணிபேட்', 'Ranipet', 'North Eastern', 2349, 1050, ARRAY['Rice','Sugarcane','Groundnut'], 'Red / Alluvial', 'Palar', 'Critical', 60, 'Leather industry hub; tannery pollution concern', ST_Point(79.3174, 12.9224), 'TN Agri Dept'),
('Salem', 'சேலம்', 'Salem', 'North Western', 5236, 900, ARRAY['Maize','Mango','Banana','Turmeric','Cotton'], 'Sandy loam / Red', 'Cauvery', 'Semi-critical', 60, 'Steel city; major mango and maize trade', ST_Point(78.1460, 11.6643), 'TN Agri Dept'),
('Sivaganga', 'சிவகங்கை', 'Sivaganga', 'Southern', 4189, 950, ARRAY['Rice','Cotton','Banana'], 'Sandy loam / Black', 'Vaigai', 'Critical', 60, 'Historical Sivaganga kingdom; temple tanks', ST_Point(78.4814, 9.8472), 'TN Agri Dept'),
('Tenkasi', 'தென்காசி', 'Tenkasi', 'Southern', 3279, 1100, ARRAY['Rice','Banana','Turmeric','Coconut'], 'Laterite / Sandy', 'Thamirabarani', 'Safe', 65, 'High rainfall; waterfalls; spice crops', ST_Point(77.3151, 8.9591), 'TN Agri Dept'),
('Thanjavur', 'தஞ்சாவூர்', 'Thanjavur', 'Cauvery Delta', 3399, 1000, ARRAY['Rice','Sugarcane','Banana','Coconut'], 'Alluvial (deep black)', 'Cauvery/Kollidam', 'Semi-critical', 75, 'Rice granary of Tamil Nadu; Brihadeeswarar temple', ST_Point(79.1378, 10.7870), 'TN Agri Dept'),
('Theni', 'தேனி', 'Theni', 'Southern', 3242, 1000, ARRAY['Banana','Grapes','Sugarcane','Garlic'], 'Sandy loam', 'Vaigai', 'Safe', 65, 'Major banana export district; grapes cultivation', ST_Point(77.4767, 10.0104), 'TN Agri Dept'),
('Thoothukudi', 'தூத்துக்குடி', 'Thoothukudi', 'Southern', 4621, 550, ARRAY['Cotton','Groundnut','Rice','Chilli'], 'Sandy coastal / Red', 'Thamirabarani', 'Critical', 55, 'Port city; Pearl fishery; low rainfall district', ST_Point(78.1348, 8.7642), 'TN Agri Dept'),
('Tiruchirappalli', 'திருச்சிராப்பள்ளி', 'Trichy', 'Cauvery Delta', 4404, 900, ARRAY['Rice','Banana','Groundnut','Sugarcane'], 'Alluvial / Red', 'Cauvery', 'Semi-critical', 60, 'Rock Fort; major rice and banana market', ST_Point(78.6869, 10.7905), 'TN Agri Dept'),
('Tirunelveli', 'திருநெல்வேலி', 'Tirunelveli', 'Southern', 6823, 900, ARRAY['Rice','Banana','Cotton','Chilli','Jasmine'], 'Sandy loam / Black', 'Thamirabarani', 'Safe', 65, 'Halwa city; banana cultivation along Thamirabarani', ST_Point(77.6994, 8.7139), 'TN Agri Dept'),
('Tirupathur', 'திருப்பத்தூர்', 'Tirupathur', 'North Eastern', 1795, 1050, ARRAY['Rice','Groundnut','Vegetables'], 'Red laterite', 'Palar tributary', 'Safe', 60, 'New district 2019; agriculture and silk weaving', ST_Point(78.5627, 12.4960), 'TN Agri Dept'),
('Tiruppur', 'திருப்பூர்', 'Tiruppur', 'Western', 5186, 700, ARRAY['Maize','Cotton','Coconut','Banana'], 'Red loam', 'Noyyal', 'Critical', 60, 'Knitwear capital of India; agriculture base', ST_Point(77.3411, 11.1085), 'TN Agri Dept'),
('Tiruvallur', 'திருவள்ளூர்', 'Tiruvallur', 'North Eastern', 3422, 1150, ARRAY['Rice','Groundnut','Vegetables'], 'Alluvial / Red', 'Palar/Kosasthalaiyar', 'Critical', 55, 'Suburban Chennai; peri-urban farming', ST_Point(79.9131, 13.1435), 'TN Agri Dept'),
('Tiruvannamalai', 'திருவண்ணாமலை', 'Tiruvannamalai', 'North Eastern', 6190, 1000, ARRAY['Rice','Sugarcane','Groundnut','Cotton'], 'Red / Sandy', 'Palar/Cheyyar', 'Critical', 60, 'Arunachala temple; major rice belt', ST_Point(79.0747, 12.2253), 'TN Agri Dept'),
('Tiruvarur', 'திருவாரூர்', 'Tiruvarur', 'Cauvery Delta', 2168, 1050, ARRAY['Rice','Banana','Coconut'], 'Deep alluvial', 'Cauvery delta', 'Safe', 75, 'Highest rice area density in TN delta', ST_Point(79.6336, 10.7729), 'TN Agri Dept'),
('Vellore', 'வேலூர்', 'Vellore', 'North Eastern', 3527, 1050, ARRAY['Rice','Sugarcane','Groundnut','Mango'], 'Red / Alluvial', 'Palar', 'Critical', 60, 'Leather city; medical tourism hub', ST_Point(79.1325, 12.9165), 'TN Agri Dept'),
('Villupuram', 'விழுப்புரம்', 'Villupuram', 'Cauvery Delta', 7218, 1100, ARRAY['Rice','Sugarcane','Groundnut','Tapioca'], 'Sandy / Alluvial', 'Pennaiyar', 'Semi-critical', 60, 'Largest district in TN by area; diverse agriculture', ST_Point(79.4938, 11.9395), 'TN Agri Dept'),
('Virudhunagar', 'விருதுநகர்', 'Virudhunagar', 'Southern', 4283, 750, ARRAY['Rice','Cotton','Chilli','Groundnut'], 'Sandy loam / Black', 'Vaigai', 'Critical', 55, 'Fireworks industry; cotton and chilli trade', ST_Point(77.9624, 9.5851), 'TN Agri Dept')
ON CONFLICT (name) DO NOTHING;
