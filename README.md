# hdb_resale_prices
Study of HDB prices in SG

## Data source
Create a `data` folder. Put all data sources in data folder. Used data sources include
- Resale flat transactions (https://data.gov.sg/dataset/resale-flat-prices)
- GeneralInformationOfSchools (https://data.gov.sg/datasets/d_688b934f82c1059ed0a6993d2a829089/view)
- MasterPlan2025RailStationNameLayer(https://data.gov.sg/datasets/d_2c06c9fe8ae724b5d33efa1f203e2c38/view)
- MasterPlan2014RailStation.geojson (https://data.gov.sg/datasets/d_c0b3488b2581d64261d629112d7d1470/view)
- Masterplan2019PlanningAreaBoundaryNoSea.geojson(https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view)
- rpi-table.csv (https://www.hdb.gov.sg/-/media/managing-my-home/selling-a-flat/process-for-selling-a-flat/resale-flat-planning/resale-statistics/RPI-Table.pdf?sc_lang=en&hash=2EC6687DDDB6A50A55E86BE61E490205)
- SG_planning_areas.csv (https://en.wikipedia.org/wiki/Planning_areas_of_Singapore)
- shopping_mall_coordinates.csv (https://www.kaggle.com/datasets/karthikgangula/shopping-mall-coordinates)
- COE prices (https://data.gov.sg/datasets/d_69b3380ad7e51aff3a7dcc84eba52b8a/view)
- GDP (https://data.gov.sg/datasets/d_a5ff719648a0e6d4b4c623ee383ab686/view)

## Tableau Links
https://public.tableau.com/app/profile/zheng.ing.ching2990/viz/HDB_resale/Q1MedianResaleandTransactionsacrTime
https://public.tableau.com/app/profile/zheng.ing.ching2990/viz/HDB_resale_POI/Dashboard3
https://public.tableau.com/app/profile/zheng.ing.ching2990/viz/HDBResale_floor_area/Q2Dashboard

# Data Visualisation
## Prepare Datasets (Pre-requisites for data visualization on Tableau and modelling)
1) Run `src\merge_datasets.py` to get `merged_resale_prices.csv`
2) Add .env with ONEMAP_TOKEN
3) Run `src\geocode_addresses.py` to get `geocoded_addresses.csv` and `merged_resale_prices_geocoded.csv`
4) Run `Cleaning_data.ipynb` to clean `geocode_final.csv` (Used for Tableau data visualization 1), clean `geocoded_addresses.csv` and get planning area information into transactions
5) Run `scale_prices_2026q2.ipynb` to get `geocode_final_scaled_2026q2.csv`, used in next step. Scales 2023-2026 transactions to 2026q2 based on RPI
6) Run `adding_geo_loc.ipynb` to get `geocoded_final_scaled_2026_with_poi.csv`, used for visualization 2 and 3. Gets train station (2025), primary school, malls and get distance to geocoded_addresses.csv. 

# Data Modeling

## Adding points of interest (POI) distances

After geocoding addresses, run the following to compute nearest-distance features (MRT, primary
school, popular primary school, shopping mall) and save them to
`data/geo_addresses_with_poi_{YEAR}.csv`:+

`year` is optional and supports `2025` (default) or `2014`, selecting which MRT station master plan
layer to join against.

```bash
python src/adding_geo.py [year]
```

## Question A
Go through `src/Q2 Data Modelling/q1_2014_model.ipynb` It uses `geo_addresses_with_poi_2014`
## Question B
Go through `src/Q2 Data Modelling/q2_2017_fair_price.ipynb`
## Question C
Go through `src/Q2 Data Modelling/q3_flat_type_prediction.ipynb`
`src/Q2 Data Modelling/q3_flat_type_prediction_unsupervised.ipynb` is there for backup/further study

# Policy Analysis

## Question A
Go through `src/Q3 Policy/q1_yishun.ipynb` 
## Quesiton B
Go through `src/Q3 Policy/q2_flat_size_trend.ipynb` 
## Question C
Go through `src/Q3 Policy/q3_dls2.ipynb` 
## Question D
Go through `src/Q3 Policy/q4_coe_vs_far_prices.ipynb`







# Prompts for claude code

## Initial set up
 Look at the pdf questions, I have already loaded the data into the folder. Create .gitignore for data folder and the pdf. Merge the datasets together and write a code to get the coordinates, but keep in mind the API calls per minute. Once that is done, save the merged dataset into a csv. Do section 1 first

## Data Modeling - 2014 prices
Predict a resale flat price’s transaction price in 2014. Use the following characteristics: flat type, flat age and town. Propose and implement a minimum of three models, select the best model, and explain the reasons for your choice. 
Write the code in ipynb, start by filtering out 2011-2014 of data, do some light eda, see what columns have null, then train turn towns in one hot encoded variables. Rescale prices accordingly using utils.py function, where passing rpi table to scale all prices to handle the time nature. Run multiple models like linear regression, randomforest regressor, xgboost regressor, SVR regressor. Come out with different metrics to measure as well, RMSE, MAE. Along side resuable pipelines that scales numerical if needed. Then do a prediction across the quarters of 2014, check for any error drift. Finally, retrain model till 2014q1 to predict on q2, retrain model till q2 to predict on q3 etc to check for improvemnt. Remember to rescale accordingly till latest quarter before predicting on next quarter. 



## dtl 2
The Downtown Line Stage 2 connects the Bukit Panjang heartland to the city. Have
prices increased for resale flats in the towns served by this Line? You might want to use a differencein-differences model for this task

my notebook in dls2,ipynb is just a draft to do this, the code below is not correct, the OLS portion is just a draft. 

downtown line stage 2 starts from bukti panjang, cashew, hillview, hume, beauty world, king albert park, sixth avenue, tan kah kee, botanic gardens, stevens, newtons, little india and rochor. This data should be found in MasterPlan2025RailStationNameLayer.geojson, create a buffer around these stations, say 1km, and check against geo_coded_addresses.csv. only keep those who is inside this buffer. Then join back with merged_resale_prices.csv. 


finally, scale according to utils to a suitable time, maybe the prices based on 2015-q4. Plot the changes in median_rescaled_price, controlled by flat type, among those found. Finally do an OLS but the cutoff date may not be 2015q4 as people may speculate. So plot first