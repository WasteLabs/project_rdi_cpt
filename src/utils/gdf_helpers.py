"""
Helper functions for geopandas
"""


import geopandas as gpd
import pandas as pd
from shapely import wkt
from pyproj import Proj


def geom_to_points(df):
    """Convert geometry layer into points layer for pydeck plotting.

    Arg:
        df (geo.dataframe): Geo-dataframe whose active geometry layer will be
            converted.

    Return:
        points column: [(lon, lat)] for each lon-lat coordinate pair.
    """
    df['points'] = df.apply(lambda x: [y for y in x.geometry.coords], axis=1)
    return df


def calc_dist(df, x0='x', y0='y', x1='x1', y1='y1'):
    dist = ( ( (df[x0].subtract(df[x1]) ).pow(2) ).add( ( df[y0].subtract(df[y1]) ).pow(2) ) ).pow(0.5)
    return dist


def create_gdf(df, crs='EPSG:4326', dropna_geom=False):
    """Convert data frame into geopandas data frame.

    Arg:
        df (data.frame): to convert, must have `geometry` column.
        crs (str): coordinate reference system.
        dropna_geom (bool): drop geometries that are nan
    """
    df = df.copy()
    if dropna_geom is True:
        df = df.dropna(subset=['geometry'])
    if df['geometry'].dtype == 'O':
        df['geometry'] = df['geometry'].astype(str).apply(wkt.loads)
    df = gpd.GeoDataFrame(df, geometry=df['geometry'], crs=crs)
    return df


def create_latlon_gdf(df, crs='EPSG:4326', x_col='lon', y_col='lat', dropna_geom=True):
    """Convert data frame into geopandas data frame.

    Arg:
        df (data.frame): to convert, must have `geometry` column.
        crs (str): coordinate reference system.
    """
    if dropna_geom is True:
        df = df.dropna(subset=[x_col, y_col])
    df = gpd.GeoDataFrame(df,
                          geometry=gpd.points_from_xy(df[x_col], df[y_col]),
                          crs=crs)
    return df


def add_xy_proj(df, crs='EPSG:3414', lon_key='lon', lat_key='lat'):
    pp = Proj(crs)
    xx, yy = pp(df[lon_key].values, df[lat_key].values)
    df['x'] = xx
    df['y'] = yy
    return df


def add_lonlat_proj(df, crs, lon_key='lon', lat_key='lat'):
    pp = Proj(crs)
    xx, yy = pp(df[lon_key].values, df[lat_key].values)
    df['x'] = xx
    df['y'] = yy
    return df


def extract_node_gdf(df, crs):
    """Extract a node data frame from arc data"""
    df = df[['u', 'v', 'geometry']].copy()
    df['points'] = df.apply(lambda x: [y for y in x['geometry'].coords],
                            axis=1)
    df['u_lon'] = df['points'].apply(lambda x: x[0][0])
    df['u_lat'] = df['points'].apply(lambda x: x[0][1])
    df['v_lon'] = df['points'].apply(lambda x: x[-1][0])
    df['v_lat'] = df['points'].apply(lambda x: x[-1][1])
    df_u = df[['u', 'u_lon', 'u_lat']]
    df_u.columns = ['u', 'x', 'y']
    df_v = df[['v', 'v_lon', 'v_lat']]
    df_v.columns = ['u', 'x', 'y']
    df = pd.concat([df_u, df_v])
    df = df.drop_duplicates()
    df = df.set_index(['u'], drop=False)
    df.index.name = None

    df = gpd.GeoDataFrame(df,
                          geometry=gpd.points_from_xy(df['x'], df['y']),
                          crs=crs)

    return df
