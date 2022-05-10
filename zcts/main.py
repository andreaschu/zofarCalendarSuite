import json
import os.path
import pprint
import time
import matplotlib.pyplot as plt

from zcts.data.xml import read_questionnaire, VarRef, JsonAttrRef, Variable, JsonAttr, Questionnaire
from typing import Dict, Union, Tuple, List
from collections import defaultdict
from zcts.caljson.util import create_module
from zcts.data.util import compress_and_hexencode
from zcts.util import timestamp
import math
from pathlib import Path

VAR_TYPES = ['string', 'enum', 'boolean']
CHARS_PER_FRAGMENT_VARIABLE = 1500

EPISODE_COUNTS_PER_MODULE = {'ns': 200, 'pl': 50, 'va': 10}


def split_by_first_page_letters(n: int, pages_dict: Dict[str, Union[VarRef, JsonAttrRef]]) -> dict:
    abbr_page_names = set([page_uid[:n] for page_uid in pages_dict.keys()])
    tmp_dict = {page_name_abbr: defaultdict(list) for page_name_abbr in abbr_page_names}
    for page_abbr in tmp_dict.keys():
        for page_name, attr_ref_list in pages_dict.items():
            if page_name.startswith(page_abbr):
                tmp_dict[page_abbr][page_name] = attr_ref_list
    return tmp_dict


def prepare_modules(input_xml: Union[str, Path]) -> Tuple[Questionnaire, Dict[str, dict]]:
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
                    if not module_var_dict[var_ref.variable.name] == var_ref.variable:
                        print(f'\033[93mVariable data differs:'
                              f'{module_var_dict[var_ref.variable.name]=}\n'
                              f'{var_ref.variable=}')
                        raise KeyError(
                            f'Key "{var_ref.variable.name}" already present, data differs (see above/below).')
                module_var_dict[var_ref.variable.name] = var_ref.variable

        all_modules_var_dict[module_name_abbr] = module_var_dict
    return q, all_modules_var_dict


def gen_trigger(var_name: str, dropdown: bool) -> Tuple[str, str, str]:
    pass


def gen_trigger_dict(input_xml: Union[str, Path], page_name_startswith: str) -> Dict[str, Dict[str, list]]:
    q = read_questionnaire(input_xml)

    trigger_dict = defaultdict(lambda: defaultdict(list))

    def _reset_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        if not dropdown:
            return [f"""<zofar:scriptItem value="toReset.add('{var_name}')" />"""]
        return [f"""<zofar:scriptItem value="toReset.add('{var_name}')" />""",
                f"""<zofar:scriptItem value="toReset.add('{var_name}dropDown')" />""",
                f"""<zofar:scriptItem value="toReset.add('{var_name}missing')" />"""]

    def _load_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        if not dropdown:
            return [f"""<zofar:scriptItem value="toLoad.add('{var_name}')" />"""]
        return [f"""<zofar:scriptItem value="toLoad.add('{var_name}')" />""",
                f"""<zofar:scriptItem value="toLoad.add('{var_name}dropDown')" />""",
                f"""<zofar:scriptItem value="toLoad.add('{var_name}missing')" />"""]

    def _save_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        enum = var.variable.type == 'enum'
        if not dropdown:
            if enum:
                return [f"""<zofar:scriptItem value="toPersist.put('{var_name}',{var_name}.valueId)" />"""]
            else:
                return [f"""<zofar:scriptItem value="toPersist.put('{var_name}',{var_name})" />"""]
        return [f"""<zofar:scriptItem value="toPersist.put('{var_name}',{var_name})" />""",
                f"""<zofar:scriptItem value="toPersist.put('{var_name}dropDown',{var_name}dropDown)" />""",
                f"""<zofar:scriptItem value="toPersist.put('{var_name}missing',{var_name}missing)" />"""]

    # get all pages that start with the given string
    relevant_pages = [page for page in q.pages if page.uid.startswith(page_name_startswith)]
    for page in relevant_pages:
        for variable in page.var_refs:
            trigger_dict[page.uid]['reset'] += _reset_trigger(variable)
            trigger_dict[page.uid]['load'] += _load_trigger(variable)
            trigger_dict[page.uid]['save'] += _save_trigger(variable)

    return trigger_dict


def calculate_size(input_xml: str,
                   counts_dict: dict,
                   qo_str_length: int = 2000,
                   qo_random: bool = True) -> dict:
    q, all_modules_var_dict = prepare_modules(input_xml)

    details_string_list = []
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
                raise NotImplementedError(f'{json_attr_ref=}')
            else:
                raise TypeError(f'Wrong type: {type(json_attr_ref)}')

        details_string_list.append(pprint.pformat({'module': module_abbr,
                                                   'pages': [page.uid for page in q.pages if
                                                             page.uid.startswith(module_abbr)],
                                                   'variables': [(var.name, var.type) for var in
                                                                 all_modules_var_dict[module_abbr].values()],
                                                   'variable_counts': module_var_counts}, indent=4))

        all_modules_var_count[module_abbr] = module_var_counts
    # pprint.pprint(details_string_list)

    episode_counter_dict = {module_abbr: 0 for module_abbr in all_modules_var_dict.keys()}

    episode_counter_dict.update(counts_dict)

    if not all([(module_abbr in all_modules_var_dict.keys()) for module_abbr in counts_dict]):
        mask = [(module_abbr in all_modules_var_dict.keys()) for module_abbr in counts_dict]
        not_found = [list(counts_dict.keys())[i] for i in range(len(mask)) if not mask[i]]
        raise ValueError(f'Module abbreviations {not_found} cannot be found in QML.')

    if not all([(module_abbr in counts_dict.keys()) for module_abbr in all_modules_var_dict.keys()]):
        mask = [(module_abbr in counts_dict.keys()) for module_abbr in all_modules_var_dict.keys()]
        not_found = [list(all_modules_var_dict.keys())[i] for i in range(len(mask)) if not mask[i]]
        for module_abbr in not_found:
            episode_counter_dict[module_abbr] = int(
                input(f'number of loops (episode count) in module "{module_abbr}": '))
        # raise ValueError(f'Module abbreviations {not_found} not found in counts_dict.')

    if min(episode_counter_dict.values()) == 0:
        # raise ValueError(f'Module "{[key for key, val in episode_counter_dict.items() if val == 0]}" has length 0.')
        print(f'Module "{[key for key, val in episode_counter_dict.items() if val == 0]}" has length 0.')

    whole_json_array = []
    for module_name_abbr, module_count in episode_counter_dict.items():
        whole_json_array += create_module(episode_count=module_count,
                                          sc_var_name_stem=f'sc_{module_name_abbr}',
                                          sc_count=all_modules_var_count[module_name_abbr]['sc_count'],
                                          mc_var_name_stem=f'mc_{module_name_abbr}',
                                          mc_count=all_modules_var_count[module_name_abbr]['mc_count'],
                                          qo_var_name_stem=f'qo_{module_name_abbr}',
                                          qo_count=all_modules_var_count[module_name_abbr]['qo_count'],
                                          qo_str_len=qo_str_length,
                                          qo_random=qo_random)

    results = {
        'whole_json_length': len(json.dumps(whole_json_array)),
        # 'whole_json_length_compressed': len(compress(json.dumps(whole_json_array))),
        # 'whole_json_length_hexencoded': len(hexencode_str(json.dumps(whole_json_array))),
        # 'whole_json_length_hexencoded_and_compressed': len(hexencode_and_compress(json.dumps(whole_json_array))),
        'whole_json_length_compressed_and_hexencoded': len(compress_and_hexencode(json.dumps(whole_json_array)))}

    results_fragment = {key: math.ceil(val / CHARS_PER_FRAGMENT_VARIABLE) for key, val in results.items()}

    tmp_dict = {'length': results.copy(),
                'length_frag': results_fragment.copy(),
                'episode_count': episode_counter_dict,
                'random': qo_random,
                'all_modules_var_count': all_modules_var_count,
                'qo_length': qo_str_length,
                'variables': {}}

    for module_abbr, json_attr_dict in all_modules_var_dict.items():
        tmp_dict['variables'][module_abbr] = {'module': module_abbr,
                                              'pages': [page.uid for page in q.pages if
                                                        page.uid.startswith(module_abbr)],
                                              'variables': [(var.name, var.type) for var in
                                                            all_modules_var_dict[module_abbr].values()],
                                              'variable_counts': module_var_counts}

    details_string_list.append('\n\n' + '#' * 100)
    details_string_list.append(f'\n\nepisode count per module:')
    details_string_list.append(pprint.pformat(episode_counter_dict, indent=4))
    details_string_list.append('\n\nwhole JSON array string length:\n')
    details_string_list.append(pprint.pformat(results, indent=4))
    details_string_list.append(
        '\n\n' + '#' * 100 + f'\n\nfragment variables needed ({CHARS_PER_FRAGMENT_VARIABLE} chars per fragment var):\n')
    details_string_list.append(pprint.pformat(results_fragment, indent=4))
    details_string_list.append('\n\n' + '#' * 100 + '\n' + '#' * 100)
    # print('\n'.join(details_string_list))
    output_file = Path(os.path.abspath(''), 'output', timestamp() + 'details.txt')
    output_file.write_text('\n'.join(details_string_list), encoding='utf-8')
    return tmp_dict


def gen_trigger_str(trigger_dict: Dict[str, Dict[str, list]], fragment_list: List[str]) -> str:
    output_str = "<!-- TRIGGER -->\n\n"

    for page_name, trigger in trigger_dict.items():
        output_str += f"""\t<!-- page {page_name} -->\n\n"""
        output_str += """\t\t<zofar:triggers>\n"""

        output_str += f"""\t\t<!-- reset var data -->\n"""
        output_str += f"""\t\t<zofar:action command="zofar.nothing()" onExit="false">\n"""
        output_str += f"""\t\t\t<!-- initialize empty list -->\n"""
        output_str += f"""\t\t\t\t<zofar:scriptItem value="zofar.assign('toReset',zofar.list())" />\n\n"""
        output_str += f"""\t\t\t\t<!-- add page variables one after another to the list -->\n\t\t\t\t"""
        output_str += '\n\t\t\t\t'.join(trigger['reset']) + '\n'
        output_str += f"""\t\t\t\t<!-- reset all variables stored in list -->\n"""
        output_str += f"""\t\t\t<zofar:scriptItem value="zofar.resetVars(toReset)" />\n\n"""
        output_str += f"""\t\t</zofar:action>\n\n"""

        output_str += f"""\t\t<!-- load json data -->\n"""
        output_str += """\t\t<!-- BAUKASTEN: BASIC page setup within loop when LOADING page -->\n"""
        output_str += """\t\t<zofar:action command="zofar.nothing()" onExit="false">\n"""
        output_str += """\t\t\t<!-- generic json setup - load whole json array (all episodes) -->\n"""
        output_str += f"""\t\t\t<zofar:scriptItem value="zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(fragment_list)}))))" />\n"""
        output_str += """\t\t\t<!-- load specific episode json object from json array (by episode index) -->\n"""
        output_str += """\t\t\t<zofar:scriptItem value="zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) " />\n\n"""
        output_str += """\t\t\t<!-- page-specific -->\n"""
        output_str += """\t\t\t<!-- initialize variables (according to page qml) -->\n"""
        output_str += """\t\t\t<zofar:scriptItem value="zofar.assign('toLoad',zofar.list())" />\n\n\t\t\t\t"""
        output_str += '\n\t\t\t\t'.join(trigger['load']) + '\n'
        output_str += """\t\t\t<zofar:scriptItem value="zofar.getJsonProperties(episodeObj,toLoad)" />\n"""
        output_str += """\t\t</zofar:action>\n\n"""

        output_str += f"""    <!-- save json data -->\n"""
        output_str += """\t\t<!-- BAUKASTEN: BASIC page setup within loop when EXITING page -->\n\n"""
        output_str += """\t\t<!-- last command: fragment json object into several variables -->\n"""
        output_str += """\t\t<zofar:action\n"""
        output_str += f"""\t\t\tcommand="zofar.frac(zofar.list({','.join(fragment_list)}),zofar.jsonArr2str(defrac))"\n"""
        output_str += """\t\t\tonExit="true">\n"""
        output_str += """\t\t\t<!-- generic json setup -->\n"""
        output_str += """\t\t\t<zofar:scriptItem\n"""
        output_str += f"""\t\t\t\tvalue="zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(fragment_list)}))))" />\n"""
        output_str += """\t\t\t<zofar:scriptItem\n"""
        output_str += """\t\t\t\tvalue="zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) " />\n\n"""
        output_str += """\t\t\t<zofar:scriptItem value="zofar.assign('toPersist',zofar.map())" />\n\n"""
        output_str += """\t\t\t<!-- Important for SC to use valueID instead of Value -->\n"""
        output_str += """\t\t\t<!-- all other variables: use value -->\n\t\t\t\t"""
        output_str += '\n\t\t\t\t'.join(trigger['save']) + '\n'
        output_str += """\t\t\t<!-- write all values to episodeObj (still in RAM) -->\n"""
        output_str += """\t\t\t<zofar:scriptItem value="zofar.setJsonProperties('episodeObj',episodeObj,toPersist)" />\n\n"""
        output_str += """\t\t\t<!-- generic json setup -->\n"""
        output_str += """\t\t\t<!-- save episode object into json array to DB -->\n"""
        output_str += """\t\t\t<zofar:scriptItem value="zofar.assign('defrac',zofar.addOrReplaceJson(defrac,episodeObj,zofar.toInteger(episode_index.value)))" />\n"""
        output_str += """\t\t</zofar:action>\n\n\n"""
        output_str += """\t\t</zofar:triggers>\n\n\n"""

    return output_str


def calculate():
    results_list = []
    for counters_dict in [{'ns': i, 'va': 0, 'pl': 0} for i in [1, 10, 20, 30, 40, 50, 100, 150, 200]]:
        results_list.append(calculate_size(input_xml=xml_source,
                                           qo_str_length=100,
                                           qo_random=False,
                                           counts_dict=counters_dict))
    a = [(entry['episode_count'], entry['all_modules_var_count'], entry['length_frag']['whole_json_length'],
          entry['length_frag']['whole_json_length_compressed_and_hexencoded'],
          entry['random'], entry['qo_length']) for entry in results_list]
    uncompressed_frag = [entry[2] for entry in a]
    compressed_frag = [entry[3] for entry in a]
    episode_count = [sum(entry[0].values()) for entry in a]
    # plotting the points
    plt.scatter(episode_count, uncompressed_frag, color='k', label="uncompressed")
    plt.plot(episode_count, uncompressed_frag, color='k')
    plt.scatter(episode_count, compressed_frag, color='g', label="compressed")
    plt.plot(episode_count, compressed_frag, color='g')
    plt.legend()

    # naming the x axis
    plt.xlabel('Episode count')
    # naming the y axis
    plt.ylabel('Fragment Vars')

    # giving a title to my graph
    plt.title(f'#nset# var: sc={a[0][1]["ns"]["sc_count"]},'
              f'mc={a[0][1]["ns"]["mc_count"]},'
              f'qo={a[0][1]["ns"]["qo_count"]};\n'
              f'qo_len:{a[0][5]};random={a[0][4]}')

    # function to show the plot
    plt.show()


def generate_trigger(input_xml: Union[str, Path]):
    t = gen_trigger_dict(input_xml, 'nset')
    s = gen_trigger_str(t, ['episodes_fragment_1', 'episodes_fragment_2', 'episodes_fragment_3', 'episodes_fragment_4'])


if __name__ == '__main__':
    xml_source = r'C:\Users\friedrich\zofar_workspace\Test_Modul\src\main\resources\questionnaire.xml'
    calculate()
    generate_trigger(xml_source)
