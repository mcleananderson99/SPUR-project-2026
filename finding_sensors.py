"""
using this to find the locations of sensors
"""

import pandas as pd
import numpy as np
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    GEOCODING_AVAILABLE = True
except ImportError:
    print("Warning: geopy not installed correctly, gotta rety champ")
    GEOCODING_AVAILABLE = False

def load_sensor_locations_from_season(season_folder):
    """
    Load all sensor locations form a season folder
    Returns a dictionary of {sensor_id: (lat, lon)}
    """
    sensor_locations = {}
    csv_files = list(Path(season_folder).glob('*.csv'))

    print(f"   Scanning {len(csv_files)} files in {season_folder}...")

    for file in csv_files:
        try:
            df = pd.read_csv(file)
            
            if 'opcn3.pm10_cor_k' not in df.columns:
                continue

            if 'deviceId' in df.columns:
                sensor_id = df['deviceId'].iloc[0]
            else:
                sensor_id = file.stem

            if 'latitude' in df.columns and 'longitude' in df.columns:
                valid_coords = df.dropna(subset=['latitude', 'longitude'])
                if not valid_coords.empty:
                    lat = valid_coords.iloc[0]['latitude']
                    lon = valid_coords.iloc[0]['longitude']
                    sensor_locations[sensor_id] = (lat, lon)

        except Exception as e:
            print(f"   Error loading {file.name}: {e}")

    return sensor_locations

def load_all_sensor_locations(seasons_list):
    """
    Load sensor locations from all seasons
    """

    all_locations = {}
    for season in seasons_list:
        print(f"\nProcessing {season}...")
        season_locations = load_sensor_locations_from_season(season)
        all_locations.update(season_locations)
        print(f"   Found {len(season_locations)} sensors in {season}")

    return all_locations

def setup_geocoder():
    """
    Seting up the geocoder with rate limiting 
    """

    if not GEOCODING_AVAILABLE:
        return None
    
    geolocator = Nominatim(user_agent="pm10_sensor_analyzer")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    return geocode

def get_city_from_coordinates(geocode, lat, lon, retry_count=2):
    """
    Get city name from coords using uno reverso geocoding
    """

    if geocode is None:
        return 'Unknown'
    
    for attempt in range(retry_count):
        try:
            location = geocode((lat, lon), language='en')

            if location:
                address = location.raw.get('address', {})

                city = address.get('city')
                if not city:
                    city = address.get('town')
                if not city:
                    city = address.get('village')
                if not city:
                    city = address.get('hamlet')
                if not city:
                    city = address.get('county')
                    if city:
                        city = city.replace('County', '')

                return city if city else 'Unkown'
            return 'Unknown'
        except Exception as e:
            if attempt < retry_count - 1:
                print(f"   Retry {attempt + 1}/{retry_count} for ({lat:.4f}, {lon:.4f})")
                time.sleep(2)
            else:
                print(f"   Error geocoding ({lat:.4f}, {lon:.4f}): {e}")
                return 'Unknown'
        

def check_predefined_city(lat, lon):
    """
    check if coords fall within predefined city boundaries
    """

    city_boundaries = {
        'Salt Lake City': {
            'lat_range': (40.6, 40.9),
            'lon_range': (-112.0, -111.8)
        },  
        'Ogden': {
            'lat_range': (41.1, 41.3),
            'lon_range': (-112.1, -111.9)
        },
        'Provo': {
            'lat_range': (40.1, 40.3),
            'lon_range': (-111.7, -111.6)
        },
        'Logan': {
            'lat_range': (41.7, 41.8),
            'lon_range': (-111.9, -111.8)
        },
        'West Valley City': {
            'lat_range': (40.65, 40.75),
            'lon_range': (-112.05, -111.95)
        },
        'Sandy': {
            'lat_range': (40.55, 40.6),
            'lon_range': (-111.9, -111.8)
        },
        'Layton': {
            'lat_range': (41.0, 41.1),
            'lon_range': (-112.0, -111.9)
        },
        'American Fork': {
            'lat_range': (40.35, 40.4),
            'lon_range': (-111.8, -111.7)
        },
        'Park City': {
            'lat_range': (40.6, 40.7),
            'lon_range': (-111.5, -111.4)
        },
        'Vernal': {
            'lat_range': (40.4, 40.5),
            'lon_range': (-109.6, -109.5)
        },
        'Price': {
            'lat_range': (39.5, 39.7),
            'lon_range': (-110.9, -110.7)
        }
    }

    for city, bounds in city_boundaries.items():
        if (bounds['lat_range'][0] <= lat <= bounds['lat_range'][1] and
            bounds['lon_range'][0] <= lon <= bounds['lon_range'][1]):
            return city
    return None


def analyze_sensor_cities(sensor_locations, use_geocoding=True):
    """
    Analyze all sensor locations and identify their cities
    """
    print("\n" + "="*60)
    print("ANALYZING SENSOR LOCATIONS")
    print("="*60)
    
    # Setup geocoder
    geocode = setup_geocoder() if use_geocoding else None
    
    if use_geocoding and geocode is None:
        print("Geocoding not available. Running in predefined mode only.")
        use_geocoding = False
    
    # Process each sensor
    city_counts = {}
    city_sensors = {}
    unknown_sensors = []
    processed = 0
    
    print(f"\nProcessing {len(sensor_locations)} sensors...")
    print("-" * 60)
    
    for sensor_id, (lat, lon) in sensor_locations.items():
        processed += 1
        
        if processed % 10 == 0:
            print(f"   Progress: {processed}/{len(sensor_locations)} sensors")
        
        # First check predefined cities
        city = check_predefined_city(lat, lon)
        
        # If not found and geocoding is enabled, use geocoding
        if city is None and use_geocoding and geocode is not None:
            city = get_city_from_coordinates(geocode, lat, lon)
        
        # If still not found, mark as unknown
        if city is None:
            city = 'Unknown'
            unknown_sensors.append((sensor_id, lat, lon))
        
        # Track city counts
        if city not in city_counts:
            city_counts[city] = 0
            city_sensors[city] = []
        city_counts[city] += 1
        city_sensors[city].append(sensor_id)
    
    return city_counts, city_sensors, unknown_sensors

def save_results(city_counts, city_sensor, unknown_sensors,
                 output_dir='city_analysis'):
    """
    Save analysis results to files
    """
    
    Path(output_dir).mkdir(exist_ok=True)

    city_counts_df = pd.DataFrame([
        {'city': city, 'sensor_count': count}
        for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True)
    ])
    
    city_counts_df.to_csv(f'{output_dir}/city_sensor_counts.csv', index=False)
    print(f"\nSaved city counts to {output_dir}/city_sensor_counts.csv")

    city_sensors_df = pd.DataFrame([
        {'city': city, 'sensor_id': sensor_id}
        for city, sensors in city_sensors.items()
        for sensor_id in sensors 
    ])

    city_sensors_df.to_csv(f'{output_dir}/sensors_by_city.csv', index=False)
    print(f"Saved sensor list by city to {output_dir}/sensors_by_city.csv")

    if unknown_sensors:
        unknown_df = pd.DataFrame([
            {'sensor_id': sensor_id, 'latitude': lat, 'longitude': lon}
            for sensor_id, lat, lon in unknown_sensors
        ])
        unknown_df.to_csv(f'{output_dir}/unknown_sensors.csv', index=False)
        print(f"Saved {len(unknown_sensors)} unknown sensors to {output_dir}/unknown_sensors.csv")

    
def print_summary(city_counts, unknown_sensors):
    """
    Print a summary of the anaylsis
    """

    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)

    total_sensors = sum(city_counts.values())
    known_cities = [c for c in city_counts.keys() if c != 'Unknown']

    print(f"\nTotal sensors analyzed: {total_sensors}")
    print(f"Total cities found: {len(known_cities)}")
    print(f"Cities: {',' .join(sorted(known_cities))}")

    print("\nCity breakdown:")
    print("-" * 59)
    for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
        if city != 'Unknown':
            percentage = (count / total_sensors) * 100
            print(f"   {city}: {count} sensors ({percentage:.1f}%)")

    if unknown_sensors:
        print(f"\nWarning {len(unknown_sensors)} sensors in UNKNOWN locations! AAAAHHHH!")
        print("These sensors couldn't be assigned to any city.")
        print("\nCheck 'unknown_sensors.csv' for their coordinates")
        print("You can use these coordinates to add new cities to your boundaries")


def generate_city_updates(city_counts, unknown_sensors):
    """
    Generate suggestions for updating the city boundaries
    """

    if not unknown_sensors:
        print("\n All sensors have been assigned to cities")
        print("No new cities to discover.")

    print("\n" + "="*60)
    print("CITY BOUNDARY UPDATE SUGGESTIONS")
    print("="*60)

    print("\nYou have sensors in unknown locations.")
    print("To discover these cities, check the coordinates in 'unknown_sensors.csv'")
    print("\nYou can manually look up these coordinates to find the city names,")
    print("or run this script again with geocoding enabled.")
    
    print("\nTo add new cities to your graphing code, update your CITY_BOUNDARIES with:")
    print("-" * 59)
   
if __name__ == "__main__":
    seasons = ['2024Spring', '2024Summer', '2024Winter', 
               '2025Spring', '2025Summer', '2025Winter']
    
    print("="*59)
    print("PM10 SENSOR CITY ANALYZER")
    print("="*59)

    print("\nLoading sensor locations form all seasons...")
    all_locations = load_all_sensor_locations(seasons)

    print(f"\nTotal unique sensors found: {len(all_locations)}")
    print("\nGeocoding requires internet connection and might take a bit")
    print("It should identify cities for sensors outside of the predifined boundaries")
    use_geocoding = input("Use geocoding? (y/n): ").lower() =='y'

    city_counts, city_sensors, unknown_sensors = analyze_sensor_cities(all_locations, use_geocoding=use_geocoding)

    print_summary(city_counts, unknown_sensors)

    save_results(city_counts, city_sensors, unknown_sensors)

    generate_city_updates(city_counts, unknown_sensors)

    print("\n" + "="*60)
    print("CITY INDEX FOR YOUR GRAPHING CODE")
    print("="*60)

    known_cities = [c for c in city_counts.keys() if c != 'Unknown']
    print("\nCopy this list to your graphing code:")
    print("-" * 60)
    print("# All cities with sensors:")
    print(f"CITIES = {known_cities}")
    print(f"# Total: {len(known_cities)} cities, {sum(city_counts.values())} sensors")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. Check 'city_analysis/city_sensor_counts.csv' - see all cities and how many sensors
2. Check 'city_analysis/sensors_by_city.csv' - see which sensors are in which city
3. If there are unknown sensors:
   - Check 'city_analysis/unknown_sensors.csv' for their coordinates
   - Look up these coordinates to find the city names
   - Add new cities to your graphing code's CITY_BOUNDARIES
4. Update your graphing code with the new cities found
5. Use the city list above to update your graphing functions
    """)