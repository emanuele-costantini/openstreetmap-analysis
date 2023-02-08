from graph import CityGraph as CG
from util import custom_logger, FileDirNames as DIR
from df_proc import RoadsDataFrame as RD, TagsDictDF as TD
import os

logger = custom_logger()


def create_save_roads_dataframe(city="Milan", network_type="drive") -> None:
    g = CG(
        city=city,
        network_type=network_type,
    )
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
    RD.to_csv(final_df)


def create_save_items_dataframe(nan_cols_thres=.3, city="Milan") -> None:
    tags_df = TD(
        nan_cols_thres=nan_cols_thres,
        city=city,
    )
    TD.df_dict_to_csv()


def main():
    os.mkdir(DIR.OSM_DIR)
    create_save_roads_dataframe()
    create_save_items_dataframe()


if __name__ == "__main__":
    main()