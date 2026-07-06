import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt



df = pd.read_csv('masterframe.csv')


coord_pairs = df.drop_duplicates(subset=["sensor_id"])
print(f"Found {len(coord_pairs)} unique sensor locations")
print(coord_pairs.head())

#this is to create the map part
fig, ax = plt.subplots(figsize=(12, 8),subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([-114.5, -109.0, 37.0, 42.0])

#state boundry
ax.add_feature(cfeature.STATES, linewidth=0.8, edgecolor='purple', alpha=0.7)

#map features
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.BORDERS, linewidth=0.5)
ax.add_feature(cfeature.LAKES, facecolor='blue', alpha=0.5)
ax.add_feature(cfeature.RIVERS, linewidth=0.5, edgecolor='blue')

#cities
cities = {'Salt Lake City': (-111.8910, 40.7608), 'Provo': (-111.6581, 40.2338), 'Ogden': (-111.9740, 41.2230)}
for city, (lon, lat) in cities.items():
    ax.plot(lon, lat, '^', color='black', markersize=4, 
            transform=ccrs.PlateCarree(), zorder=10)
    
    ax.text(lon + 0.1, lat + 0.03, city, 
            transform=ccrs.PlateCarree(), 
            fontsize=5,           # Increased from 10
            fontweight='bold',
            color='black',         # Changed to black for contrast
            zorder=6)    
    

scatter = ax.scatter(coord_pairs['longitude'], coord_pairs['latitude'], 
                    c='red', s=5, alpha=0.7, transform=ccrs.PlateCarree())
                 

plt.title(f'Sensor Locations in Utah ({len(coord_pairs)} sensors)', fontsize=14, fontweight='bold')

plt.show()