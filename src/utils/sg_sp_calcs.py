import networkx as nx
from mcarptif.converter.network_prep import ShortestPathNodes

import logging
logging.basicConfig(level=logging.INFO)

file = "sp_files/full_road_simple_red.gpickle"
logging.info(f'Reading OSMNX graph from `{file}`')
G = nx.read_gpickle(file)

sp_object = ShortestPathNodes(G)
sp_object.calc_shortest_path_pytable('sp_files/SG_sp.h', f'SP calcs for: "{file}"')