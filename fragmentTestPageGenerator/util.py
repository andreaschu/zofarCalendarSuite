from dataclasses import dataclass
import datetime
from typing import Optional, Union
import json
import random
from dateutil.relativedelta import relativedelta
from pathlib import Path
from os import path
from fragmentMemoryCalculator.fragmentMemoryCalculator import compress_and_hexencode
import math

TYPES = ['Slot1', 'Slot2', 'Slot3', 'Slot4', 'Slot5', 'Slot6', 'Slot7', 'Slot8', 'Slot9', 'Slot10']
FLAGS = ['startHO', 'endHO', 'startIDK', 'endIDK', 'FLAG01', 'FLAG02', 'FLAG03', 'FLAG04']

BLINDTEXT = Path(path.abspath('.'), 'data', 'blindtext01.txt').read_text(encoding='utf-8').split(' ')


def random_date(n: int = 1):
    return [datetime.datetime(year=random.choice(range(50)) + 1980,
                              month=random.choice(range(12)) + 1,
                              day=1,
                              hour=1) for i in range(n)]


def random_date_pair():
    t1 = datetime.datetime(year=random.choice(range(50)) + 1980,
                           month=random.choice(range(12)) + 1,
                           day=1,
                           hour=1)
    return t1, t1 + relativedelta(months=random.choice(range(120))) - relativedelta(days=1)


def as_zofar_datetime_str(timestamp_tuple: tuple):
    return tuple([ts.strftime(format='%Y-%m-%dT01-00-00.000Z') for ts in timestamp_tuple])


def create_episode(start_date: datetime.date, end_date: datetime.date, *args, **kwargs):
    return {"startDate": start_date, "endDate": end_date}


def create_random_episode(*args, **kwargs):
    start_date, end_date = as_zofar_datetime_str(random_date_pair())
    return create_episode(start_date=start_date, end_date=end_date, *args, **kwargs)


def create_blindtext(str_length: int) -> str:
    blindtext = ""

    while len(blindtext) < str_length:
        blindtext += ' ' + ' '.join(random.sample(BLINDTEXT, 3))
    return blindtext


def random_single_choice_var_dict(k: int, var_name_stem: str = 'scvarstem'):
    return {var_name_stem + str(i): 'ao' + str(random.choice(range(10))) for i in range(k)}


def random_multiple_choice_var_dict(k: int, var_name_stem: str = 'mcvarstem'):
    return {var_name_stem + str(i): random.choice(['True', 'False']) for i in range(k)}


def random_open_question_var_dict(k: int, qo_str_length: int = 30, var_name_stem: str = 'qovarstem'):
    return {var_name_stem + str(i): create_blindtext(str_length=qo_str_length) for i in range(k)}


def add_random_episode_to_dict(input_list: list,
                               sc_count: int = 10,
                               mc_count: int = 10,
                               qo_count: int = 10,
                               qo_str_len: int = 30):
    episode = create_random_episode()
    episode['index'] = len(input_list)
    episode['type'] = random.choice(TYPES)
    flags = random.sample(FLAGS, random.choice(range(len(FLAGS))))
    if flags != []:
        episode['flags'] = flags
    episode.update(random_single_choice_var_dict(k=sc_count))
    episode.update(random_multiple_choice_var_dict(k=mc_count))
    episode.update(random_open_question_var_dict(k=qo_count, qo_str_length=qo_str_len))
    input_list.append(episode)
    return input_list


def create_array_of_dicts_max_json_length(json_str_len: int = 10000, **kwargs) -> list:
    array_of_dicts = []
    while len(json.dumps(array_of_dicts)) < json_str_len:
        add_random_episode_to_dict(input_list=array_of_dicts, **kwargs)
    return array_of_dicts


def create_array_of_dicts_max_fragment_var_count(fragment_var_count: int = 150,
                                                 str_len_per_frag_var: int = 1500,
                                                 **kwargs) -> list:
    array_of_dicts = []
    while math.ceil(len(compress_and_hexencode(json.dumps(array_of_dicts)))/str_len_per_frag_var) < fragment_var_count:
        add_random_episode_to_dict(input_list=array_of_dicts, **kwargs)
    return array_of_dicts


def main():
    x = create_array_of_dicts_max_json_length(json_str_len=10000)
    y = create_array_of_dicts_max_fragment_var_count(fragment_var_count=150)
    print()


if __name__ == "__main__":
    main()
