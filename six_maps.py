import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
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

state_std_min = seasonal_data['std_pm10'].min()
state_std_max = seasonal_data['std_pm10'].max()
print(f"State Std Dev range: {state_std_min:.2f} - {state_std_max:.2f} µg/m³")

base_size_min = 20 #smallest bubble size
base_size_max = 150 #biggest bubble size

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
    std_values = season_df['std_pm10'].values

    if state_std_max > state_std_min:
        std_normalized = (std_values - state_std_min) / (state_std_max - state_std_min)
        bubble_sizes = base_size_min + std_normalized * (base_size_max - base_size_min)
    else:
        bubble_sizes = np.full_like(std_values, (base_size_min + base_size_max) / 2)

    scatter = ax.scatter(
        lons, lats,
        c=values,
        s=bubble_sizes,
        cmap='coolwarm',
        alpha=0.7,
        transform=ccrs.PlateCarree(),
        vmin=state_min,
        vmax=state_max,
        edgecolors='black',
        linewidth=0.5,
        zorder=5
    )
    
    for city, (lon, lat) in cities.items():
        if -114.5 <= lon <= -109.0 and 37.0 <= lat <= 42.0:
            ax.text(lon, lat, city,
               transform=ccrs.PlateCarree(),
               fontsize=6,
               fontweight='normal',
               color='#444444',
               alpha=0.5,
               zorder=6, bbox=dict(
                   boxstyle="round,pad=0.1",
                   facecolor='white',
                   edgecolor='none',
                   alpha=0.6,
                   linewidth=0
               ))
        
    cbar = plt.colorbar(scatter, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
    cbar.set_label('Average PM10 (µg/m³)', fontsize=11, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)

    from matplotlib.lines import Line2D
    legend_elements = []

    sd_levels = [state_std_min, state_std_min + (state_std_max - state_std_min)
                 * 0.25,
                 state_std_min + (state_std_max - state_std_min) * 0.5,
                 state_std_min + (state_std_max - state_std_min) * 0.75,
                 state_std_max]
    for sd_level in sd_levels:
        if state_std_max > state_std_min:
            norm_sd = (sd_level - state_std_min) / (state_std_max - state_std_min)
            size = base_size_min + norm_sd * (base_size_max - base_size_min)
        else:
            size = (base_size_min + base_size_max) / 2
        legend_elements.append(
            Line2D([0], [0], marker='o', color='w',
                   label=f'SD: {sd_level:.1f}',
                   markerfacecolor='gray',
                   markersize=np.sqrt(size) / 2,
                   alpha=0.7,
                   markeredgecolor='black')
        )
    ax2 = ax.inset_axes([0.02, 0.02, 0.2, 0.15]) #[x,y,width, hight]
    ax2.axis('off')
    ax2.legend(handles=legend_elements, loc='center',
               title='Standard Devation\n(Bubble size)',
               fontsize=8, title_fontsize=9)
    
    sd_text = f"Bubble size represents Standard Deviation\n"
    sd_text += f"Range: {state_std_min:.1f} - {state_std_max:.1f} µg/m³"

    ax.text(0.98, 0.02, sd_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle="round,pad=0.4",
                      facecolor='white',
                      edgecolor='gray',
                      alpha=0.85))

    season_display = season.replace('2024', '2024 ').replace('2025', '2025 ')

    plt.title(f'{season_display} - PM10 Distribution in Northern Utah\n(n={len(season_df)} sensors)', 
              fontsize=14, fontweight='bold', pad=20)
    
    season_min = season_df['avg_pm10'].min()
    season_max = season_df['avg_pm10'].max()
    season_mean = season_df['avg_pm10'].mean()
    season_std_mean = season_df['std_pm10'].mean()

    plt.figtext(
        0.5, 0.02,
        f'PM10 Range: {season_min:.2f} - {season_max:.2f} µg/m³ | '
        f'Mean: {season_mean:.2f} µg/m³ | '
        f'Mean SD: {season_std_mean:.2f} µg/m³',
        ha='center',
        fontsize=10,
        style='italic',
        color='#444444')
    plt.tight_layout()
    plt.show()

    #stats
print("\n" + "="*50)
print("SUMMARY STATISTICS")
print("="*50)
for season in seasons:
    season_df = seasonal_data[seasonal_data['season'] == season]
    if not season_df.empty:
        print(f"\n{season}:")
        print(f"  Sensors: {len(season_df)}")
        print(f"  PM10 Mean: {season_df['avg_pm10'].mean():.2f} µg/m³")
        print(f"  PM10 Range: {season_df['avg_pm10'].min():.2f} - {season_df['avg_pm10'].max():.2f} µg/m³")
        print(f"  Std Dev Mean: {season_df['std_pm10'].mean():.2f} µg/m³")
        print(f"  Std Dev Range: {season_df['std_pm10'].min():.2f} - {season_df['std_pm10'].max():.2f} µg/m³")    
