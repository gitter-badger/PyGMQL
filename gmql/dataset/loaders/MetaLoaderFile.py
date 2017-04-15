from glob import glob
from tqdm import tqdm
import logging

from ..parsers.GenericMetaParser import GenericMetaParser
from . import generateKey
import os
import pandas as pd

logger = logging.getLogger('gmql_logger')


def load_meta_from_path(path):
    meta_files = glob(pathname=path + '/*.meta')
    parsed = []
    parser = GenericMetaParser()
    logger.info("Loading meta data from path {}".format(path))
    for f in tqdm(meta_files, total=len(meta_files)):
        abs_path = os.path.abspath(f)
        abs_path_no_meta = abs_path[:-5]
        key = generateKey(abs_path_no_meta)
        lines = open(abs_path).readlines()
        # parsing
        parsed.extend(list(map(lambda row: parser.parse_line_meta(key, row), lines)))  # [(id, (attr_name, value)),...]
    return to_pandas(parsed)


def to_pandas(meta_list):
    # turn to dictionary
    meta_list = list(map(to_dictionary, meta_list))     # [{'id_sample': id, attr_name: value},...]
    df = pd.DataFrame.from_dict(meta_list)
    columns = df.columns

    # grouping by 'id_sample'
    g = df.groupby('id_sample')

    logger.info("dataframe construction")
    result_df = pd.DataFrame()
    for col in tqdm(columns, total=len(columns)):
        if col != 'id_sample':
            result_df[col] = g[col].apply(to_list)
    return result_df


def to_dictionary(tuple):
    return {"id_sample": tuple[0], tuple[1][0] : tuple[1][1]}


def to_list(x):
    l = list(x)
    l = [a for a in l if not pd.isnull(a)]
    return l