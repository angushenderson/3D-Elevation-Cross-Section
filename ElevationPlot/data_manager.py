import requests
import numpy as np
import time
import csv
import os
import pathlib
from .progress_bar import printProgressBar


BASE_URL = 'https://api.opentopodata.org/v1/srtm90m?locations='
RETRIES = 10
CSV_HEADER = ['Lat(X)', 'Lng(Y)', 'Elevation(Z)']
MODES = ['from_to', 'around']


def store_plot(X: list, Y: list, Z: list, plot_name: str, overwrite=True) -> bool:
    """
    Store points for loading a future time without having to call API
    :param X, Y, Z list: X, Y and Z coodinates of points to plot
    :param plot_name str: Name of plot -> What to call when reopen the data
    :param overwrite bool: if True then any file with same name will be overwriten,
            if False then the file won't be changed if the file already exists. Default -> True
    :return bool: True if completed successfully, False if not
    """
    path = f'{pathlib.Path(__file__).parent.absolute()}/data/{plot_name}.csv'
    if len(X) == len(Y) == len(Z):
        if overwrite or not os.path.isfile(path):
            with open(path, 'w', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(CSV_HEADER)
                for i in range(len(X)):
                    csv_writer.writerow([X[i], Y[i], Z[i]])
            return True
    return False


def load_data(plot_name: str) -> (list, list, list):
    """
    Load data previously stored by module on local storage
    :param plot_name str: Name of plot to load
    :return x, y, z: List of points ready to plot, None if can't open file
    """
    x, y, z = [], [], []
    path = f'{pathlib.Path(__file__).parent.absolute()}/data/{plot_name}.csv'
    if os.path.isfile(path):
        with open(path, 'r', newline='') as file:
            csv_reader = csv.reader(file, delimiter=',')
            for index, row in enumerate(csv_reader):
                if index > 0:
                    x.append(float(row[0]))
                    y.append(float(row[1]))
                    z.append(float(row[2]))
        return x, y, z
    else:
        return None


def API_call(mode: str, **kwargs) -> (list, list, list):
    """ 
    Function to format data for api request
    :param from_coords tuple(float, float): Coordinate location of where to map from
    :param to_coords tuple(float, float): Coordinate location of where to map to
    :param center_coords tuple(float, float): Coordinate location of where to plot around -> For around plot
    :param horizontal_data_points int: Number of points to get elevation for horizontally (x)
    :param vertical_data_points int: Number of points to get elevation for vertically (y)
    :param width float: Width to plot, coordinate degree, for around plot
    :param height float: Height to plot, coordinate degree, for around plot
    :return X, Y, Z list: List of points ready to plot
    """
    if mode in MODES:
        if mode == MODES[0]:
            # Format input for from, to plot
            formatted_coords = fetch_format_from_to(
                kwargs['from_coords'], kwargs['to_coords'], kwargs['horizontal_data_points'], kwargs['vertical_data_points'])
        else:
            # Format input for around plot
            formatted_coords = fetch_format_around(
                kwargs['center_coords'], kwargs['horizontal_data_points'], kwargs['vertical_data_points'], kwargs['width'], kwargs['height'])
        # Fetch data from API
        response = fetch(formatted_coords)
        # Format data for plotting
        X, Y, Z = plot_format(response)
        return X, Y, Z
    else:
        raise ValueError(f"Please select a mode from MODES: {str(MODES)}")


def plot_format(response: list) -> (list, list, list):
    """
    Function to format data for trisurf plot
    :param response list: List of API responses, get by calling fetch()
    :return x, y, z list: List of X, Y and Z values to pass into plot function
    """
    x, y, z = [], [], []
    for r in response:
        x.append(r['location']['lat'])
        y.append(r['location']['lng'])
        z.append(r['elevation'])
    return x, y, z


def fetch_format_from_to(from_coords: tuple, to_coords: tuple, horizontal_data_points: int, vertical_data_points: int) -> (list, int, int):
    """ 
    Function to format data for api request
    :param from_coords tuple(float, float): Coordinate location of where to map from
    :param to_coords tuple(float, float): Coordinate location of where to map to
    :param horizontal_data_points int: Number of points to get elevation for horizontally (x)
    :param vertical_data_points int: Number of points to get elevation for vertically (y)
    :return formatted_coords list: List of coords ready to get elevation for
    """
    formatted_coords = []
    for y in np.linspace(from_coords[1], to_coords[1], vertical_data_points):   # Y
        formatted_coords.extend((str(round(x, 7)), str(y))
                                for x in np.linspace(from_coords[0], to_coords[0], horizontal_data_points))    # X
    return formatted_coords


def fetch_format_around(center_coords: tuple, horizontal_data_points: int, vertical_data_points: int, width=0.2, height=0.2) -> (list, list, list):
    """
    Function to format coordinate data from around a certain point
    :param center_coords tuple(float, float): Coordinate location of where to map center from
    :param horizontal_data_points int: Number of points to get elevation for horizontally (x)
    :param vertical_data_points int: Number of points to get elevation for vertically (y)
    :param width float: Width to plot, coordinate degree
    :param height float: Height to plot, coordinate degree
    :return formatted_coords list: List of coords ready to get elevation for
    """
    from_coords = (center_coords[0] - width/2, center_coords[1] - height/2)
    to_coods = (center_coords[0] + width/2, center_coords[1] + height/2)
    formatted_coords = fetch_format_from_to(from_coords, to_coods,
                                            horizontal_data_points, vertical_data_points)
    return formatted_coords


# TODO Implement some sort of async operation here
def fetch(coords: list) -> list:
    """
    Get and parse data from server with provided coordinats list
    :param coords list: List of coords(x, y) to get the elevation of
    :return data list: List of dictionaries from API: {lat, lng, elevation}
    """
    coords_url = ""
    data = []
    timer = time.time() - 1   # Get the calls going imediately
    # Initiate progress bar
    printProgressBar(0, len(coords), prefix='Fetching Elevation Data:',
                     suffix='Complete', length=50)
    for index, coord in enumerate(coords):
        coords_url += coord[0] + "," + coord[1] + "|"
        if index % 100 == 0:
            # remove trailing |
            coords_url = coords_url[:-1]
            # API has a call limit of 1 per second, so delay here until that limit is up
            while time.time() - timer < 1:
                pass
            for _ in range(RETRIES):
                if type(response := _get(BASE_URL + coords_url)) == dict:
                    break
            else:
                raise TimeoutError("Server not returning data")
            # Progress progress bar
            printProgressBar(index, len(coords), prefix='Fetching Elevation Data:',
                             suffix='Complete', length=50)
            # Check to make sure there are no NoneType's responsed
            if all(map(lambda r: r['elevation'] != None, response['results'])):
                data.extend(response['results'])
            else:
                raise ValueError(
                    f'API didn\'t like your coordinates: {coords_url}')
            timer = time.time()  # Reset timer
            coords_url = ""
    else:
        # Completed nomonally
        printProgressBar(len(coords), len(coords), prefix='Fetching Elevation Data:',
                         suffix='Complete', length=50)
        return data
    raise ValueError("Something went wrong")


def _get(url: str, errors=True):
    """
    For getting a response from the API
    :param url str: URL to get
    :param errors bool: If True display HTTP response code if theres an error
    :return response.json()
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        if errors:
            print("Response status code: ", response.status_code)
        return response.status_code
