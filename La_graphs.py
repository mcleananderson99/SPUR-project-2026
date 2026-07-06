import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.dates as mdates

def load_and_filter_sensor_data(file_path):
    """
    Load CSV files for PM10 sensors and filter out flagged rows
    """
    try:
        df = pd.read_csv(file_path)

        pm10_col = 'opcn3.pm10_cor_k'
        pm25_col = 'pms5003t.pm2_5_cf_cor_r'


        if pm10_col not in df.columns:
            print(f"   Skipping {file_path.name}: No PM10 column")
            return None, None, None
        
        if pm25_col not in df.columns:
            print(f"   Skipping {file_path.name}: No PM2.5 column")
            return None, None, None
        
        
        flag_col = 'opcn3.pm10_cor_k_flag'

        df_filtered = df.copy()

        if flag_col in df.columns:
            df_filtered = df_filtered[df_filtered[flag_col].isna()]

        df_filtered = df_filtered.dropna(subset=[pm10_col, pm25_col])

        if df_filtered.empty:
            print(f"  Skipping {file_path.name}: All rows flagged")
            return None, None, None
        
        if 'deviceId' in df.columns:
            sensor_id = df['deviceId'].iloc[0]
        else:
            sensor_id = file_path.stem

        if 'latitude' in df.columns and 'longitude' in df.columns:
            valid_coords = df_filtered.dropna(subset=['latitude', 'longitude'])
            if not valid_coords.empty:
                lat = valid_coords.iloc[0]['latitude']
                lon = valid_coords.iloc[0]['longitude']
            else:
                print(f"   Skipping {file_path.name}: No valid Coordinates")
                return None, None, None
        else:
            print(f"   Skipping {file_path.name}: No coordinate columns")
            return None, None, None
        
        df_filtered['sensor_id'] = sensor_id
        df_filtered['latitude'] = lat
        df_filtered['longitude'] = lon
        df_filtered['pm10'] = df_filtered[pm10_col]
        df_filtered['pm25'] = df_filtered[pm25_col]
        df_filtered['coarse_pm'] = df_filtered['pm10'] - df_filtered['pm25']
        df_filtered['pm10_raw'] = df_filtered[pm10_col]
        df_filtered['pm25_raw'] = df_filtered[pm25_col]

        if 'DateTime_UTC' in df_filtered.columns:
            df_filtered['DateTime_UTC'] = pd.to_datetime(df_filtered['DateTime_UTC'])

        return df_filtered, sensor_id, (lat, lon)
    
    except Exception as e:
        print(f"   Error loading {file_path.name}: {e}")
        return None, None, None
    

def load_season_data(season_folder):
    """
    Load all sensor data for a season, Automatically filter PM10 sensors and flagged rows
    """
    print(f"\nLoading {season_folder}...")
    sensor_data = {}
    sensor_locations = {}

    csv_files = list(Path(season_folder).glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files")

    for file in csv_files:
        df, sensor_id, coords = load_and_filter_sensor_data(file)

        if df is not None and sensor_id is not None:
            sensor_data[sensor_id] = df
            sensor_locations[sensor_id] = coords
            print(f"   Loaded sensor {sensor_id}: {len(df)} valid rows")

    print(f"Loaded {len(sensor_data)} valid PM sensors")
    return sensor_data, sensor_locations

def load_full_dataset(season_list):
    """
    Load data from all seasons and combine into a singel continous dataset
    """
    print("\n" + "="*59)
    print("LOADING FULL 2-YEAR DATASET")
    print("="*59)

    all_sensor_data = {}
    all_sensor_locations = {}

    for season in season_list:
        sensor_data, sensor_locations = load_season_data(season)

        #merge da data
        for sensor_id, df in sensor_data.items():
            if sensor_id not in all_sensor_data:
                all_sensor_data[sensor_id] = []
            all_sensor_data[sensor_id].append(df)

        all_sensor_locations.update(sensor_locations)

    combined_data = {}
    for sensor_id, df_list in all_sensor_data.items():
        combined_data[sensor_id] = pd.concat(df_list, ignore_index=True)

        if 'DateTime_UTC' in combined_data[sensor_id].columns:
            combined_data[sensor_id] = combined_data[sensor_id].sort_values('DateTime_UTC')
    
    print(f"\nLoaded {len(combined_data)} sensors across all seasons")
    return combined_data, all_sensor_locations

def assign_city_by_coordinates(lat, lon):
    """
    Assign a city based on coordinates
    uses a sor t of box for major cities in Utah
    """

    #define city boundaries
    city_boundaries = {
        'Salt Lake City': {
            'lat_range': (40.5, 40.9),
            'lon_range': (-112.1, -111.6)
    },  
        'Ogden': {
            'lat_range': (41, 42),
            'lon_range': (-112.3, -111.4)
    },
        'Provo': {
            'lat_range': (39.8, 40.49),
            'lon_range': (-112.1, -111.5)
        },
        'St. George': {
            'lat_range': (37.0, 38.3),
            'lon_range': (-114.05, -111.85)
        },
        'Tooele': {
            'lat_range': (40.35, 40.7),
            'lon_range': (-112.7, -112.09)
        },
        'Tabiona': {
            'lat_range': (40, 40.5),
            'lon_range': (-111, -110)
        },
        'Wendover': {
            'lat_range': (40.5, 40.8),
            'lon_range': (-114.2, -113.7)
        }
        
    }
    for city, bounds in city_boundaries.items():
        if (bounds['lat_range'][0] <= lat <= bounds['lat_range'][1] and
            bounds['lon_range'][0] <= lon <= bounds['lon_range'][1]):
            return city
    return 'Other'
def group_sensors_by_city(sensor_locations):
    """
    Group sensors by city based on their coordinates
    """    
    city_groups = {}

    for sensor_id, (lat, lon) in sensor_locations.items():
        city = assign_city_by_coordinates(lat, lon)
        if city not in city_groups:
            city_groups[city] = []
        city_groups[city].append(sensor_id)

    return city_groups

def create_continuous_city_graph(city_name, 
                           sensor_ids, sensor_data, 
                           time_col='DateTime_UTC', 
                           pm_col='coarse_pm',
                           y_label='Coarse PM (µg/m³)',
                           title_prefix='Coarse PM', 
                           save_path = None,
                           show_stats=True,
                           show_pm10_comparison=False):
    """
    create an area graph showing multiple sensors for a specific city
    for the 2 continuous years
    """

    if not sensor_ids:
        print(f"No sensors found for {city_name}")
        return
    
    print(f"\nCreating continuous 2-year area graph for {city_name} with {len(sensor_ids)} sensors...")

    #this filters for sensors with data
    valid_sensors = [s_id for s_id in sensor_ids if s_id in sensor_data]

    if not valid_sensors:
        print(f"No data available for any sensor in {city_name}")
        return
    
    if time_col not in sensor_data[valid_sensors[0]].columns:
        print(f"Warning: '{time_col}' column not found. Trying alternatives...")
        possible_time_cols = ['DateTime_UTC', 'timestamp', 'datetime', 'time', 'date', 'created_at']
        for col in possible_time_cols:
            if col in sensor_data[valid_sensors[0]].columns:
                time_col = col
                print(f"   Using '{time_col}' instead")
                break
        else:
            print(f"No time column found for {city_name}")
            return

    fig, ax = plt.subplots(figsize=(16, 8))

    colors = plt.cm.tab10(np.linspace(0, 1, len(valid_sensors)))
    sensor_stats = {}

    for idx, sensor_id in enumerate(valid_sensors):
        df = sensor_data[sensor_id].copy()

        df[time_col] = pd.to_datetime(df[time_col])
        df = df.sort_values(time_col)

        sensor_stats[sensor_id] = {
            'mean': df[pm_col].mean(),
            'median': df[pm_col].median(),
            'min': df[pm_col].min(),
            'max': df[pm_col].max(),
            'count': len(df)
        }

        ax.plot(df[time_col], df[pm_col],
                linewidth=1.5,
                alpha=0.7,
                color=colors[idx],
                label=f'Sensor {sensor_id[:12]}...' if len(sensor_id) > 12 else f'Sensor {sensor_id}')
        
        if show_pm10_comparison and idx == 0:
            ax.plot(df[time_col], df['pm10'],
                    linewidth=0.5, alpha=0.2, color='red', linestyle='--',
                    label='PM10 (ref)')
            ax.plot(df[time_col], df['pm25'],
                    linewidth=0.5, alpha=0.2, color='blue', linestyle='--',
                    label='PM2.5 (ref)')
        

    all_values = []
    for sensor_id in valid_sensors:
        all_values.extend(sensor_data[sensor_id][pm_col].values)
    overall_mean = np.mean(all_values)


    ax.axhline(y=overall_mean, color='red',linestyle='--',
                   linewidth=2, label=f'Overall Mean: {overall_mean:.2f}')
    
    season_boundaries = [
        datetime(2024, 3, 20),  # Spring 2024
        datetime(2024, 6, 20),  # Summer 2024
        datetime(2024, 9, 22),  # Fall 2024
        datetime(2024, 12, 21), # Winter 2024
        datetime(2025, 3, 20),  # Spring 2025
        datetime(2025, 6, 20),  # Summer 2025
        datetime(2025, 9, 22),  # Fall 2025
        datetime(2025, 12, 21), # Winter 2025
    ]

    for boundary in season_boundaries:
        ax.axvline(x=boundary, color='gray', linestyle=':', alpha=0.5, linewidth=1)

    ax.set_xlabel('Date/Time', fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12, fontweight='bold')

    
    ax.set_title(f'{city_name} - 2-Year {title_prefix} Data\n'
                     f'{len(valid_sensors)} sensors | {len(all_values)} total observations',
                     fontsize=14, fontweight='bold')
        
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    if show_stats:
        stats_text = "Sensor Statistics:\n"
        stats_text += "-" * 20 + "\n"
        for sensor_id, stats in sensor_stats.items():
            short_id = sensor_id[:12] + '...' if len(sensor_id) > 12 else sensor_id
            stats_text += f"{short_id}:\n"
            stats_text += f"   Mean: {stats['mean']:.2f}\n"
            stats_text += f"   Range: {stats['min']:.1f} - {stats['max']:.1f}\n"
    
        stats_text += "-" * 20 + "\n"
        stats_text += f"Overall Mean: {overall_mean:.2f}"

        ax.text(0.98, 0.98, stats_text,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor='white',
                          alpha=0.9,
                          edgecolor='gray'))
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {save_path}")

    plt.show()
    return sensor_stats


def create_all_continuous_city_graphs(season_folder, save_dir=None, pm_type='coarse_pm'):
    """
    Creates continuous 2-year graphs for all cities
    """
    print(f"\n{'='*60}")
    print(f"Creating city area graphs for {season_folder}")
    print(f"PM Type: {pm_type}")
    print(f"{'='*60}")

    sensor_data, sensor_locations = load_full_dataset(season_folder)

    if not sensor_data:
        print(f"No valid data found for {season_folder}")
        return
    
    city_groups = group_sensors_by_city(sensor_locations)

    print(f"\nCity sensor distribution:")
    for city, sensors in sorted(city_groups.items()):
        if city != 'Other':
            print(f"   {city}: {len(sensors)} sensors")
    if 'Other' in city_groups:
        print(f"   Other: {len(city_groups['Other'])} sensors")

    pm_labels = {
        'coarse_pm': ('Coarse PM (µg/m³)', 'Coarse PM'),
        'pm10': ('PM10 (µg/m³)', 'PM10'),
        'pm25': ('PM2.5 (µg/m³)', 'PM2.5')
    }
    y_label, title_prefix = pm_labels.get(pm_type, ('PM (µg/m³)', 'PM'))

    for city, sensors in city_groups.items():
        if city != 'Other' and sensors:
            save_path = None
            if save_dir:
                save_path = Path(save_dir) / f"2Year_{city.replace(' ','_')}.png"
            create_continuous_city_graph(city, sensors, sensor_data, save_path=save_path)

    return sensor_data, sensor_locations, city_groups

def create_continuous_combined_city_comparison(season_folder, save_path=None,
                                               pm_type='coarse_pm'):
    """
    Create a combined figure showing area graphs for all cities side by side
    """
    print(f"\nCreating combined city comparison for {pm_type}")
    
    sensor_data, sensor_locations = load_full_dataset(season_folder)

    if not sensor_data:
        print(f"No valid data found for {season_folder}")
        return
    
    city_groups = group_sensors_by_city(sensor_locations)

    cities_with_sensors = {city: sensors for city, sensors in city_groups.items()
                           if sensors and city != 'Other'}
    if not cities_with_sensors:
        print("No sensors found for any city")
        return
    
    n_cities = len(cities_with_sensors)
    fig, axes = plt.subplots(1, n_cities, figsize=(7*n_cities, 8))
    if n_cities == 1:
        axes = [axes]

    time_col = 'DateTime_UTC'

    pm_labels = {
        'coarse_pm': ('Coarse PM (µg/m³)', 'Coarse PM'),
        'pm10': ('PM10 (µg/m³)', 'PM10'),
        'pm25': ('PM2.5 (µg/m³)', 'PM2.5')
    }
    y_label, title_prefix = pm_labels.get(pm_type, ('PM (µg/m³)', 'PM'))

    for idx, (city_name, sensor_ids) in enumerate(cities_with_sensors.items()):
        ax = axes[idx]

        valid_sensors = [s_id for s_id in sensor_ids if s_id in sensor_data]

        if not valid_sensors:
            ax.text(0.5, 0.5, f'No data for {city_name}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title(city_name)
            continue

        if time_col not in sensor_data[valid_sensors[0]].columns:
            possible_time_cols = ['DateTime_UTC', 'timestamp', 'datetime', 'time', 'date', 'created_at']
            for col in possible_time_cols:
                if col in sensor_data[valid_sensors[0]].columns:
                    time_col = col
                    break



        colors = plt.cm.tab10(np.linspace(0, 1, len(valid_sensors)))

        for i, sensor_id in enumerate(valid_sensors):
            df = sensor_data[sensor_id].copy()
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col)

            ax.plot(df[time_col], df['pm_type'],
                    linewidth=1.5,
                    alpha=0.7,
                    color=colors[i],
                    label=f'Sensor {sensor_id[:8]}...')
        ax.set_xlabel('Date/Time', fontsize=10)
        ax.set_ylabel(y_label, fontsize=10)
        ax.set_title(f'{city_name}\n({len(valid_sensors)} sensors)',
                     fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        if idx == 0:
            ax.legend(loc='upper left', fontsize=7)

    plt.suptitle(f'2-Year {title_prefix} - City Comparison',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved comparison plot to {save_path}")

    plt.show()

#============ Main execution zone ============

if __name__ == "__main__":
    seasons = ['2024Spring', '2024Summer', '2024Winter', 
               '2025Spring', '2025Summer', '2025Winter']
    
    print("="*60)
    print("PM10 2-YEAR CONTINUOUS SENSOR GRAPH GENERATOR")
    print("="*60)
    print("This will create continuous 2-year graphs instead of seasonal ones")
    print("Time Column: DateTime_UTC (Year-Month-Day Hour)")
    print("="*60)


    PM_TYPE = 'coarse_pm'

    print(f"\nCreating continuous 2-year graph for all cities...")
    print(f"Plotting: {PM_TYPE}")

    create_all_continuous_city_graphs(seasons, pm_type=PM_TYPE)