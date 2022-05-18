from pathlib import Path
from typing import Union, Dict, List
from collections import defaultdict
from zcts.data.xml import read_questionnaire, Variable


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
        output_str += """\t\t</zofar:triggers>\n\n\n\n\n"""

    return output_str


def generate_trigger(input_xml: Union[str, Path], page_name_startswith: str, fragment_var_list: list) -> str:
    t = gen_trigger_dict(input_xml=input_xml,
                         page_name_startswith=page_name_startswith)
    return gen_trigger_str(t, fragment_var_list)


def gen_trigger_dict(input_xml: Union[str, Path], page_name_startswith: str) -> Dict[str, Dict[str, list]]:
    # ToDo: 2022-05-12 CF: add handling of variables from prior pages (parent nodes) that are stored within the json and
    #  are use on the current page
    # ToDo: 2022-05-12 CF: define end-pages as leaf nodes within the subset graph
    # ToDo: 2022-05-12 CF: find a way to mark pages as split pages and process them as such (split-stack & split-trigger)

    q = read_questionnaire(input_xml)

    trigger_dict = defaultdict(lambda: defaultdict(list))

    def _trigger_reset(var: str) -> str:
        return f"""<zofar:scriptItem value="toReset.add('{var}')" />"""

    def _trigger_save(var: str, sc: bool = False) -> str:
        if not sc:
            return f"""<zofar:scriptItem value="toPersist.put('{var}',{var}.valueId)" />"""
        else:
            return f"""<zofar:scriptItem value="toPersist.put('{var}',{var}.value)" />"""

    def _trigger_load(var: str) -> str:
        return f"""<zofar:scriptItem value="toLoad.add('{var}')" />"""

    def _reset_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        if not dropdown:
            return [_trigger_reset(var_name)]
        return [_trigger_reset(var_name),
                _trigger_reset(var_name + 'dropDown'),
                _trigger_reset(var_name + 'missing')]

    def _load_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        if not dropdown:
            return [_trigger_load(var_name)]
        return [_trigger_load(var_name),
                _trigger_load(var_name + 'dropDown'),
                _trigger_load(var_name + 'missing')]

    def _save_trigger(var: Variable) -> List[str]:
        var_name = var.variable.name
        dropdown = var.dropdown
        enum = var.variable.type == 'enum'
        if not dropdown:
            if enum:
                return [_trigger_save(var_name, True)]
            else:
                return [_trigger_save(var_name)]
        return [_trigger_save(var_name),
                _trigger_save(var_name + 'dropDown'),
                _trigger_save(var_name + 'missing')]

    # get all pages that start with the given string
    relevant_pages = [page for page in q.pages if page.uid.startswith(page_name_startswith)]
    for page in relevant_pages:
        for variable in page.var_refs:
            trigger_dict[page.uid]['reset'] += _reset_trigger(variable)
            trigger_dict[page.uid]['load'] += _load_trigger(variable)
            trigger_dict[page.uid]['save'] += _save_trigger(variable)

    return trigger_dict
