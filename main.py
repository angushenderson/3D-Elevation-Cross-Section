import ElevationPlot.data_manager as manager
import ElevationPlot.plot as plot


if (coords := manager.load_data('mt_st_helens')):
    print('Loading saved data')
    X, Y, Z = coords
else:
    print('No data saved, calling API')
    # Fetch data
    X, Y, Z = manager.API_call('around', center_coords=(46.1914, -122.1956),
                               horizontal_data_points=50, vertical_data_points=50, width=0.075, height=0.075)
    # Store data
    manager.store_plot(X, Y, Z, 'mt_st_helens')

# Plot
plot.elevation_plot(X, Y, Z)
