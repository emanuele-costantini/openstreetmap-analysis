import logging
import time
from functools import wraps
from statistics import mean
from typing import Callable, List, Union, get_type_hints

import pandas as pd
from pyproj import Transformer
from shapely import LineString, MultiLineString, line_merge, ops, wkt


def mean_centrality_road(df: pd.DataFrame, col_u: str, col_v: str) -> float:
    mean_u = df[col_u].mean()
    mean_v = df[col_u].mean()

    avg_mean = (mean_u + mean_v) / 2
    return avg_mean


def time_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        logging.info(f"Computing {func.__name__} algorithm on graph...")
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        if total_time <= 60:
            final_time = total_time
            logging.info(f"{func.__name__} took {final_time:.2f} seconds")
        else:
            final_time = total_time / 60
            logging.info(f"{func.__name__} took {final_time:.2f} minutes")
        return result

    return wrapper


def function_rename(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        hints_dict = get_type_hints(func)
        if Callable in hints_dict:
            newname = [i for i in hints_dict if hints_dict[i] == Callable][0]
            func.__name__ = newname
        result = func(*args, **kwargs)
        return result

    return wrapper


def custom_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger


class GeoUtil:

    TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    @staticmethod
    def merge_lines(line_list: List[LineString]) -> Union[LineString, MultiLineString]:
        df_grouped_line_merged = line_merge(line_list)
        merged = ops.linemerge(df_grouped_line_merged)
        return merged

    @staticmethod
    def compute_line_length(linestr: LineString) -> float:
        line_transformed = ops.transform(GeoUtil.TRANSFORMER.transform, linestr)
        return line_transformed.length

    @staticmethod
    def compute_sub_curveness(df: LineString) -> float:
        try:
            p1 = df.boundary.geoms[0]
            p2 = df.boundary.geoms[1]
            bounds_linestring = LineString([p1, p2])

            length = GeoUtil.compute_line_length(df)
            air_length = GeoUtil.compute_line_length(bounds_linestring)
            curve = round(air_length / length, 5)
        except IndexError:
            curve = 0
        return 1 - curve

    @staticmethod
    def compute_avg_curveness(df: pd.DataFrame, first_method: bool) -> float:
        if first_method:
            result = df.mean()
        else:
            df = [wkt.loads(x) for x in df.values]
            merged = GeoUtil.merge_lines(df)
            curveness_list = []
            if isinstance(merged, MultiLineString):
                for line in merged.geoms:
                    curv = GeoUtil.compute_sub_curveness(line)
                    curveness_list.append(curv)
                result = mean(curveness_list)
            else:
                result = GeoUtil.compute_sub_curveness(
                    merged,
                )

        return round(result, 5)


class CustomFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;41m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileDirNames:

    OSM_DIR = "./Data"
