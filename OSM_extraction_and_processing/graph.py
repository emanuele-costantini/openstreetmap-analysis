import logging
from functools import cached_property
from typing import Callable, Tuple

import networkx as nx
import osmnx as ox
import pandas as pd

from util import mean_centrality_road, time_decorator


class CityGraph:

    CENTRALITY_METRICS = {
        "pagerank": time_decorator(nx.pagerank),
        "degree": time_decorator(nx.degree_centrality),
        "betweenness": time_decorator(nx.betweenness_centrality),
        "closeness": time_decorator(nx.closeness_centrality),
    }

    def __init__(
        self,
        city: str,
        network_type: str,
    ) -> None:
        self.city = city
        self.network_type = network_type

    @cached_property
    def graph(self):
        return self.retrieve_graph()

    def retrieve_graph(self) -> nx.MultiDiGraph:
        logging.info("Creating graph for {}...".format(self.city))
        g = ox.graph_from_place(self.city, network_type=self.network_type)
        logging.info("Graph for {} created!".format(self.city))
        return g

    @staticmethod
    def graph_stats(graph: nx.MultiDiGraph) -> Tuple[int, int]:
        if not isinstance(graph, nx.MultiDiGraph):
            logging.error("Input is not a graph!")
            raise TypeError("No graph provided as input")
        n_nodes = len(graph.nodes)
        n_edges = len(graph.edges)
        logging.info("Number of nodes: {}".format(n_nodes))
        logging.info("Number of edges: {}".format(n_edges))

        return n_nodes, n_edges

    def compute_centrality(self, centrality_func: Callable) -> Tuple[pd.DataFrame, str]:
        centrality_dict = centrality_func(self.graph)
        centrality_col_name = centrality_func.__name__.rsplit("_", 1)[0]
        centrality_df = pd.DataFrame(
            centrality_dict.items(), columns=["node", centrality_col_name]
        )
        centrality_df[centrality_col_name] = centrality_df[centrality_col_name].round(5)

        return centrality_df, centrality_col_name

    def compute_merge_centrality_metrics(
        self, df_to_merge: pd.DataFrame
    ) -> pd.DataFrame:
        for cen_metric, val in self.__class__.CENTRALITY_METRICS.items():
            df_graph, col = self.compute_centrality(val)

            df_to_merge = df_to_merge.merge(
                df_graph, left_on="u", right_on="node", how="left"
            )
            df_to_merge = df_to_merge.drop("node", axis=1)
            df_to_merge = df_to_merge.rename(columns={col: col + "_u"})

            df_to_merge = df_to_merge.merge(
                df_graph, left_on="v", right_on="node", how="left"
            )
            df_to_merge = df_to_merge.drop("node", axis=1)
            df_to_merge = df_to_merge.rename(columns={col: col + "_v"})

            tmp = (
                df_to_merge.groupby("name")[[col + "_u", col + "_v"]]
                .apply(
                    mean_centrality_road,
                    col_u=cen_metric + "_u",
                    col_v=cen_metric + "_v",
                )
                .to_frame("avg_via_" + col)
            )

            df_to_merge = df_to_merge.merge(tmp, left_on="name", right_on="name")
            df_to_merge["avg_sub_" + col] = (
                df_to_merge[col + "_u"] + df_to_merge[col + "_v"]
            ) / 2

        return df_to_merge
