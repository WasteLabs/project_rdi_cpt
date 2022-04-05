"""
Process Open-Street-Map data retrieved using OSMNX and converted into
geo-dataframes.
"""

import numpy as np
from shapely import wkt
import logging
logger = logging.getLogger(__name__)


def geom_to_points(df):
    """Convert geometry layer into points layer for pydeck plotting.

    Arg:
        df <geo.dataframe>: Geo-dataframe whose line-geometry layer will be
            converted.

    Return:
        points <list (lon, lat)>: list of coordinate pairs of each point
            in the geometry object.
    """
    logger.debug('Extracting points from `geometry`')
    if type(df['geometry'].values[0]) == str:
        df['geometry'] = df['geometry'].apply(wkt.loads)
    return df.apply(lambda x: [y for y in x.geometry.coords], axis=1)


def create_arc_id(df, arc_id_col, columns=None):
    """Create new id based on a bunch of column values.

    Note that where nan keys are filled with zeros, the resulting key
    will have 0 in places, which may represent an actual arc key for another
    arc.

    Args:
        df <pd.DataFrame>: data-frame to create a new id columns with
        arc_id <col-str>: column name of id
        columns <list (col-str)>: column names of new ids.

    Return:
        df[arc_id] <str>: '-' separated string of values in columns.
    """
    logger.debug('Creating new arc ids')
    if columns is None:
        columns = ['u', 'v', 'key']

    df[arc_id_col] = ''
    key_nan = []
    for i, key in enumerate(columns):
        key_i = df[key].fillna(0).astype(str)
        if i == 0:
            df[arc_id_col] = key_i
            key_nan = df[key].isna()
        else:
            df[arc_id_col] = df[arc_id_col] + '-' + key_i
            key_nan = key_nan | key_nan

    if len(key_nan):
        df.loc[key_nan, arc_id_col] = np.nan

    return df


def create_geometry_key(df, geometry_id_col='geom_id', inverse=True):
    """Create new id from points geometry column.

    Args:
        df <pd.DataFrame>: data-frame to create a new id columns with
        geometry_id_col <col-str>: column name of id
        inverse <bool>: create an inverse key.

    Return:
        df[geometry_id_col] <str>: geometry string.
        df[geometry_id_col + '_inv'] <str>: geometry string inverted.
    """
    logger.debug('Creating string geometry keys')
    points = geom_to_points(df)
    df[geometry_id_col] = points.astype(str)
    if inverse:
        logger.debug('Creating inverted geometry keys')
        points_inv = points.apply(lambda x: x[::-1])
        df[geometry_id_col + '_inv'] = points_inv.astype(str)
    return df


def update_inverse_id(df,
                      geometry_id_col='geom_id',
                      geometry_id_inv_col='geom_id_inv',
                      geometry_id_order='geom_id_order'):
    """Update inverse geom ids to point only to arcs that are truly
    inverted and add ordered ids for invertable arcs, so that there
    are only one per pair.

    Args:
        df <pd.DataFrame>: data-frame to create a new id columns with
        geometry_id_col <col-str>: column name of geom id
        geometry_id_inv_col <col-str>: column name of inverted geom id
        geometry_id_order <col-str>: name of ordered geometry column id. Used
            when only one arc orientation is needed.

    Return:
        df[geometry_id_inv_col] <str>: set to NaN if not an edge.
        df[geometry_id_order] <str>: ordered (smallest) geom-id between
            geometry_id_col and geometry_id_inv_col, if the arc belongs
            to an edge, otherwise, `geometry_id_inv_col=geometry_id_col`.
    """
    logger.debug('Removing inverted geometry keys for one-way arcs.')
    invert = df[geometry_id_inv_col].isin(df[geometry_id_col])

    if geometry_id_order is not None:
        logger.debug('Creating ordered geometry key.')
        min_id = df[[geometry_id_col, geometry_id_inv_col]].min(axis=1)
        df[geometry_id_order] = min_id
        df.loc[~invert, geometry_id_order] = df.loc[~invert, geometry_id_col]

    df.loc[~invert, geometry_id_inv_col] = np.nan

    return df


def process_edges(df, add_arc_key=True):
    """Process OSM edges by assigning inverse geom-ids.

    Args:`
        df <pd.DataFrame>: data-frame with geometry column. Doesn't have
            to be a geodataframe object.
        add_arc_key (bool): add arc key, useful when working with projected xy
            and original lon-lat coordinate systems.

    Return:
        df['geom_id'] <str>: geometry string.
        df['geom_id_inv'] <str>: geometry string inverted, if the arc is
            a two-way segment, otherwise it's NaN.
        df['geom_id_order'] <str>: ordered (smallest) geom-id between
            'geom_id' and 'geom_id_inv', if the arc is a two-way segment,
            otherwise, `geom_id_order=geom_id_inv`.
    """
    logger.debug('Adding geometry keys to OSM arcs.')
    df = df.copy()
    if add_arc_key:
        df = create_arc_id(df, 'arc_id')
    df = create_geometry_key(df)
    df = update_inverse_id(df)
    return df
