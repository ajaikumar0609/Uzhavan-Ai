-- Auto-generated seed SQL from TNAU extraction

-- Crop Varieties (from text extraction)
CREATE TABLE IF NOT EXISTS crop_varieties (
  variety_id SERIAL PRIMARY KEY,
  crop VARCHAR(100),
  variety VARCHAR(100),
  season VARCHAR(100),
  zone VARCHAR(100),
  source_url TEXT
);

INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('General', 'CO2', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/agriculture/agri_min_nutri_history.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Pearl Millet', 'CO (', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_cumbunapierhybrids.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Pearl Millet', 'CO 6', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_cumbunapierhybrids.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Pearl Millet', 'CO 8', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_cumbunapierhybrids.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Pearl Millet', 'CO 7', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/agriculture/agri_seasonandvarieties_cumbunapierhybrids.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('General', 'IRR', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/farm_enterprises/Farm enterprises_ Forest nursery.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'CO 1', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/horticulture/horti_vegetables_lab%20lab.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'CO 2', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/horticulture/horti_vegetables_lab%20lab.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'CO 3', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/horticulture/horti_vegetables_lab%20lab.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'CO 4', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/horticulture/horti_vegetables_lab%20lab.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'CO 5', '', 'Tamil Nadu', 'http://agritech.tnau.ac.in/horticulture/horti_vegetables_lab%20lab.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Guava', 'TRY (', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/horticulture/horti_fruits_guava.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('General', 'CO1', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/horticulture/horti_fruits_sapota.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('General', 'CO 2', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/horticulture/horti_fruits_sapota.html') ON CONFLICT DO NOTHING;
INSERT INTO crop_varieties(crop, variety, season, zone, source_url) VALUES ('Rice', 'MDU 1', '', 'Tamil Nadu', 'https://agritech.tnau.ac.in/horticulture/horti_vegetables_clusterbeans.html') ON CONFLICT DO NOTHING;

-- Total varieties: 15
