import json
import pprint
import re
import os.path
from pathlib import Path
from typing import Union, List, Optional
from lxml import etree
import html
from collections import defaultdict
from zcs.data.xmlutil import read_questionnaire

XML_INPUT_PATH = os.environ.get('XML_INPUT_PATH')
XML_OUTPUT_PATH = os.environ.get('XML_OUTPUT_PATH')

AUTOMATION_COMMENT_START = "AUTOMATION_COMMENT_START"
AUTOMATION_COMMENT_END = "AUTOMATION_COMMENT_END"
AUTOMATION_COMMENT_NONE = "AUTOMATION_COMMENT_NONE"

AUTOMATICALLY_GENERATED_TR_COMMENT = "AUTOMATICALLY GENERATED"

PAGE_NAME_STARTSWITH = "PAGE_NAME_STARTSWITH"
SPLIT_TYPE_DICT = "SPLIT_TYPE_DICT"
SPLIT_TRANSITIONS_LIST = "SPLIT_TRANSITIONS_LIST"
SPLIT_PAGES_LIST = "SPLIT_PAGES_LIST"
SPLIT_TYPE_ORDER = "SPLIT_TYPE_ORDER"
MODULE_END_PAGES = "MODULE_END_PAGES"

TIMESTAMP_VAR = "TIMESTAMP_VAR"
SPLIT_VAR = "SPLIT_VAR"
START_PAGE = "START_PAGE"
END_PAGES = "END_PAGES"

DATA = "DATA"
MODULES_DATA = "MODULE_DATA"
FRAGMENT_VARS_STEM = "FRAGMENT_VARS_STEM"
FRAGMENT_VARS_COUNT = "FRAGMENT_VARS_COUNT"
EPISODE_TYPE_STR = "EPISODE_TYPE_STR"

ZOFAR_PAGE_TAG = "{http://www.his.de/zofar/xml/questionnaire}page"
ZOFAR_TRANSITIONS_TAG = "{http://www.his.de/zofar/xml/questionnaire}transitions"
ZOFAR_TRANSITION_TAG = "{http://www.his.de/zofar/xml/questionnaire}transition"
ZOFAR_TRIGGERS_TAG = "{http://www.his.de/zofar/xml/questionnaire}triggers"
ZOFAR_TRIGGER_TAG = "{http://www.his.de/zofar/xml/questionnaire}trigger"
ZOFAR_SCRIPT_ITEM_TAG = "{http://www.his.de/zofar/xml/questionnaire}scriptItem"
ZOFAR_ACTION_TAG = "{http://www.his.de/zofar/xml/questionnaire}action"
ZOFAR_VARIABLES_TAG = "{http://www.his.de/zofar/xml/questionnaire}variables"
ZOFAR_VARIABLE_TAG = "{http://www.his.de/zofar/xml/questionnaire}variable"


def create_script_item(val: str) -> etree.Element:
    return etree.Element('{http://www.his.de/zofar/xml/questionnaire}scriptItem',
                         attrib={"value": val})


def create_transition(target_str: str, condition_str: str,
                      comment_str: str = 'AUTOMATICALLY GENERATED') -> etree.Element:
    tmp_element = etree.Element(ZOFAR_TRANSITION_TAG, attrib={"target": target_str, "condition": condition_str})
    tmp_comment = etree.Comment(comment_str)
    tmp_element.append(tmp_comment)
    return tmp_element


""" # just a sketch (as yet)
def gen_debug_body_section(header_elements: Optional[List[etree.Element]] = None,
                           body_elements: Optional[List[etree.Element]] = None) -> Optional[etree.Element]:

    if header_elements is None and body_elements is None:
        return None

    # load body section template
    xml_template = Path(os.path.abspath('.'), 'data', 'template', 'body_section_template.xml')
    template_root = etree.parse(xml_template)
    blank_section_element = None
    for element in template_root.iter():
        if element.tag == '{http://www.his.de/zofar/xml/questionnaire}section':
            blank_section_element = element
            break

    # prepare the surrounding section element
    section_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}section')
    section_element.set('uid', 'debug_autogen')
    section_element.set('isAccordion', 'true')
    # prepare the header
    section_header_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}header')
    section_element.append(section_header_element)

    # prepare the body
    section_body_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}body')
    section_element.append(section_body_element)

    return section_element
"""


def section_header_display_text(content_text: str, index: int) -> etree.Element:
    display_element = etree.Element('{http://www.dzhw.eu/zofar/xml/display}text')
    display_element.set('uid', f's_header_text{index}')
    display_element.text = html.escape(content_text)
    return display_element


def get_element_attrib(elemnt: etree.Element, attr: str) -> Optional[str]:
    if hasattr(elemnt, 'attrib'):
        if attr in elemnt.attrib:
            return elemnt.attrib[attr]
    return None


def is_comment_element(elemnt: etree.Element) -> bool:
    if hasattr(elemnt.tag.__class__, '__code__'):
        if hasattr(elemnt.tag.__code__, 'co_name'):
            if elemnt.tag.__code__.co_name:
                return True
    return False


def automation_comment_switch(elemnt: etree.Element) -> str:
    if is_comment_element(elemnt):
        if elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER START'):
            return AUTOMATION_COMMENT_START
        elif elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER END'):
            return AUTOMATION_COMMENT_END
    return AUTOMATION_COMMENT_NONE


def auto_generate_split_type_removal_trigger(xml_element: etree.Element,
                                             input_xml: Union[str, Path],
                                             split_type_to_remove: str) -> None:
    def _create_save_trigger_element(split_type: str, frag_var_ls: List[str]) -> etree.Element:
        new_action_command = f"zofar.frac(zofar.list({','.join(frag_var_list)}),zofar.jsonArr2str(defrac))"
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true",
                                                   "direction": "forward"})
        tmp_comment = etree.Comment(
            f"automatically generated trigger for removing split type '{split_type}' from 'current_split' of episode")
        new_action_element.insert(0, tmp_comment)
        script_item_str_list = [
            f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) ",
            "zofar.assign('toPersist',zofar.map())",
            f"zofar.deleteCurrentSplitType(defrac,episode_index,'{split_type}')",
            "zofar.setJsonProperties('episodeObj',episodeObj,toPersist)",
            "zofar.assign('defrac',zofar.addOrReplaceJson(defrac,episodeObj,zofar.toInteger(episode_index.value)))"]

        [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
         create_script_item is not None]

        return new_action_element

    q = read_questionnaire(input_xml, with_comments=True)

    frag_var_stem = str(q.split_data[DATA][FRAGMENT_VARS_STEM])
    frag_var_count = int(q.split_data[DATA][FRAGMENT_VARS_COUNT])

    frag_var_list = [frag_var_stem + str(i + 1) for i in
                     range(frag_var_count)]

    xml_element.addprevious(_create_save_trigger_element(split_type_to_remove, frag_var_list))


def auto_generate_split_episode_trigger(xml_element: etree.Element,
                                        split_type_dict: dict,
                                        frag_vars_list: List[str]) -> None:
    new_action_command = f"zofar.frac(zofar.list({','.join(frag_vars_list)}),zofar.jsonArr2str(json_array))"
    new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                       attrib={"command": new_action_command,
                                               "onExit": "true",
                                               "direction": "forward"})
    tmp_comment = etree.Comment(
        f"automatically generated trigger for splitting the episode")
    new_action_element.insert(0, tmp_comment)

    escaped_split_type_dict_json = json.dumps(split_type_dict).replace('"', '*')
    script_item_str_list = [
        f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_vars_list)}))))",
        "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) ",
        f"zofar.assign('split_type_dict',zofar.parseJsonObj({escaped_split_type_dict_json}))",
        # DEBUG ToDo remove later
        "zofar.log('split_type_dict: '.concat(split_type_dict),sessionController.participant)",
        # DEBUG ToDo remove later
        "zofar.log('json_array prior to split: '.concat(json_array),sessionController.participant)",
        "zofar.assign('index_json_map', zofar.splitEpisode(json_array,zofar.asNumber(episode_index), split_type_dict))",
        # DEBUG ToDo remove later
        "zofar.log('index_json_map after split: '.concat(index_json_map),sessionController.participant)",
        # DEBUG ToDo remove later
        "zofar.log('index_json_map after split: '.concat(index_json_map),sessionController.participant)",
        "zofar.assign('newSplitIndex',index_json_map['index'])",
        "zofar.assign('json_array',index_json_map['episodes'])",
        # DEBUG ToDo remove later
        "zofar.log('json_array after split: '.concat(json_array),sessionController.participant)",
        "zofar.setVariableValue(episode_index,splitIndex)"]

    [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
     create_script_item is not None]

    return xml_element.addprevious(new_action_element)


def auto_generate_regular_trigger(xml_element: etree.Element,
                                  input_xml: Union[str, Path],
                                  input_page_uid: str) -> None:
    def _create_reset_trigger_element(var_list: list) -> etree.Element:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": "zofar.nothing()", "onExit": "false"})
        tmp_comment = etree.Comment(
            f"automatically generated triggers for resetting variables: {[var.variable.name for var in var_list]}")
        new_action_element.insert(0, tmp_comment)
        script_item_str_list = ["zofar.assign('toReset',zofar.list())"]

        for variable in var_list:
            if variable.dropdown:
                script_item_str_list += [
                    f"toReset.add('{variable.variable.name}')",
                    f"toReset.add('{variable.variable.name}dropDown')",
                    f"toReset.add('{variable.variable.name}missing')"]
            else:
                script_item_str_list.append(f"toReset.add('{variable.variable.name}')")

        script_item_str_list.append("zofar.resetVars(toReset)")

        [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
         create_script_item is not None]
        return new_action_element

    def _create_load_trigger_element(var_list: list, frag_var_ls: List[str]) -> etree.Element:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": "zofar.nothing()", "onExit": "false"})

        tmp_comment = etree.Comment(
            f"automatically generated triggers for loading variables: {[var.variable.name for var in var_list]}; additionally sets variables: 'v_startmonth', 'v_startyear', 'v_endmonth', 'v_endyear'")
        new_action_element.insert(0, tmp_comment)

        script_item_str_list = [
            f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value)))",
            "zofar.assign('monthMap',zofar.map('1=ao1,2=ao2,3=ao3,4=ao4,5=ao5,6=ao6,7=ao7,8=ao8,9=ao9,10=ao10,11=ao11,12=ao12'))",
            "zofar.assign('yearMap',zofar.map('2018=ao1,2019=ao2,2020=ao3,2021=ao4,2022=ao5,2023=ao6,2024=ao7'))",
            "zofar.setVariableValue(v_startmonth,zofar.getFromMap(monthMap,zofar.getMonthFromStamp(startDate)+1))",
            "zofar.setVariableValue(v_startyear,zofar.getFromMap(yearMap,zofar.getYearFromStamp(startDate)))",
            "zofar.setVariableValue(v_endmonth,zofar.getFromMap(monthMap,zofar.getMonthFromStamp(endDate)+1))",
            "zofar.setVariableValue(v_endyear,zofar.getFromMap(yearMap,zofar.getYearFromStamp(endDate)))",
            "zofar.assign('toLoad',zofar.list())"]

        for index, variable in enumerate(var_list):
            if variable.dropdown:
                script_item_str_list.append(f"toLoad.add('{variable.variable.name}')")
                script_item_str_list.append(f"toLoad.add('{variable.variable.name}dropDown')")
                script_item_str_list.append(f"toLoad.add('{variable.variable.name}missing')")
            else:
                script_item_str_list.append(f"toLoad.add('{variable.variable.name}')")
        script_item_str_list.append("zofar.getJsonProperties(episodeObj,toLoad)")

        [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
         script_item_str is not None]

        return new_action_element

    def _create_save_trigger_element(var_list: list, frag_var_ls: List[str]) -> etree.Element:
        new_action_command = f"zofar.frac(zofar.list({','.join(frag_var_list)}),zofar.jsonArr2str(defrac))"
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true"})
        tmp_comment = etree.Comment(
            f"automatically generated triggers for saving variables: {[var.variable.name for var in var_list]}")
        new_action_element.insert(0, tmp_comment)

        script_item_str_list = [
            f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) ",
            "zofar.assign('toPersist',zofar.map())"]
        for index, variable in enumerate(var_list):
            if variable.dropdown:
                script_item_str_list.append(
                    f"toPersist.put('{variable.variable.name}',{variable.variable.name}.valueId)")
                script_item_str_list.append(
                    f"toPersist.put('{variable.variable.name}dropDown',{variable.variable.name}dropDown.value)")
                script_item_str_list.append(
                    f"toPersist.put('{variable.variable.name}missing',{variable.variable.name}missing.value)")

            else:
                if variable.variable.type == 'enum':
                    script_item_str_list.append(
                        f"toPersist.put('{variable.variable.name}',{variable.variable.name}.valueId)")
                else:
                    script_item_str_list.append(
                        f"toPersist.put('{variable.variable.name}',{variable.variable.name}.value)")

        script_item_str_list += [
            "zofar.setJsonProperties('episodeObj',episodeObj,toPersist)",
            "zofar.assign('defrac',zofar.addOrReplaceJson(defrac,episodeObj,zofar.toInteger(episode_index.value)))"]

        script_item_str_list.append("zofar.assign('toLoad',zofar.list())")
        for index, variable in enumerate(var_list):
            script_item_str_list.append(f"toLoad.add('{variable.variable.name}')")
        script_item_str_list.append("zofar.getJsonProperties(episodeObj,toLoad)")

        [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
         create_script_item is not None]

        return new_action_element

    q = read_questionnaire(input_xml, with_comments=True)

    # get the page object for the page uid
    relevant_page = [page_obj for page_obj in q.pages if page_obj.uid == input_page_uid][0]

    frag_var_stem = str(q.split_data[DATA][FRAGMENT_VARS_STEM])
    frag_var_count = int(q.split_data[DATA][FRAGMENT_VARS_COUNT])

    frag_var_list = [frag_var_stem + str(i + 1) for i in
                     range(frag_var_count)]

    xml_element.addprevious(_create_reset_trigger_element(list(relevant_page.var_refs)))
    xml_element.addprevious(_create_load_trigger_element(list(relevant_page.var_refs), frag_var_list))
    xml_element.addprevious(_create_save_trigger_element(list(relevant_page.var_refs), frag_var_list))


def _variable_declaration(var_name: str, var_type: str):
    return etree.Element(ZOFAR_VARIABLE_TAG,
                         attrib={"name": var_name, "type": var_type})


def _insert_fragment_variable_declarations(element_tree: etree.Element,
                                           fragment_var_stem: str,
                                           fragment_var_count: int):
    declared_fragment_var_set = set()

    for elm in element_tree.find(ZOFAR_VARIABLES_TAG).iterchildren():
        if is_comment_element(elm):
            continue
        var_name = get_element_attrib(elm, 'name')
        var_type = get_element_attrib(elm, 'type')
        if var_name.startswith(fragment_var_stem):
            tmp_str = var_name[len(fragment_var_stem):]
            count_match = re.match(r'^\d+', tmp_str)
            if count_match is not None:
                if int(count_match[0]) > fragment_var_count or var_name in declared_fragment_var_set:
                    elm.getparent().remove(elm)
                else:
                    declared_fragment_var_set.add(var_name)

    all_fragment_var_set = {fragment_var_stem + str(i + 1) for i in range(fragment_var_count)}
    not_declared_fragment_var_list = list(all_fragment_var_set.symmetric_difference(declared_fragment_var_set))
    not_declared_fragment_var_list.sort()

    for frag_var_name in not_declared_fragment_var_list:
        element_tree.find(ZOFAR_VARIABLES_TAG).append(
            _variable_declaration(frag_var_name, 'string'))


def _duplicate_str(matchobj: re.Match):
    i = matchobj.group(0)
    return str(i) * 2


def split_start_end_pages_well_formed(input_dict: dict, pages_start_with: str,
                                      list_of_all_pagenames: List[str]) -> bool:
    end_pages_set = set()
    start_pages_set = set()

    for split_type_name, split_type_data in input_dict.items():
        if split_type_data[START_PAGE] in start_pages_set:
            pprint.pprint(input_dict)
            raise ValueError(f'Start page already used for other split type: {split_type_data[START_PAGE]}')
        start_pages_set.add(split_type_data[START_PAGE])

        for page in split_type_data[END_PAGES]:
            if page == '':
                continue
            if page in end_pages_set:
                pprint.pprint(input_dict)
                raise ValueError(f'End page already used for other split type: {page}')
            if page in start_pages_set and page != split_type_data[START_PAGE] and len(split_type_data[END_PAGES]) == 1:
                pprint.pprint(input_dict)
                raise ValueError(f'Page found in both start pages and end pages: {page}')
            end_pages_set.add(page)

    non_existing_pages = [page for page in end_pages_set.union(start_pages_set) if page not in list_of_all_pagenames]

    if non_existing_pages:
        raise ValueError(
            f'the following Page Names do not exist in the QML: {non_existing_pages}')

    not_well_formed_pagenames = [page_name for page_name in end_pages_set.union(start_pages_set) if
                                 not page_name.startswith(pages_start_with)]

    if not_well_formed_pagenames:
        raise ValueError(
            f'the following pagenames do not start with the given string '
            f'"{pages_start_with}": {not_well_formed_pagenames}')

    return True


def main(xml_input_path: Union[Path, str], xml_output_path: Union[Path, str]):
    etree.register_namespace('zofar', 'http://www.his.de/zofar/xml/questionnaire')
    etree.register_namespace('display', 'http://www.dzhw.eu/zofar/xml/display')

    # prepare paths
    xml_input_path = Path(xml_input_path)
    xml_output_path = Path(xml_output_path)

    # load existing QML file
    q = read_questionnaire(xml_input_path, with_comments=True)

    xml_template = bytes(xml_input_path.read_text(encoding='utf-8'), 'utf-8')

    parser = etree.XMLParser(remove_blank_text=True)
    template_root = etree.fromstring(xml_template, parser)
    for element in template_root.iterchildren():
        if is_comment_element(element):
            # evaluate comments here, if needed
            pass

    frag_var_stem = str(q.split_data[DATA][FRAGMENT_VARS_STEM])
    frag_var_count = int(q.split_data[DATA][FRAGMENT_VARS_COUNT])

    frag_var_list = [frag_var_stem + str(i + 1) for i in range(frag_var_count)]

    calendar_modules_startswith_list = [val[PAGE_NAME_STARTSWITH] for key, val in q.split_data[MODULES_DATA].items()]

    # ToDo run frag var declaration / check

    # this is where we store the generated transitions in correct order
    generated_split_type_transitions_dict = defaultdict(list)
    generated_current_split_removal_trigger = defaultdict(list)
    generated_split_episode_trigger = defaultdict(list)

    if q.split_data[MODULES_DATA]:
        # iterate over all modules
        for module_name_str, module_data in q.split_data[MODULES_DATA].items():
            try:
                # get all ducks in a row...
                module_page_name_startswith = module_data[PAGE_NAME_STARTSWITH]
                module_type_str = module_data[EPISODE_TYPE_STR]
                module_split_type_dict = module_data[SPLIT_TYPE_DICT]
                assert split_start_end_pages_well_formed(module_split_type_dict,
                                                         module_page_name_startswith,
                                                         [page.uid for page in q.pages])
                module_split_type_order = module_data[SPLIT_TYPE_ORDER]
                module_end_pages = module_data[MODULE_END_PAGES]

                split_types_not_found = [split_type for split_type in module_data[SPLIT_TYPE_ORDER] if
                                         split_type not in module_split_type_dict.keys()]
                if split_types_not_found:
                    raise KeyError(
                        f'Split Type(s) from {SPLIT_TYPE_ORDER} not found in {SPLIT_TYPE_DICT}: "{split_types_not_found}"')
            except KeyError as e:
                print(f'Module Data Dictionary for Module "{module_name_str}"')
                pprint.pprint(module_data)
                raise KeyError(e)

            # iterate over all split types in SPLIT_TYPE_DICT of the current module
            for list_index, split_type_name in enumerate(module_split_type_order):
                try:
                    split_type_data = module_split_type_dict[split_type_name]
                    if split_type_name not in module_split_type_order:
                        raise KeyError(
                            f'Split Type from {SPLIT_TYPE_DICT} not found in {SPLIT_TYPE_ORDER}: "{split_type_name}"')
                    transition_target = split_type_data[START_PAGE]
                    split_type_end_pages_list = [page for page in split_type_data[END_PAGES] if page != '']
                    transition_condition = f"zofar.hasCurrentSplitType(defrac, episode_index, '{split_type_name}')"
                    for page in module_end_pages:
                        generated_split_type_transitions_dict[page].append(
                            create_transition(transition_target, transition_condition))

                    for split_type_end_page in split_type_end_pages_list:
                        # add triggers:
                        generated_current_split_removal_trigger[split_type_end_page].append(split_type_name)
                        # add transitions:
                        if (list_index + 1) < len(split_type_end_pages_list):
                            for split_type_name_rest in module_split_type_order[list_index + 1:]:
                                split_type_end_page_transition_target = module_split_type_dict[split_type_name_rest][
                                    START_PAGE]
                                split_type_end_page_transition_condition = f"zofar.hasCurrentSplitType(defrac, " \
                                                                           f"episode_index, '{split_type_name_rest}')"
                                generated_split_type_transitions_dict[split_type_end_page].append(
                                    create_transition(split_type_end_page_transition_target,
                                                      split_type_end_page_transition_condition))

                except KeyError as e:
                    print(f'Split Type Dictionary for Module "{module_name_str}", Split Type "{split_type_name}"')
                    pprint.pprint(module_split_type_dict)
                    raise KeyError(e)

    _insert_fragment_variable_declarations(template_root, frag_var_stem, frag_var_count)

    processed_pages_list = []

    for page in template_root.iterchildren(ZOFAR_PAGE_TAG):
        page_uid = get_element_attrib(page, 'uid')

        remove_mode_switch = False
        for triggers in page.iterchildren(ZOFAR_TRIGGERS_TAG):
            automation_comment_list = [automation_comment_switch(elmn) for elmn in
                                       page.find(ZOFAR_TRIGGERS_TAG).iter()]
            if AUTOMATION_COMMENT_START in automation_comment_list and \
                    AUTOMATION_COMMENT_END in automation_comment_list[
                                              automation_comment_list.index(AUTOMATION_COMMENT_START) + 1:]:
                # track progress
                processed_pages_list.append(page_uid)

                trigger_to_delete = None
                for trigger in triggers.iterchildren():
                    if trigger_to_delete is not None:
                        trigger_to_delete.getparent().remove(trigger_to_delete)
                        trigger_to_delete = None

                    if automation_comment_switch(trigger) == AUTOMATION_COMMENT_END:
                        remove_mode_switch = False

                        # input new trigger - edit in-place, does not return anything
                        # 1st: remove split types from episode JSON

                        if page_uid in generated_current_split_removal_trigger:
                            for split_type_to_rm in generated_current_split_removal_trigger[page_uid]:
                                auto_generate_split_type_removal_trigger(xml_element=trigger,
                                                                         input_xml=xml_input_path,
                                                                         split_type_to_remove=split_type_to_rm)

                        # 2nd: other trigger
                        if any([page_uid.startswith(start_str) for start_str in calendar_modules_startswith_list]):
                            auto_generate_regular_trigger(xml_element=trigger, input_xml=xml_input_path,
                                                          input_page_uid=page_uid)

                        for module_name_str, module_data in q.split_data[MODULES_DATA].items():
                            if page_uid.startswith(module_data[PAGE_NAME_STARTSWITH]):
                                if page_uid in module_data[MODULE_END_PAGES]:
                                    auto_generate_split_episode_trigger(xml_element=trigger,
                                                                        split_type_dict=module_data[SPLIT_TYPE_DICT],
                                                                        frag_vars_list=frag_var_list)
                        break

                    if remove_mode_switch:
                        if automation_comment_switch(trigger) != AUTOMATION_COMMENT_END:
                            trigger_to_delete = trigger
                            continue
                    if automation_comment_switch(trigger) == AUTOMATION_COMMENT_START:
                        remove_mode_switch = True
            else:
                if any([page_uid.startswith(start_str) for start_str in calendar_modules_startswith_list]):
                    print(f'Missing Automated Trigger Comments for Page:"{page_uid}"')
        # deal with transitions - delete old transitions
        if page.find(ZOFAR_TRANSITIONS_TAG) is not None:
            for transition in page.find(ZOFAR_TRANSITIONS_TAG).iterchildren():
                if transition.tag == ZOFAR_TRANSITION_TAG:
                    for comment_candidate in transition.iter():
                        if is_comment_element(comment_candidate):
                            if comment_candidate.text == "AUTOMATICALLY GENERATED":
                                transition.getparent().remove(transition)

        # deal with transitions - add new transitions
        if page_uid in generated_split_type_transitions_dict.keys():
            if page.find(ZOFAR_TRANSITIONS_TAG) is None:
                raise ValueError(f'no "transitons" tag found on page: {page_uid}')
            else:
                transitions_element = page.find(ZOFAR_TRANSITIONS_TAG)

                for transition_index, transition_element in enumerate(generated_split_type_transitions_dict[page_uid]):
                    transitions_element.insert(transition_index, transition_element)

    print(f'{processed_pages_list=}')

    output_xml_string = etree.tostring(template_root, pretty_print=True, method='xml').decode('utf-8')

    output_xml_string = '\n'.join([re.sub(r'^ +', _duplicate_str, line) for line in output_xml_string.split('\n')])

    output_xml_file = Path(xml_output_path)
    output_xml_file.write_text(output_xml_string, 'utf-8')


if __name__ == '__main__':
    main(XML_INPUT_PATH, XML_OUTPUT_PATH)
