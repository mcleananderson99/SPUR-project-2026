import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
from scipy.interpolate import griddata
import matplotlib.colors as colors

seasonal_data = pd.read_csv('Clean_PlotData.csv')
seasons = ['2024Spring', '2024Summer', '2024Winter', '2025Spring', '2025Summer', '2025Winter']
print("="*50)
print("Creating 6 seperate seasonal pm10 maps...")
print("="*50)


#cities
cities = {'Salt Lake City': (-111.8910, 40.7608), 
        'Provo': (-111.6581, 40.2338), 
        'Ogden': (-111.9740, 41.2230),
        'Layton': (-112, 41),
        'American Fork': (-111.8, 40.4),
        'St. George': (-113.5, 37.0),
        'Tooele': (-112.3, 40.5),
        'Tabiona': (-110.71, 40.35),
        'Wendover': (-114.04, 40.74),
        

}

#calc for state min/max
state_min = seasonal_data['avg_pm10'].min()
state_max = seasonal_data['avg_pm10'].max()
print(f"State PM10 range for consistent coloring: {state_min:.2f} - {state_max:.2f} µg/m³")

grid_resolution = 500

xmin, xmax = -114.5, -109.0
ymin, ymax =  37.0, 42.0

for season in seasons:
    season_df = seasonal_data[seasonal_data['season'] == season]

    if season_df.empty:
        print(f"No data available for {season}, skipping...")
        continue

    print(f"\nCreating map for {season} with {len(season_df)} sensors...")

    #creates the figure and axis
    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([-114.5, -109.0, 37.0, 42.0])

    ax.add_feature(cfeature.STATES, linewidth=0.8, edgecolor='purple', alpha=0.7)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAKES, facecolor='blue', alpha=0.5)
    ax.add_feature(cfeature.RIVERS, linewidth=0.5, edgecolor='blue', alpha=0.5)

    #gets the coords and values
    lons = season_df['longitude'].values
    lats = season_df['latitude'].values
    values = season_df['avg_pm10'].values

    #creates a grid for interpolation
    grid_x = np.linspace(xmin, xmax, grid_resolution) 
    grid_y = np.linspace(ymin, ymax, grid_resolution)

    grid_X, grid_Y = np.meshgrid(grid_x, grid_y)

    #interpolate the data into the grid
    grid_Z = griddata(
        (lons, lats),
        values,
        (grid_X, grid_Y),
        method='cubic'  #either cubic for smooth, or linear for fast
    )

    heatmap = ax.pcolormesh(
        grid_X, grid_Y, grid_Z,
        cmap='YlOrRd', alpha=0.7, transform=ccrs.PlateCarree(),
        vmin=state_min, vmax=state_max, shading='auto'

    )
    contourf = ax.contourf(
        grid_X, grid_Y, grid_Z,
        levels=10, colors='black', linewidths=0.5,
        alpha=0.3, transform=ccrs.PlateCarree()
    )
    ax.clabel(contourf, inline=True, fontsize=8, fmt='%.1f')
    
    for city, (lon, lat) in cities.items():
        ax.text(lon, lat, city,
               transform=ccrs.PlateCarree(),
               fontsize=8,
               fontweight='bold',
               color='#2c2c2c',
               zorder=6, bbox=dict(
                   boxstyle="round,pad=0.3",
                   facecolor='white',
                   edgecolor='gray',
                   alpha=0.85,
                   linewidth=0.5
               ))
        
    cbar = plt.colorbar(heatmap, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
    cbar.set_label('Average PM10 (µg/m³)', fontsize=11, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)

    season_display = season.replace('2024', '2024 ').replace('2025', '2025 ')

    plt.title(f'{season_display} - PM10 Distribution in Northern Utah\n(n={len(season_df)} sensors)', 
              fontsize=14, fontweight='bold', pad=20)
    
    season_min = season_df['avg_pm10'].min()
    season_max = season_df['avg_pm10'].max()
    season_mean = season_df['avg_pm10'].mean()
    plt.figtext(0.5, 0.02, 
                f'Range: {season_min:.2f} - {season_max:.2f} µg/m³ | Mean: {season_mean:.2f} µg/m³', 
                ha='center', fontsize=10, style='italic', color = '#444444')
    
    plt.tight_layout()
    plt.show()
