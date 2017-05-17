from glob import glob
import tqdm
import os
import xml.etree.ElementTree as ET
from ..parsers.BedParser import BedParser
import logging
import pandas as pd
from . import generateKey
from ..DataStructures import reg_fixed_fileds, \
    chr_aliases, start_aliases, stop_aliases, strand_aliases


# global logger
logger = logging.getLogger("PyGML logger")


def load_reg_from_path(path, parser=None):
    if parser is None:
        # get the parser for the dataset
        parser = get_parser(path)
    # we need to take only the files of the regions, so only the files that does NOT end with '.meta'
    all_files = set(glob(pathname=path + '/*'))
    meta_files = set(glob(pathname=path + '/*.meta'))

    only_region_files = all_files - meta_files
    logger.info("Loading region data from path {}".format(path))
    parsed = []
    for file in tqdm.tqdm(only_region_files, total=len(only_region_files)):
        if file.endswith("schema") or file.endswith("_SUCCESS"):
            continue
        abs_path = os.path.abspath(file)
        key = generateKey(abs_path)
        fo = open(abs_path)
        lines = fo.readlines()
        fo.close()
        # parsing
        list_of_dict = list(map(lambda row: parser.parse_line_reg(key, row), lines))
        del lines
        df = to_pandas(list_of_dict)
        parsed.append(df)    # [dict,...]
        del df
        #TODO: solve the problem of memory consuption
    result = pd.concat(objs=parsed, ignore_index=True, copy=False)
    del parsed
    result = result.set_index('id_sample')
    return result


def get_parser(path):
    schema_file = glob(pathname=path + '/*.schema')[0]
    tree = ET.parse(schema_file)
    gmqlSchema = tree.getroot().getchildren()[0]
    parser_name = gmqlSchema.get('type')
    field_nodes = gmqlSchema.getchildren()

    i = 0
    chrPos, startPos, stopPos, strandPos, otherPos = None, None, None, None, None
    otherPos = []
    for field in field_nodes:
        name = list(field.itertext())[0].lower()
        type = field.get('type').lower()

        if name in chr_aliases:
            chrPos = i
        elif name in start_aliases:
            startPos = i
        elif name in stop_aliases:
            stopPos = i
        elif name in strand_aliases:
            strandPos = i
        else: # other positions
            otherPos.append((i, name, type))
        i += 1

    return BedParser(parser_name=parser_name, delimiter='\t',
                     chrPos=chrPos, startPos=startPos, stopPos=stopPos,
                     strandPos=strandPos, otherPos=otherPos)


def to_pandas(reg_list):
    df = pd.DataFrame.from_dict(reg_list)
    df = df[reg_fixed_fileds + [c for c in df.columns if c not in reg_fixed_fileds]]
    return df


def to_dictionary(tuple):
    d = tuple[1]
    d['id_sample'] = tuple[0]
    return d


