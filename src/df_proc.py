import logging
import os
from functools import cached_property
from typing import Dict, Tuple

import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import wkt

from util import FileDirNames as DIR
from util import GeoUtil as GU


class RoadsDataFrame:

    ROADS_DF_NAME = "roads_graph_data"

    @staticmethod
    def dfs_from_graph(graph: nx.MultiDiGraph) -> Tuple[pd.DataFrame, pd.DataFrame]:
        logging.info("Extracting nodes and edges dataframes from roads graph")
        nodes, edges = ox.graph_to_gdfs(graph)
        return nodes, edges

    @staticmethod
    def graph_df_preproc(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
        nodes = nodes.reset_index()
        edges = edges.reset_index()

        nodes = nodes[
            [
                "osmid",
                "street_count",
                "geometry",
            ]
        ]
        nodes.rename(
            columns={"geometry": "point_geometry", "osmid": "point_osmid"},
            inplace=True,
        )

        cols_cast = [
            "name",
            "highway",
            "lanes",
            "osmid",
            "reversed",
        ]

        for col in cols_cast:
            edges[col] = edges[col].astype(str)

        logging.info("Merging nodes and edges into a unique dataframe")
        roads = (
            edges.merge(nodes, left_on="u", right_on="point_osmid", how="left")
            .rename(columns={"point_osmid": "point_osmid_u"})
            .rename(columns={"street_count": "street_count_u"})
            .rename(columns={"point_geometry": "point_geometry_u"})
            .merge(nodes, left_on="v", right_on="point_osmid", how="left")
            .rename(columns={"point_osmid": "point_osmid_v"})
            .rename(columns={"street_count": "street_count_v"})
            .rename(columns={"point_geometry": "point_geometry_v"})
        )
        roads["name"].fillna("Unknown", inplace=True)
        return roads

    @staticmethod
    def remove_duplicates(roads_df: pd.DataFrame) -> pd.DataFrame:
        roads_df["tmp"] = roads_df["u"] + roads_df["v"]
        roads_df = roads_df.groupby(["tmp", "name"]).first().reset_index()

        cols = [
            "point_osmid_u",
            "point_osmid_v",
            "key",
            "osmid",
            "reversed",
            "maxspeed",
            "ref",
            "bridge",
            "tunnel",
            "access",
            "width",
            "est_width",
            "tmp",
        ]

        roads_df.drop(
            columns=list(set(cols) & set(roads_df.columns)),
            inplace=True,
        )
        return roads_df

    @staticmethod
    def df_sub_curveness(df_in: pd.DataFrame) -> pd.DataFrame:
        logging.info("Computing sinuosity of single road segments")
        df_in["sub_curveness"] = df_in["geometry"].apply(GU.compute_sub_curveness)
        return df_in

    @staticmethod
    def df_avg_curveness(df_in: pd.DataFrame, first_method: bool) -> pd.DataFrame:
        col_creation = "avg_curveness_first"
        col_group = "sub_curveness"
        if first_method:
            logging.info(
                "Computing average sinuosity of entire road by name (first method)"
            )
        if not first_method:
            logging.info(
                "Computing average sinuosity of entire road by name (second method)"
            )
            col_creation = "avg_curveness_second"
            col_group = "geometry"
            df_in["geometry"] = df_in["geometry"].astype(str)

        df_in[col_creation] = df_in.groupby("name")[col_group].transform(
            GU.compute_avg_curveness, first_method
        )

        if not first_method:
            df_in["geometry"] = df_in.apply(lambda x: wkt.loads(x["geometry"]), axis=1)
        return df_in

    @staticmethod
    def compute_segment_avg_adjacent_segments(roads: pd.DataFrame) -> pd.DataFrame:
        roads["avg_sub_adjacent_roads"] = (
            roads["street_count_u"] + roads["street_count_v"]
        ) / 2
        return roads

    @staticmethod
    def to_csv(df, city) -> None:
        df_path = os.path.join(DIR.OSM_DIR, city, RoadsDataFrame.ROADS_DF_NAME + ".csv")
        if os.path.isfile(df_path):
            logging.warning(
                "File {} already exists, overwriting it".format(
                    RoadsDataFrame.ROADS_DF_NAME
                )
            )
            os.remove(df_path)
        logging.info("Saving {}...".format(RoadsDataFrame.ROADS_DF_NAME))
        df.to_csv(df_path, index=False)


class TagsDictDF:

    TAGS = {
        "semaforo": {"highway": "traffic_signals"},
        "precedenza": {"highway": "give_way"},
        "stop": {"highway": "stop"},
        "rotatoria": {"junction": "roundabout"},
        "rotaie_tram": {"railway": "tram"},
        "manto_stradale": {"surface": True},
        "parcometri": {
            "amenity": "vending_machine",
            "vending": "parking_tickets",
        },
        "colonnine": {"amenity": "charging_station"},
    }

    def __init__(self, nan_cols_thres: float, city: str):
        self.nan_cols_thres = nan_cols_thres
        self.city = city

    @cached_property
    def df_dict(self):
        return self.retrieve_dict()

    def retrieve_dict(self) -> Dict[str, pd.DataFrame]:

        df_dict = {}

        highway_filt_manto = [
            "living_street",
            "motorway",
            "motorway_link",
            "primary",
            "primary_link",
            "residential",
            "secondary",
            "secondary_link",
            "service",
            "tertiary",
            "tertiary_link",
            "trunk",
            "trunk_link",
            "unclassified",
        ]

        for obj, query in self.__class__.TAGS.items():
            df_path = os.path.join(DIR.OSM_DIR, self.city, obj + ".csv")
            if not os.path.isfile(df_path):
                logging.info("Retrieving {}".format(obj))
                df = ox.geometries_from_place(
                    self.city,
                    query,
                )
                df = df.reset_index()

                if obj == "manto_stradale":
                    df = df[
                        df["highway"].isin(
                            list(set(highway_filt_manto) & set(df.columns))
                        )
                    ]
                    df["surface_mapped"] = np.where(
                        df["surface"] == "asphalt", "asphalt", "other"
                    )
                col_list = (
                    [col for col in df.columns if col != "nodes"]
                    if obj in ["rotatoria", "rotaie_tram", "manto_stradale"]
                    else df.columns
                )

                nan_dict = {col: df[col].isna().sum() / df.shape[0] for col in col_list}
                df = df[[col for col, v in nan_dict.items() if v < self.nan_cols_thres]]

                unique_v_dict = {col: df[col].unique().shape[0] for col in df.columns}
                df = df[[col for col, v in unique_v_dict.items() if v > 1]]

                df_dict[obj] = df
            else:
                logging.warning("File {} already exists".format(df_path))
        return df_dict

    def df_dict_to_csv(self) -> None:
        for name, df in self.df_dict.items():
            df_path = os.path.join(DIR.OSM_DIR, self.city, name + ".csv")
            logging.info("Saving {}...".format(name))
            df.to_csv(df_path, index=False)
