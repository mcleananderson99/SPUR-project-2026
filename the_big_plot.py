import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path

#creates the function
def seasonal_averages(seasons_list):
    """
    Calculate average PM10 for each sensor in each season
    """
 
    all_seasonal_data = []
    
    for season in seasons_list:
        print(f"Processing {season}....")

        csv_files = Path(season).glob('*.csv')

        for file in csv_files:
            try:
                df = pd.read_csv(file)

                pm10_col = 'opcn3.pm10_cor_k'
                flag_col = 'opcn3.pm10_cor_k_flag'

            
                if pm10_col not in df.columns:
                     print(f"Warning not correct PM10 column found in {file}")
                     continue #continue skips the file
                
                if flag_col in df.columns:
                    df_filtered = df[df[flag_col].isna()]
                    print(f"   Filtered {file.name}: kept {len(df_filtered)} of {len(df)} rows")

                    if df_filtered.empty:
                        print(f"   Warning: all rows are flagged in {file.name}, skipping file")
                        continue

                    df_to_use = df_filtered
                    print(f"   Filtered {file.name}: Kept {len(df_filtered)} of {len(df)} rows")
                else:
                    df_to_use = df
                    print(f"   No Flag columns found in {file.name}, using all data")
                if df_to_use.empty:
                    print(f"   Warning: No data remaining for {file.name}, skipping")
                    continue

                 
                # Calculate statistics
                pm10_data = df_to_use[pm10_col]
                avg_pm10 = pm10_data.mean()
                median_pm10 = pm10_data.median()
                std_pm10 = pm10_data.std()

                if pd.isna(avg_pm10):
                    print(f"  Warning: No valid pm10 values in {file.name}, skipping")
                    continue

                #gives me the sensor ID
                if 'deviceId' in df.columns:
                    sensor_id = df['deviceId'].iloc[0]
                else:
                    sensor_id = file.stem

                #this gets coordinates
                if 'latitude' in df.columns and 'longitude' in df.columns:
                    valid_coords = df_to_use.dropna(subset=['latitude', 'longitude'])
                    if not valid_coords.empty:
                        lat = valid_coords.iloc[0]['latitude']
                        lon = valid_coords.iloc[0]['longitude']
                    else:
                        print(f"Warning: No valid coordinates in {file}")
                        continue #skips file if no valid coordinates
                else:
                    print(f"Warning: No coordinate columns in {file}")
                    continue #Skips file if no coordinate columns

                #Append the data via a dictionary
                all_seasonal_data.append({
                    'sensor_id': sensor_id,
                    'latitude': lat,
                    'longitude': lon,
                    'season': season,
                    'avg_pm10': avg_pm10,
                    'median_pm10': median_pm10,
                    'std_pm10': std_pm10         
                })

                print(f"    Processed {file.name} - Sensor {sensor_id}, PM10: {avg_pm10:.2f}")
            except Exception as e:
                print(f"Error processing {file}: {e}")

        #returns the DataFrame after processing all files
    if all_seasonal_data:
        return pd.DataFrame(all_seasonal_data)
    else:
        print("No data was processed successfully!")
        return pd.DataFrame() #this rerutns empty DataFrame

seasons = ['2024Spring', '2024Summer', '2024Winter', '2025Spring', '2025Summer', '2025Winter']

print("Thinking about the PM10 averages, please be patient friend")

#this will run the function
seasonal_data = seasonal_averages(seasons)

#this checks if we even have the data
if not seasonal_data.empty:
    print(f"\success! processed {len(seasonal_data)} sensor-season combinations")
    print("\nFirst few rows for test:")
    print(seasonal_data.head())

    seasonal_data.to_csv('Clean_PlotData.csv')

    #check unique seasons
    print(f"\Seasons in data: {seasonal_data['season'].unique()}")

    #check on the PM10 range
    print(f"\nPM10range: {seasonal_data['avg_pm10'].min():.2f} - {seasonal_data['avg_pm10'].max():.2f} µg/m³")

#show how many sensors per season
    print("\nSensors per season:")
    print(seasonal_data['season'].value_counts()) 

else:
    print("Nope, no data was processed. Gotta check on them pesky paths and column names")



