import pandas as pd
import glob

# Defines the folder structure
seasons = ['2024Spring','2024Summer','2024winter', '2025Spring', '2025Summer', '2025Winter']



#this creates an empty list to store dataframes
all_sensors = []



for season in seasons:
    csv_files = glob.glob(f'{season}/*.csv') #finds all CSV files for this season

    print(f"Found {len(csv_files)} files in {season}")

    for file in csv_files:
        df = pd.read_csv(file, usecols=['longitude', 'latitude', 'deviceId'])

        sensor_id = df['deviceId'].unique()
        id = sensor_id[0]
        if len(sensor_id) != 1:
            print("Warning: too many sensor datas in file")

        # Drop rows with missing coordinates
        valid_coords = df.dropna(subset=['latitude', 'longitude'])
            
        #checks if there are any valid coordinates
        if not valid_coords.empty:
            first_valid = valid_coords.iloc[0]
            lat = first_valid['latitude']
            lon = first_valid['longitude']


            #creates a row for this sensor
            sensor_info = {
                'sensor_id': id,
                'latitude': lat,
                'longitude': lon,
                'season': season,
            }

            all_sensors.append(sensor_info)
        else: 
            print(f"Warning: no valid coordinates in {file}")

if all_sensors:
        
#combines all into a big ol' dataframe
    master_df = pd.DataFrame(all_sensors)

    print(f"Loaded {len(master_df)} sensor-season combinations")
    print("\nFirst few rows:")
    print(master_df.head())
    master_df.to_csv('masterframe.csv')


