import argparse
import os
import warnings

from df_proc import RoadsDataFrame as RD
from df_proc import TagsDictDF as TD
from graph import CityGraph as CG
from util import FileDirNames as DIR
from util import custom_logger

logger = custom_logger()


def create_save_roads_dataframe(city="Milan", network_type="drive") -> None:
    g = CG(
        city=city,
        network_type=network_type,
    )
    g.graph_stats()
    road_graph = g.graph
    nodes, streets = RD.dfs_from_graph(road_graph)
    roads = RD.graph_df_preproc(
        nodes,
        streets,
    )
    roads = RD.remove_duplicates(roads)
    roads = RD.df_sub_curveness(roads)
    roads = RD.df_avg_curveness(roads, first_method=True)
    roads = RD.df_avg_curveness(roads, first_method=False)

    final_df = g.compute_merge_centrality_metrics(roads)
    RD.to_csv(final_df, city)


def create_save_items_dataframe(nan_cols_thres=0.3, city="Milan") -> None:
    tags_df = TD(
        nan_cols_thres=nan_cols_thres,
        city=city,
    )
    tags_df.df_dict_to_csv()


def main():
    parser = argparse.ArgumentParser(
        description="Extract and process OSM data for the specified city"
    )
    parser.add_argument(
        "-c",
        "--city",
        type=str,
        required=True,
    )
    city = parser.parse_args().city
    if not os.path.isdir(DIR.OSM_DIR):
        os.mkdir(DIR.OSM_DIR)
    city_dir_path = os.path.join(DIR.OSM_DIR, city)
    if not os.path.isdir(city_dir_path):
        os.mkdir(city_dir_path)

    create_save_roads_dataframe(city=city)
    create_save_items_dataframe(city=city)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
