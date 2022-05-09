import json
import pprint
from zcts.data.xml import read_questionnaire, VarRef, JsonAttrRef, Variable, JsonAttr
from typing import Dict, Union
from collections import defaultdict
from fragmentTestPageGenerator.util import create_module
from fragmentMemoryCalculator.fragmentMemoryCalculator import hexencode_and_compress, compress_and_hexencode, \
    hexencode_str, compress
import math

VAR_TYPES = ['string', 'enum', 'boolean']
CHARS_PER_FRAGMENT_VARIABLE = 1500

EPISODE_COUNTS_PER_MODULE = {
    'va': 10,
    'vc': 5
}


def split_by_first_page_letters(n: int, pages_dict: Dict[str, Union[VarRef, JsonAttrRef]]) -> dict:
    abbr_page_names = set([page_uid[:n] for page_uid in pages_dict.keys()])
    tmp_dict = {page_name_abbr: defaultdict(list) for page_name_abbr in abbr_page_names}
    for page_abbr in tmp_dict.keys():
        for page_name, attr_ref_list in pages_dict.items():
            if page_name.startswith(page_abbr):
                tmp_dict[page_abbr][page_name] = attr_ref_list
    return tmp_dict


def main():
    input_xml = r'C:\Users\friedrich\zofar_workspace\Test_Modul\src\main\resources\questionnaire.xml'
    q = read_questionnaire(input_path=input_xml)
    pages_with_json_triggers = {page.uid: page.var_refs + page.json_attr for page in q.pages if page.json_attr}

    s = split_by_first_page_letters(pages_dict=pages_with_json_triggers, n=2)

    all_modules_var_dict = {}
    for module_name_abbr, module_pages in s.items():
        module_var_dict = {}
        for page_name, json_attr_list in module_pages.items():
            for var_ref in json_attr_list:
                if var_ref.variable.name in module_var_dict.keys():
                    # ToDo: find a way to process this (if it ever occurs)
                    pass
                    # raise KeyError(f'Key "{var_ref.variable.name}" already present.')
                module_var_dict[var_ref.variable.name] = var_ref.variable

        all_modules_var_dict[module_name_abbr] = module_var_dict

    all_modules_var_count = {}

    for module_abbr, json_attr_dict in all_modules_var_dict.items():
        module_var_counts = defaultdict(int)

        for json_attr_name, json_attr_ref in json_attr_dict.items():
            if json_attr_name in ['id', 'startDate', 'endDate', 'type', 'typeColor']:
                continue

            # if the JSON attribute is also a zofar variable
            if isinstance(json_attr_ref, Variable):
                if json_attr_ref.type == 'string':
                    module_var_counts['qo_count'] += 1
                elif json_attr_ref.type == 'enum':
                    module_var_counts['sc_count'] += 1
                elif json_attr_ref.type == 'boolean':
                    module_var_counts['mc_count'] += 1
                else:
                    raise ValueError(f'Unknown type: {json_attr_ref.type}')

            # if the JSON attribute is NOT a zofar variable
            elif isinstance(json_attr_ref, JsonAttr):
                raise NotImplementedError('')
            else:
                raise TypeError(f'Wrong type: {type(json_attr_ref)}')
            print()

        all_modules_var_count[module_abbr] = module_var_counts
        print()

    episode_counter_dict = {module_abbr: 0 for module_abbr in all_modules_var_dict.keys()}
    episode_counter_dict.update(EPISODE_COUNTS_PER_MODULE)

    if min(episode_counter_dict.values()) == 0:
        raise ValueError(f'Module "{[key for key, val in episode_counter_dict.items() if val == 0]}" has length 0.')

    whole_json_array = []
    for module_name_abbr, module_count in episode_counter_dict.items():
        whole_json_array += create_module(episode_count=module_count,
                                          sc_var_name_stem=f'sc_{module_name_abbr}',
                                          sc_count=all_modules_var_count[module_name_abbr]['sc_count'],
                                          mc_var_name_stem=f'mc_{module_name_abbr}',
                                          mc_count=all_modules_var_count[module_name_abbr]['mc_count'],
                                          qo_var_name_stem=f'qo_{module_name_abbr}',
                                          qo_count=all_modules_var_count[module_name_abbr]['qo_count'],
                                          qo_str_len=2000,
                                          qo_random=True)

    results = {
        'whole_json_length': len(json.dumps(whole_json_array)),
        'whole_json_length_compressed': len(compress(json.dumps(whole_json_array))),
        'whole_json_length_hexencoded': len(hexencode_str(json.dumps(whole_json_array))),
        'whole_json_length_hexencoded_and_compressed': len(hexencode_and_compress(json.dumps(whole_json_array))),
        'whole_json_length_compressed_and_hexencoded': len(compress_and_hexencode(json.dumps(whole_json_array)))}

    results_fragment = {key: math.ceil(val / CHARS_PER_FRAGMENT_VARIABLE) for key, val in results.items()}

    print('\n\n' + '#' * 100 + '\n\nwhole JSON array string length:\n')
    pprint.pprint(results)
    print('\n\n' + '#' * 100 + f'\n\nfragment variables needed {CHARS_PER_FRAGMENT_VARIABLE} chars per fragment var:\n')
    pprint.pprint(results_fragment)
    breakpoint()


if __name__ == '__main__':
    main()
