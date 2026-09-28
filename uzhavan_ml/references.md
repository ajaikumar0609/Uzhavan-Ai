# UZHAVAN AI: verified references (IEEE style)

Verified 2026-09-25. Each DOI was resolved against its official registry (**Crossref** for papers, **DataCite** for datasets and arXiv). The two DOI-less conference papers were checked on their official proceedings pages. Web sources carry the access date of our actual download (from the dataset metadata in `uzhavan_data/`). Google Scholar itself can't be queried automatically (captcha), so cross-check any entry there by pasting its title.

## A. Datasets actually used
[1] D. Sani, S. Mahato, S. Saini, H. K. Agarwal, C. C. Devshali, S. Anand, G. Arora, and T. Jayaraman, "SICKLE: A multi-sensor satellite imagery dataset annotated with multiple key cropping parameters," in *Proc. IEEE/CVF Winter Conf. Appl. Comput. Vis. (WACV)*, 2024, pp. 5983–5992, doi: 10.1109/WACV57701.2024.00589.

[2] D. P. Hughes and M. Salathé, "An open access repository of images on plant health to enable the development of mobile disease diagnostics," *arXiv preprint* arXiv:1511.08060, 2015, doi: 10.48550/arXiv.1511.08060.  *(the PlantVillage dataset itself)*

[3] S. P. Mohanty, D. P. Hughes, and M. Salathé, "Using deep learning for image-based plant disease detection," *Frontiers in Plant Science*, vol. 7, Art. no. 1419, 2016, doi: 10.3389/fpls.2016.01419.

[4] P. K. E, "Multi-Crop Disease Dataset," Mendeley Data, 2025, doi: 10.17632/6243z8r6t6.1.  *(VIT Chennai; banana, chilli, groundnut: our primary source)*

[5] K. Patil, "Coconut Tree Disease Dataset," Mendeley Data, 2023, doi: 10.17632/gh56wbsnj5.1.

[6] S. Daphal, "Sugarcane Leaf Disease Dataset," Mendeley Data, 2022, doi: 10.17632/9424skmnrk.1.

[7] B. Sasmal, "A novel groundnut leaf dataset for detection and classification of groundnut leaf diseases," Mendeley Data, v2, 2024, doi: 10.17632/x6x5jkk873.2.  *(our groundnut cross-source test set)*

[8] S. Talasila, "Blackgram Plant Leaf Disease Dataset," Mendeley Data, v3, 2022, doi: 10.17632/zfcv9fmrgv.3.

[9] P. K. Sethy, "Rice Leaf Disease Image Samples," Mendeley Data, v2, 2024, doi: 10.17632/fwcj7stb8r.2.

[10] J. Shah and H. Prajapati, "Rice Leaf Diseases," UCI Machine Learning Repository, 2017, doi: 10.24432/C5R013.

[11] X. Wu, C. Zhan, Y.-K. Lai, M.-M. Cheng, and J. Yang, "IP102: A large-scale benchmark dataset for insect pest recognition," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2019, pp. 8779–8788, doi: 10.1109/CVPR.2019.00899.  *(academic-use licence; research evaluation only, never in the product)*

## B. Models and methods
[12] M. Tan and Q. V. Le, "EfficientNetV2: Smaller models and faster training," in *Proc. 38th Int. Conf. Mach. Learn. (ICML)*, PMLR, vol. 139, 2021, pp. 10096–10106.

[13] J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, "ImageNet: A large-scale hierarchical image database," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2009, pp. 248–255, doi: 10.1109/CVPR.2009.5206848.  *(source of the pretrained weights)*

[14] V. Sainte Fare Garnot and L. Landrieu, "Panoptic segmentation of satellite image time series with convolutional temporal attention networks," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)*, 2021, pp. 4852–4861, doi: 10.1109/ICCV48922.2021.00483.  *(U-TAE; SICKLE's model code builds on it)*

[15] X. Shi, Z. Chen, H. Wang, D.-Y. Yeung, W.-K. Wong, and W.-C. Woo, "Convolutional LSTM network: A machine learning approach for precipitation nowcasting," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 28, 2015.

## C. Satellite missions
[16] M. Drusch *et al.*, "Sentinel-2: ESA's optical high-resolution mission for GMES operational services," *Remote Sensing of Environment*, vol. 120, pp. 25–36, 2012, doi: 10.1016/j.rse.2011.11.026.

[17] R. Torres *et al.*, "GMES Sentinel-1 mission," *Remote Sensing of Environment*, vol. 120, pp. 9–24, 2012, doi: 10.1016/j.rse.2011.05.028.

[18] D. P. Roy *et al.*, "Landsat-8: Science and product vision for terrestrial global change research," *Remote Sensing of Environment*, vol. 145, pp. 154–172, 2014, doi: 10.1016/j.rse.2014.02.001.

## D. Weather and climate
[19] D. S. Pai, M. Rajeevan, O. P. Sreejith, B. Mukhopadhyay, and N. S. Satbha, "Development of a new high spatial resolution (0.25° × 0.25°) long period (1901–2010) daily gridded rainfall data set over India and its comparison with existing data sets over the region," *MAUSAM*, vol. 65, no. 1, pp. 1–18, 2014, doi: 10.54302/mausam.v65i1.851.  *(IMD's required citation for the rainfall grid)*

[20] A. K. Srivastava, M. Rajeevan, and S. R. Kshirsagar, "Development of a high resolution daily gridded temperature data set (1969–2005) for the Indian region," *Atmospheric Science Letters*, vol. 10, no. 4, pp. 249–254, 2009, doi: 10.1002/asl.232.  *(IMD's required citation for the temperature grid)*

[21] H. Hersbach *et al.*, "The ERA5 global reanalysis," *Quarterly Journal of the Royal Meteorological Society*, vol. 146, no. 730, pp. 1999–2049, 2020, doi: 10.1002/qj.3803.  *(upstream data behind Open-Meteo)*

[22] P. Zippenfenig, "Open-Meteo.com Weather API," Zenodo, v1.4.0, 2024, doi: 10.5281/zenodo.7970649.

[23] NASA Langley Research Center, "Prediction of Worldwide Energy Resources (POWER) Project, Daily API v2.10.0." [Online]. Available: https://power.larc.nasa.gov (accessed Sep. 25, 2026).

*(Only if ERA5-Land is later collected: J. Muñoz-Sabater et al., "ERA5-Land: a state-of-the-art global reanalysis dataset for land applications," Earth Syst. Sci. Data, vol. 13, pp. 4349–4383, 2021, doi: 10.5194/essd-13-4349-2021. It has NOT been collected, so don't cite it as used.)*

## E. Soil and boundaries
[24] L. Poggio, L. M. de Sousa, N. H. Batjes, G. B. M. Heuvelink, B. Kempen, E. Ribeiro, and D. Rossiter, "SoilGrids 2.0: Producing soil information for the globe with quantified spatial uncertainty," *SOIL*, vol. 7, no. 1, pp. 217–240, 2021, doi: 10.5194/soil-7-217-2021.

[25] D. Runfola *et al.*, "geoBoundaries: A global database of political administrative boundaries," *PLOS ONE*, vol. 15, no. 4, Art. no. e0231866, 2020, doi: 10.1371/journal.pone.0231866.

[26] Department of Agriculture & Farmers Welfare, Govt. of India, "Soil Health Card: Nutrient Dashboard." [Online]. Available: https://www.soilhealth.dac.gov.in/nutrient-dashboard (accessed Sep. 24, 2026).

## F. Agricultural knowledge, production and market sources
[27] Tamil Nadu Agricultural University, "TNAU Agritech Portal." [Online]. Available: https://agritech.tnau.ac.in (accessed Jun. 30, 2026).

[28] Tamil Nadu Agricultural University and Department of Agriculture, Govt. of Tamil Nadu, *Crop Production Guide 2020: Agriculture* and *Crop Production Guide 2020: Horticulture*. Coimbatore, India: TNAU, 2020.

[29] ICRISAT, "District Level Database (DLD) for Indian Agriculture." [Online]. Available: http://data.icrisat.org/dld (accessed Sep. 24, 2026).

[30] Department of Economics and Statistics, Govt. of Tamil Nadu, "Season and Crop Report of Tamil Nadu 2024–25 (Fasli 1434)." [Online]. Available: https://www.tn.gov.in/crop/stat.htm (accessed Sep. 24, 2026).

[31] Directorate of Marketing & Inspection, Ministry of Agriculture & Farmers Welfare, Govt. of India, "AGMARKNET: Agricultural Marketing Information Network." [Online]. Available: https://agmarknet.gov.in (accessed Sep. 25, 2026).

## G. Related work only: NOT used as data (cite only as unavailable / future work)
[32] Petchiammal, B. Kiruba, Murugan, and P. Arjunan, "Paddy Doctor: A visual image dataset for automated paddy disease classification and benchmarking," in *Proc. 6th Joint Int. Conf. Data Science & Management of Data (CODS-COMAD)*, 2023, pp. 203–207, doi: 10.1145/3570991.3570994.
*(Real paper, but we could not obtain the data, which needs an IEEE/Kaggle login. Never write that UZHAVAN was trained on it.)*

## Required attribution notices (paper acknowledgements and app "About" screen)
- "Contains modified Copernicus Sentinel data 2024–2025."
- "Landsat imagery courtesy of the U.S. Geological Survey."
- "Weather data by Open-Meteo.com" (CC BY 4.0).
- NASA POWER (exact wording from the POWER referencing page, recorded in our metadata): "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division." Add the service/version (Daily API v2.10.0) and the access date. POWER also asks to be sent references to publications that use its data.
- The CC BY 4.0 datasets [4]–[10] require attribution (cite them as above).
