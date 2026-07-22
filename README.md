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

# Data Visualisation
## Prepare Datasets (Pre-requisites for data visualization on Tableau)
1) Run `src\merge_datasets.py` to get `merged_resale_prices.csv`
2) Add .env with ONEMAP_TOKEN
3) Run `src\geocode_addresses.py` to get `geocoded_addresses.csv` and `merged_resale_prices_geocoded.csv`
4) Run `Cleaning_data.ipynb` to clean `geocode_final.csv` (Used for Tableau data visualization 1), clean `geocoded_addresses.csv` and get planning area information into transactions
5) Run `scale_prices_2026q2.ipynb` to get `geocode_final_scaled_2026q2.csv`, used in next step. Scales 2023-2026 transactions to 2026q2 based on RPI
6) Run `adding_geo_loc.ipynb` to get `geocoded_final_scaled_2026_with_poi.csv`, used for visualization 2 and 3. Gets train station (2025), primary school, malls and get distance to geocoded_addresses.csv. 

# Data Modeling

## Question A
Go through `src/Q2 Data Modelling/q1_2014_model.ipynb`
## Question B
Go through `src/Q2 Data Modelling/q2_2017_fair_price.ipynb`



## Adding points of interest (POI) distances

After geocoding addresses, run the following to compute nearest-distance features (MRT, primary
school, popular primary school, shopping mall) and save them to
`data/geo_addresses_with_poi_{YEAR}.csv`:

```bash
python src/adding_geo.py [year]
```

`year` is optional and supports `2025` (default) or `2014`, selecting which MRT station master plan
layer to join against.

# Prompts for calude code
 Look at the pdf questions, I have already loaded the data into the folder. Create .gitignore for data folder and the pdf. Merge the datasets together and write a code to get the coordinates, but keep in midn the API calls per minute. Once that is done, save the merged dataset into a csv. Do section 1 first


