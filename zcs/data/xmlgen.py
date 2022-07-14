import math
import sys

from art import text2art
import json
import pprint
import re
import os.path
from pathlib import Path
from typing import Union, List, Optional, Set, Dict, Tuple
from lxml import etree
import html
from collections import defaultdict
from zcs.data.xmlutil import read_questionnaire, Transition, Questionnaire

XML_INPUT_PATH = os.environ.get('XML_INPUT_PATH')
XML_OUTPUT_PATH = os.environ.get('XML_OUTPUT_PATH')

DEBUG = False
if 'DEBUG' in os.environ:
    if os.environ['DEBUG'].upper().strip() == 'TRUE':
        DEBUG = True

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
SPLIT_DATA = "SPLIT_DATA"
MODULES_DATA = "MODULE_DATA"
FRAGMENT_VARS_STEM = "FRAGMENT_VARS_STEM"
FRAGMENT_VARS_COUNT = "FRAGMENT_VARS_COUNT"
EPISODE_TYPE_STR = "EPISODE_TYPE_STR"

ZOFAR_NAMESPACE = "{http://www.his.de/zofar/xml/questionnaire}"
ZOFAR_QUESTIONNAIRE_TAG = f"{ZOFAR_NAMESPACE}questionnaire"
ZOFAR_NAME_TAG = f"{ZOFAR_NAMESPACE}name"
ZOFAR_PAGE_TAG = f"{ZOFAR_NAMESPACE}page"
ZOFAR_TRANSITIONS_TAG = f"{ZOFAR_NAMESPACE}transitions"
ZOFAR_TRANSITION_TAG = f"{ZOFAR_NAMESPACE}transition"
ZOFAR_TRIGGERS_TAG = f"{ZOFAR_NAMESPACE}triggers"
ZOFAR_TRIGGER_TAG = f"{ZOFAR_NAMESPACE}trigger"
ZOFAR_SCRIPT_ITEM_TAG = f"{ZOFAR_NAMESPACE}scriptItem"
ZOFAR_ACTION_TAG = f"{ZOFAR_NAMESPACE}action"
ZOFAR_VARIABLES_TAG = f"{ZOFAR_NAMESPACE}variables"
ZOFAR_VARIABLE_TAG = f"{ZOFAR_NAMESPACE}variable"
ZOFAR_SECTION_TAG = f"{ZOFAR_NAMESPACE}section"
ZOFAR_HEADER_TAG = f"{ZOFAR_NAMESPACE}header"
ZOFAR_BODY_TAG = f"{ZOFAR_NAMESPACE}body"
ZOFAR_TITLE_TAG = f"{ZOFAR_NAMESPACE}title"
ZOFAR_DISPLAY_TAG = f"{ZOFAR_NAMESPACE}display"
ZOFAR_TEXT_TAG = f"{ZOFAR_NAMESPACE}text"
DISPLAY_NAMESPACE = "{http://www.dzhw.eu/zofar/xml/display}"
ZOFAR_DISPLAY_TEXT_TAG = f"{DISPLAY_NAMESPACE}text"


def create_ascii_art_comments(input_str: str, font: str = 'standard') -> List[etree.Comment]:
    ascii_art = text2art(input_str, font)
    return [etree.Comment('###  ' + line) for line in ascii_art.split('\n') if len(line) > 0]


def is_ascii_art_comment(input_element: etree.Element) -> bool:
    if is_comment_element(input_element):
        if input_element.text.startswith('###'):
            return True
    return False


def remove_all_ascii_art_comments(input_root: etree.Element):
    for root_element in input_root.iterchildren():
        if is_ascii_art_comment(root_element):
            root_element.getparent().remove(root_element)


def create_script_item(val: str) -> etree.Element:
    return etree.Element('{http://www.his.de/zofar/xml/questionnaire}scriptItem',
                         attrib={"value": val})


def create_transition(target_str: str, condition_str: Optional[str] = None,
                      comment_str: str = 'AUTOMATICALLY GENERATED') -> etree.Element:
    tmp_element = etree.Element(ZOFAR_TRANSITION_TAG, attrib={"target": target_str})
    if condition_str is not None:
        if isinstance(condition_str, str):
            condition_str = condition_str.strip()
            if condition_str != "":
                tmp_element = etree.Element(ZOFAR_TRANSITION_TAG,
                                            attrib={"target": target_str,
                                                    "condition": condition_str})
    tmp_comment = etree.Comment(comment_str)
    tmp_element.append(tmp_comment)
    return tmp_element


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


def find_all_html_escaped_chars(s: str) -> set:
    return set(re.findall(r'(&#.{,5};)', s))


def automation_comment_switch(elemnt: etree.Element) -> str:
    if is_comment_element(elemnt):
        if elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER START'):
            return AUTOMATION_COMMENT_START
        elif elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER END'):
            return AUTOMATION_COMMENT_END
    return AUTOMATION_COMMENT_NONE


def delete_from_current_split_trigger_element(split_type: Union[List[str], str],
                                              frag_var_ls: List[str]) -> etree.Element:
    new_action_command = f"zofar.frac(zofar.list({','.join(frag_var_ls)}),zofar.jsonArr2str(json_array))"
    new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                       attrib={"command": new_action_command,
                                               "onExit": "true",
                                               "direction": "forward"})
    tmp_comment = etree.Comment(
        f"automatically generated trigger for removing split type '{split_type}' from 'current_split' of episode")
    new_action_element.insert(0, tmp_comment)
    script_item_str_list = [
        f"zofar.assign('json_array',zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))"]
    if isinstance(split_type, str):
        script_item_str_list += [f"zofar.assign('json_array',"
                                 f"zofar.deleteCurrentSplitType(json_array,zofar.toInteger(episode_index.value),'{split_type}'))"]
    elif isinstance(split_type, list):
        list_of_split_types_str = "'" + "','".join(split_type) + "'"
        script_item_str_list += [f"zofar.assign('json_array',"
                                 f"zofar.deleteCurrentSplitType(json_array,"
                                 f"zofar.toInteger(episode_index.value),zofar.list({list_of_split_types_str})))"]
    else:
        raise TypeError(f"Function only accepts str or List[str]; given type was: {type(split_type)}")

    [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
     create_script_item is not None]

    return new_action_element


def auto_generate_split_type_removal_trigger(xml_element: etree.Element,
                                             input_xml: Union[str, Path],
                                             split_type_to_remove: str) -> None:
    q = read_questionnaire(input_xml, with_comments=True)

    frag_var_list = generate_frag_var_list_from_split_data(q.split_data[DATA])

    xml_element.addprevious(delete_from_current_split_trigger_element(split_type_to_remove, frag_var_list))


def auto_generate_split_episode_trigger_element(split_type_dict: dict,
                                                frag_vars_list: List[str],
                                                condition: Optional[str] = None) -> etree.Element:
    new_action_command = f"zofar.frac(zofar.list({','.join(frag_vars_list)}),zofar.jsonArr2str(json_array))"
    if condition is None:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true",
                                                   "direction": "forward"})
    else:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true",
                                                   "direction": "forward",
                                                   "condition": condition})
    tmp_comment = etree.Comment(
        f"automatically generated trigger for splitting the episode")
    new_action_element.insert(0, tmp_comment)

    escaped_split_type_dict_json = json.dumps(split_type_dict).replace('"', '*')
    script_item_str_list = [
        f"zofar.assign('json_array',zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_vars_list)}))))",
        "zofar.assign('episodeObj',zofar.getOrCreateJson(json_array,zofar.toInteger(episode_index.value))) ",
        f"zofar.assign('split_type_dict',zofar.parseJsonObj('{escaped_split_type_dict_json}'))"]

    if DEBUG:
        script_item_str_list.append(
            "zofar.log('split_type_dict: '.concat(split_type_dict),sessionController.participant)")
        script_item_str_list.append(
            "zofar.log('json_array prior to split: '.concat(json_array),sessionController.participant)")
    script_item_str_list.append(
        "zofar.assign('index_json_map', zofar.splitEpisode(json_array,zofar.toInteger(episode_index.value), split_type_dict))")
    if DEBUG:
        script_item_str_list.append(
            "zofar.log('index_json_map after split: '.concat(index_json_map),sessionController.participant)")
    script_item_str_list.append("zofar.assign('newSplitIndex',index_json_map['index'])")
    if DEBUG:
        script_item_str_list.append(
            "zofar.log('newSplitIndex after split: '.concat(newSplitIndex),sessionController.participant)")
    script_item_str_list.append("zofar.assign('json_array',index_json_map['episodes'])")
    if DEBUG:
        script_item_str_list.append(
            "zofar.log('json_array after split: '.concat(json_array),sessionController.participant)")
    script_item_str_list.append("zofar.setVariableValue(episode_index,newSplitIndex)")

    [new_action_element.append(create_script_item(script_item_str)) for script_item_str in script_item_str_list if
     create_script_item is not None]
    return new_action_element


def auto_generate_split_episode_trigger(xml_element: etree.Element,
                                        split_type_dict: dict,
                                        frag_vars_list: List[str]) -> None:
    return xml_element.addprevious(auto_generate_split_episode_trigger_element(split_type_dict, frag_vars_list))


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

        # ToDo: find out why sometimes the variables do not reset!
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
            f"automatically generated triggers for loading variables: {[var.variable.name for var in var_list]}; additionally sets variables: 'startmonth', 'startyear', 'endmonth', 'endyear'")
        new_action_element.insert(0, tmp_comment)

        script_item_str_list = [
            f"zofar.assign('json_array',zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(json_array,zofar.toInteger(episode_index.value)))",
            "zofar.assign('monthMap',zofar.map('1=ao1,2=ao2,3=ao3,4=ao4,5=ao5,6=ao6,7=ao7,8=ao8,9=ao9,10=ao10,11=ao11,12=ao12'))",
            "zofar.assign('yearMap',zofar.map('1970=ao1,1971=ao2,1972=ao3,1973=ao4,1974=ao5,1975=ao6,1976=ao7,1977=ao8,1978=ao9,1979=ao10,1980=ao11,1981=ao12,1982=ao13,1983=ao14,1984=ao15,1985=ao16,1986=ao17,1987=ao18,1988=ao19,1989=ao20,1990=ao21,1991=ao22,1992=ao23,1993=ao24,1994=ao25,1995=ao26,1996=ao27,1997=ao28,1998=ao29,1999=ao30,2000=ao31,2001=ao32,2002=ao33,2003=ao34,2004=ao35,2005=ao36,2006=ao37,2007=ao38,2008=ao39,2009=ao40,2010=ao41,2011=ao42,2012=ao43,2013=ao44,2014=ao45,2015=ao46,2016=ao47,2017=ao48,2018=ao49,2019=ao50,2020=ao51,2021=ao52,2022=ao53,2023=ao54,2024=ao55,2025=ao56,2026=ao57,2027=ao58,2028=ao59,2029=ao60,2030=ao61,2031=ao62,2032=ao63,2033=ao64,2034=ao65,2035=ao66,2036=ao67,2037=ao68,2038=ao69,2039=ao70,2040=ao71'))",
            "zofar.assign('startDate',zofar.getJsonProperty(episodeObj, 'startDate'))",
            "zofar.assign('endDate',zofar.getJsonProperty(episodeObj, 'endDate'))",
            "zofar.setVariableValue(startmonth,zofar.getFromMap(monthMap,zofar.getMonthFromStamp(startDate)+1))",
            "zofar.setVariableValue(startyear,zofar.getFromMap(yearMap,zofar.getYearFromStamp(startDate)))",
            "zofar.setVariableValue(endmonth,zofar.getFromMap(monthMap,zofar.getMonthFromStamp(endDate)+1))",
            "zofar.setVariableValue(endyear,zofar.getFromMap(yearMap,zofar.getYearFromStamp(endDate)))",
            "zofar.assign('toLoad',zofar.list())"]

        vars_to_exclude = ['startmonth', 'startyear', 'endmonth', 'endyear']
        var_list = [v for v in var_list if v.variable.name not in vars_to_exclude]

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
        new_action_command = f"zofar.frac(zofar.list({','.join(frag_var_list)}),zofar.jsonArr2str(json_array))"
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true"})
        tmp_comment = etree.Comment(
            f"automatically generated triggers for saving variables: {[var.variable.name for var in var_list]}")
        new_action_element.insert(0, tmp_comment)

        script_item_str_list = [
            f"zofar.assign('json_array',zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_ls)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(json_array,zofar.toInteger(episode_index.value))) ",
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
            "zofar.assign('json_array',zofar.addOrReplaceJson(json_array,episodeObj,zofar.toInteger(episode_index.value)))"]

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

    frag_var_list = generate_frag_var_list_from_split_data(q.split_data[DATA])

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
        # if stripped start page name string is empty
        if split_type_data[START_PAGE].strip() == "":
            print(f'{START_PAGE}: JSON Key "{START_PAGE}" for PAGE_STARTSWITH="{pages_start_with}" is empty!')
        else:
            if split_type_data[START_PAGE] in start_pages_set:
                pprint.pprint(input_dict)
                raise ValueError(f'Start page already used for other split type: {split_type_data[START_PAGE]}')
            start_pages_set.add(split_type_data[START_PAGE])

        for page in split_type_data[END_PAGES]:
            # if stripped end page name string is empty
            if page == '':
                print(f'{END_PAGES}: JSON Key for end page in PAGE_STARTSWITH="{pages_start_with}" is empty!')
                continue
            else:
                # if no start page has been declared, but an end page has been found
                if len(start_pages_set) == 0:
                    raise ValueError(
                        f'{END_PAGES}: End page {page} found, but no start page declared for PAGE_STARTSWITH="{pages_start_with}"')
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


def debug_accordion(uid_str: str, title_text: str, body_text: str) -> etree.Element:
    section_element = etree.Element(ZOFAR_SECTION_TAG, attrib={"uid": uid_str, "isaccordion": "true"})
    header_element = etree.Element(ZOFAR_HEADER_TAG)
    title_element = etree.Element(ZOFAR_TITLE_TAG, attrib={"uid": "t"})
    title_element.text = f"#{{layout.BOLD_START}} {title_text} #{{layout.BOLD_END}}"
    header_element.append(title_element)
    section_element.append(header_element)

    body_element = etree.Element(ZOFAR_BODY_TAG, attrib={"uid": "b"})
    display_element = etree.Element(ZOFAR_DISPLAY_TAG, attrib={"uid": "debug"})
    text_element = etree.Element(ZOFAR_DISPLAY_TEXT_TAG, attrib={"uid": "debugtext"})
    text_element.text = body_text
    display_element.append(text_element)
    body_element.append(display_element)
    section_element.append(body_element)
    return section_element


def has_current_split_zofar_function(split_type_name: str, frag_var_list: list) -> str:
    return f"zofar.hasCurrentSplitType(zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_list)}))" \
           f"), zofar.toInteger(episode_index.value), '{split_type_name}')"


def has_current_split_list_zofar_function(split_type_name_list: List[str], frag_var_list: list) -> str:
    split_type_list_str = "'" + "','".join(split_type_name_list) + "'"
    return f"zofar.hasCurrentSplitType(zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_list)}))" \
           f"), zofar.toInteger(episode_index.value), zofar.list({split_type_list_str}))"


def do_split_on_end_page_candidate_function(split_type_list: List[str], frag_var_list: list) -> str:
    split_type_list_str = "'" + "','".join(split_type_list) + "'"
    return f"zofar.doSplitOnEndPageCandidate(zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list({','.join(frag_var_list)}))" \
           f"), zofar.toInteger(episode_index.value), zofar.list({split_type_list_str}))"


def soundness_check_module_split_data(module_data_dict: dict, module_split_type_dict: dict) -> bool:
    # check for split types (declaration data and split type order should show the same entries)
    assert soundness_check_split_types(module_data_dict, module_split_type_dict)
    # soundness check for split type end pages (in every split type there must be at least one end page in END_PAGES without any conditions)
    assert soundness_check_split_type_end_pages(module_data_dict, module_split_type_dict)
    assert soundness_check_all_module_pages_startwith(module_data_dict)
    return True


def soundness_check_all_modules_data(all_modules_data_dict: dict) -> bool:
    soundness_check_unique_module_page_startswith(all_modules_data_dict)
    soundness_check_unique_module_end_pages(all_modules_data_dict)
    return True


def soundness_check_unique_module_page_startswith(all_modules_data_dict: dict) -> bool:
    # soundness check for uniqueness of module page name startswith
    startswith_module_dict = defaultdict(list)
    [startswith_module_dict[module_data[PAGE_NAME_STARTSWITH]].append(module_name) for module_name, module_data in
     all_modules_data_dict.items()]

    duplicate_startswith = {key: val for key, val in startswith_module_dict.items() if len(val) > 1}
    if duplicate_startswith != {}:
        pprint.pprint(duplicate_startswith)
        raise KeyError(
            f'Module end pages {duplicate_startswith.keys()} found in multiple modules: '
            f'{pprint.pformat(duplicate_startswith)}')
    return True


def soundness_check_unique_module_end_pages(all_modules_data_dict: dict) -> bool:
    # soundness check for uniqueness of module end pages
    end_pages_module_dict = defaultdict(list)
    for module_name, module_data in all_modules_data_dict.items():
        if module_data[MODULE_END_PAGES] == ['']:
            continue
        else:
            for end_page_name in module_data[MODULE_END_PAGES]:
                end_pages_module_dict[end_page_name].append(module_name)
    multiple_pages = {key: val for key, val in end_pages_module_dict.items() if len(val) > 1}
    if multiple_pages != {}:
        pprint.pprint(multiple_pages)
        raise KeyError(f'Module end pages {multiple_pages.keys()} found in multiple modules: '
                       f'{pprint.pformat(multiple_pages)}')
    return True


def soundness_check_all_module_pages_startwith(module_data_dict: dict) -> bool:
    page_names_startwith = module_data_dict[PAGE_NAME_STARTSWITH]
    malformed_module_end_page_names = [page for page in module_data_dict[MODULE_END_PAGES] if page != '' and
                                       not str(page).startswith(page_names_startwith)]

    malformed_split_type_start_pages = [split_type_dict[START_PAGE] for split_type_name, split_type_dict in
                                        module_data_dict[SPLIT_TYPE_DICT].items() if
                                        split_type_dict[START_PAGE] != '' and not split_type_dict[
                                            START_PAGE].startswith(page_names_startwith)]
    malformed_split_type_start_pages = [item for items in [[k for k, _ in key.items()] for key in
                                                           [split_type_dict[END_PAGES] for
                                                            split_type_name, split_type_dict in
                                                            module_data_dict[SPLIT_TYPE_DICT].items()]] for item in
                                        items if not item.startswith(page_names_startwith)]
    malformed_split_type_end_pages = [page for pages in [split_type_dict[END_PAGES].keys() for split_type_dict in
                                                         module_data_dict[SPLIT_TYPE_DICT].values()] for page in pages
                                      if not page.startswith(page_names_startwith)]
    if any(malformed_module_end_page_names):
        raise KeyError(f'Malformed module end page name(s): {malformed_module_end_page_names}')
    if any(malformed_split_type_start_pages):
        raise KeyError(f'Malformed module end page name(s): {malformed_module_end_page_names}')
    if any(malformed_split_type_end_pages):
        raise KeyError(f'Malformed module end page name(s): {malformed_module_end_page_names}')
    return True


def flatten(input_list):
    output_list = []
    for element in input_list:
        if isinstance(element, list):
            [output_list.append(entry) for entry in flatten(element)]
        else:
            output_list.append(element)
    return output_list


def soundness_check_split_types(module_data_dict: dict, module_split_type_dict: dict) -> bool:
    # soundness check for split types (declaration data and split type order should show the same entries)
    split_types_not_found = [split_type for split_type in module_data_dict[SPLIT_TYPE_ORDER] if
                             split_type not in module_split_type_dict.keys() and split_type.strip() != '']
    if split_types_not_found:
        raise KeyError(
            f'Split Type(s) from {SPLIT_TYPE_ORDER} not found in {SPLIT_TYPE_DICT}: "{split_types_not_found}"')
    return True


def soundness_check_split_type_end_pages(module_data_dict: dict, module_split_type_dict: dict) -> bool:
    # soundness check for split type end pages (in every split type there must be at least one end page in END_PAGES without any conditions)
    for split_type, split_type_data in module_split_type_dict.items():
        if split_type_data[SPLIT_VAR] == [{"": ""}]:
            continue
        split_or_list = []
        for split_end_page, split_end_condition_list in split_type_data[END_PAGES].items():
            for split_condition in split_end_condition_list:
                split_and_list = []
                if len(split_condition) == 0:
                    continue
                for split_cond_var, split_cond_val in split_condition.items():
                    split_and_list.append(f'{split_cond_var}.value == {split_cond_val}')
                if len(split_and_list) > 0:
                    split_or_list.append(split_and_list)

            split_condition_str = '(' + ') or ('.join(
                [' and '.join(entry) for entry in split_or_list]) + ')'
            # ToDo: what to do with this condition string?

        if not any(
                [end_page for end_page, end_page_val in split_type_data[END_PAGES].items() if
                 len(end_page_val) == 0 or end_page_val == [{}]]):
            raise KeyError(
                f'"{split_type=}" does not have any end pages without conditions! There must be at least one page in "{END_PAGES}" without conditions.')
    return True


def create_zofar_page(page_uid: str,
                      list_of_header_elements: Optional[List[etree._Element]] = None,
                      list_of_body_elements: Optional[List[etree._Element]] = None,
                      list_of_triggers: Optional[List[etree._Element]] = None,
                      list_of_transitions: Optional[List[etree._Element]] = None):
    new_page_elmnt = etree.Element(ZOFAR_PAGE_TAG, attrib={'uid': page_uid})
    new_page_elmnt.append(etree.Element(ZOFAR_HEADER_TAG))
    new_page_elmnt.append(etree.Element(ZOFAR_BODY_TAG, attrib={'uid': 'b'}))
    new_page_elmnt.append(etree.Element(ZOFAR_TRIGGERS_TAG))
    new_page_elmnt.append(etree.Element(ZOFAR_TRANSITIONS_TAG))
    if list_of_header_elements is not None:
        [new_page_elmnt.find(ZOFAR_HEADER_TAG).append(element) for element in list_of_header_elements]
    if list_of_body_elements is not None:
        [new_page_elmnt.find(ZOFAR_BODY_TAG).append(element) for element in list_of_body_elements]
    if list_of_triggers is not None:
        [new_page_elmnt.find(ZOFAR_TRIGGERS_TAG).append(element) for element in list_of_triggers]

    if list_of_transitions is not None:
        [new_page_elmnt.find(ZOFAR_HEADER_TAG).append(element) for element in list_of_transitions]
    else:
        new_page_elmnt.find(ZOFAR_TRANSITIONS_TAG).append(etree.Element(ZOFAR_TRANSITION_TAG, attrib={'target': 'end'}))
    return new_page_elmnt


def create_zofar_action(command: str,
                        on_exit: Optional[str] = None,
                        direction: Optional[str] = None,
                        condition: Optional[str] = None) -> etree._Element:
    attrib_dict = {'command': command}
    if on_exit is not None:
        attrib_dict['onExit'] = on_exit
    if direction is not None:
        attrib_dict['direction'] = direction
    if condition is not None:
        attrib_dict['condition'] = condition
    new_action = etree.Element(ZOFAR_ACTION_TAG, attrib_dict)
    return new_action


def remove_backwardsblock_pages(input_html_root: etree._Element) -> etree._Element:
    for page in input_html_root.iterchildren(ZOFAR_PAGE_TAG):
        page_uid = get_element_attrib(page, 'uid')
        if page_uid is not None:
            if page_uid.startswith('backwardsBlock_'):
                page.getparent().remove(page)
    return input_html_root


def create_text_element(uid: str, input_text: str):
    new_text_element = etree.Element(ZOFAR_TEXT_TAG, attrib={'uid': uid})
    new_text_element.text = input_text
    return new_text_element


def remove_and_add_splitlanding_pages(html_root: etree._Element,
                                      split_data_dict: dict,
                                      copy_old_headers_bodies: bool = True) -> etree._Element:
    for module in split_data_dict[MODULES_DATA].values():
        split_landing_uid = 'splitLanding_' + module[PAGE_NAME_STARTSWITH]
        if copy_old_headers_bodies:
            old_header = None
            old_body = None
            for page in html_root.iterchildren(ZOFAR_PAGE_TAG):
                page_uid = get_element_attrib(page, 'uid')
                if page_uid != split_landing_uid:
                    continue
                old_header = [header for header in page.find(ZOFAR_HEADER_TAG).iterchildren()]
                old_body = [body for body in page.find(ZOFAR_BODY_TAG).iterchildren()]
                # ToDo fix this!!
                new_splitlanding_page = create_zofar_page(split_landing_uid, old_header, old_body)
                page.getparent().remove(page)
                html_root.append(new_splitlanding_page)
                break

    return html_root


def create_redirect_action(target: str, on_exit: str, direction: str = None, condition: str = None) -> etree._Element:
    return create_zofar_action(command=f"navigatorBean.redirect('{target}')",
                               on_exit=on_exit,
                               direction=direction,
                               condition=condition)


def add_backwardsblock_pages(input_html_root: etree._Element,
                             input_pages_dict: Dict[str, Union[List[str], Set[str]]]) -> etree._Element:
    for input_pages_startswith, input_pages_iterable in input_pages_dict.items():
        episodedispatcher_trigger_element = create_redirect_action(target='episodeDispatcher',
                                                                   on_exit='false',
                                                                   condition=f"!navigatorBean.getBackwardViewID().startsWith('/splitLanding_{input_pages_startswith}')")
        for page in input_pages_iterable:
            header_text_element = create_text_element('t1', 'Diese Page sollte eigentlich nicht angezeigt, sondern '
                                                            'direkt übersprungen werden.#{layout.BREAK} Das hat '
                                                            'leider nicht geklappt. Bitte klicken Sie auf "Weiter".')

            trigger_element = create_redirect_action(target=page,
                                                     on_exit="false",
                                                     condition=f"navigatorBean.getBackwardViewID().startsWith('/splitLanding_{input_pages_startswith}')")

            # ToDo: add comment to indicate that it is auto generated
            new_page = create_zofar_page(page_uid='backwardsBlock_' + page,
                                         list_of_header_elements=[header_text_element],
                                         list_of_triggers=[episodedispatcher_trigger_element, trigger_element])

            new_page.insert(0, etree.Comment('Automatically generated page for blocking backward'
                                             'jumps. Redirects to "episodeDispatcher".'))
            input_html_root.append(new_page)
    return input_html_root


def generate_frag_var_list_from_split_data(input_data: Dict[str, Union[int, str]]) -> list:
    return [str(input_data[FRAGMENT_VARS_STEM]) + str(counter + 1) for counter in
            range(int(input_data[FRAGMENT_VARS_COUNT]))]


def add_debug_info_to_page(page: etree._Element, split_data: dict) -> etree._Element:
    page_name = get_element_attrib(page, 'uid')
    module_data = split_data[MODULES_DATA]
    module_name_str = None
    for module_name, module_data_dict in module_data.items():
        module_startswith = module_data_dict[PAGE_NAME_STARTSWITH]
        if page_name.startswith(module_startswith):
            module_name_str = module_name
            break

    module_data_dict = module_data[module_name_str]

    frag_var_list = generate_frag_var_list_from_split_data(split_data[DATA])
    episode_overview_text = f"#{{layout.BREAK}}" \
                            f"Token: " \
                            f"#{{layout.BOLD_START}}#{{sessionController.participant.token}}" \
                            f"#{{layout.BOLD_END}}" \
                            f"#{{layout.BREAK}}" \
                            f"Zeitstempel Sessionbeginn: #{{zofar.valueOf(startPoint)}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"episode_index: #{{episode_index.value}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"#{{layout.UNDERLINED_START}}Zeitraum der aktuellen Episode: " \
                            f"#{{layout.UNDERLINED_END}}#{{layout.BREAK}}" \
                            f"startmonth: #{{zofar.labelOf(startmonth)}}#{{layout.BREAK}}" \
                            f"startyear: #{{zofar.labelOf(startyear)}}#{{layout.BREAK}}" \
                            f"endmonth: #{{zofar.labelOf(endmonth)}}#{{layout.BREAK}}" \
                            f"endyear: #{{zofar.labelOf(endyear)}}#{{layout.BREAK}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"v_complete: #{{v_complete.value}} #{{layout.BREAK}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"Episode Counter (Ausbildung: v_episodeCount): #{{v_episodeCount}}" \
                            f"#{{layout.BREAK}}" \
                            f"Episode Counter (fertige Ausbildungsepisoden: v_episodeCount_done): " \
                            f"#{{v_episodeCount_done}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"#{{layout.UNDERLINED_START}}Array: #{{layout.UNDERLINED_END}}" \
                            f"#{{layout.BREAK}}" \
                            f"#{{zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_list)})))}}" \
                            f"#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}#{{layout.BREAK}}" \
                            f"Back to: " \
                            f"#{{layout.ITALIC_START}}" \
                            f"#{{navigatorBean.getBackwardViewID()}}" \
                            f"#{{layout.ITALIC_END}}"

    debug_accordion_json_text = f"#{{layout.SMALL_START}}" \
                                f"#{{zofar.prettyPrintJsonHtml(zofar.str2jsonArr(" \
                                f"zofar.defrac(zofar.list({','.join(frag_var_list)}))))}}" \
                                f"#{{layout.SMALL_END}}"
    debug_accordion_episode_text = f"#{{layout.SMALL_START}}" \
                                   f"#{{zofar.prettyPrintJsonHtml(zofar.getJson(zofar.str2jsonArr(" \
                                   f"zofar.defrac(zofar.list({','.join(frag_var_list)}))), " \
                                   f"zofar.toInteger(episode_index.value)))}}" \
                                   f"#{{layout.SMALL_END}}"

    split_type_dict_escaped = json.dumps(module_data_dict[SPLIT_TYPE_DICT]).replace('"', '*')
    debug_accordion_split_type_text = f"#{{layout.SMALL_START}}" \
                                      f"#{{zofar.prettyPrintJsonHtml(" \
                                      f"zofar.parseJsonObj('{split_type_dict_escaped}'))}}"

    # add debug section accordion
    page.find(ZOFAR_BODY_TAG).append(debug_accordion("automaticallygenerated01",
                                                     "Episoden Überblick",
                                                     episode_overview_text))
    # add debug section accordion
    page.find(ZOFAR_BODY_TAG).append(debug_accordion("automaticallygenerated02",
                                                     "JSON Array",
                                                     debug_accordion_json_text))
    # add debug section accordion
    page.find(ZOFAR_BODY_TAG).append(debug_accordion("automaticallygenerated03",
                                                     f'JSON Episode (episode_index: '
                                                     f'#{{zofar.toInteger(episode_index.value)}})',
                                                     debug_accordion_episode_text))

    # add debug section accordion
    page.find(ZOFAR_BODY_TAG).append(debug_accordion("automaticallygenerated04",
                                                     f'Modul: {module_name_str} - split type dictionary',
                                                     debug_accordion_split_type_text))

    return page


def list_all_module_pages(q: Questionnaire) -> List[str]:
    list_all_startswith_strings = [module_data[PAGE_NAME_STARTSWITH] for module_data in
                                   q.split_data[MODULES_DATA].values()]
    return_list = []
    for string in list_all_startswith_strings:
        for page_uid in [page.uid for page in q.pages]:
            if page_uid.startswith(string):
                return_list.append(page_uid)
    return return_list


def main(xml_input_path: Union[Path, str], xml_output_path: Union[Path, str]):
    etree.register_namespace('zofar', 'http://www.his.de/zofar/xml/questionnaire')
    etree.register_namespace('display', 'http://www.dzhw.eu/zofar/xml/display')

    # prepare paths
    xml_input_path = Path(xml_input_path)
    xml_output_path = Path(xml_output_path)

    # load existing QML file
    q = read_questionnaire(xml_input_path, with_comments=True)

    xml_input_string = xml_input_path.read_text(encoding='utf-8')

    xml_template = bytes(xml_input_string, 'utf-8')

    parser = etree.XMLParser(remove_blank_text=True, encoding='utf-8')
    template_root = etree.fromstring(xml_template, parser)

    frag_var_stem = str(q.split_data[DATA][FRAGMENT_VARS_STEM])
    frag_var_count = int(q.split_data[DATA][FRAGMENT_VARS_COUNT])

    frag_var_list = generate_frag_var_list_from_split_data(q.split_data[DATA])

    calendar_modules_startswith_list = [val[PAGE_NAME_STARTSWITH] for key, val in q.split_data[MODULES_DATA].items()]

    _insert_fragment_variable_declarations(template_root, frag_var_stem, frag_var_count)

    page_transitions_list_dict = defaultdict(list)
    page_trigger_list_dict_ins_after = defaultdict(list)
    page_trigger_list_dict_ins_prior = defaultdict(list)
    backwardsblock_pages_dict = defaultdict(set)

    if q.split_data[MODULES_DATA]:
        # soundness check for all modules data
        soundness_check_all_modules_data(q.split_data[MODULES_DATA])

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
                module_split_type_order = [split_type for split_type in module_data[SPLIT_TYPE_ORDER] if
                                           split_type.strip() != '']
                module_end_pages = [page for page in module_data[MODULE_END_PAGES] if page.strip() != ""]

                # soundness check of module_data and module_split_type_dict
                assert soundness_check_module_split_data(module_data, module_split_type_dict)

            except KeyError as e:
                print(f'Module Data Dictionary for Module "{module_name_str}"')
                pprint.pprint(module_data)
                raise KeyError(e)

            module_end_page_transitions_list = []
            for end_page in module_end_pages:

                tmp_pages = [page for page in q.pages if page.uid == end_page]
                if len(tmp_pages) == 0:
                    raise ValueError(f'Page "{end_page}" not found in QML!')
                end_page_obj = tmp_pages[0]

                # first run: initialize the list
                if module_end_page_transitions_list == []:
                    [module_end_page_transitions_list.append(transition) for transition in end_page_obj.transitions]
                # after first run: ensure that all transitions on all end pages are identical
                else:
                    if [transition for transition in end_page_obj.transitions] != module_end_page_transitions_list:
                        print(f'page: "{end_page}":')
                        pprint.pprint(end_page_obj.transitions)
                        print(f'previos end_page(s):')
                        pprint.pprint(module_end_page_transitions_list)
                        raise AssertionError(
                            f'Transitions from module_end_pages "{module_end_pages}" are not the same over all pages!')
            # ToDo: ensure that the module end transitions are added on all split type end pages and
            #  split type end candidate pages incl. condition
            module_split_transitions_list = []

            for split_type, split_type_data in module_split_type_dict.items():
                if split_type_data[START_PAGE].strip() != "":
                    target_uid = split_type_data[START_PAGE]
                    condition = f"zofar.hasCurrentSplitType(zofar.str2jsonArrNoEmpty(zofar.defrac(zofar.list(" \
                                f"{','.join(frag_var_list)}))), zofar.toInteger(episode_index.value), '{split_type}')"
                    module_split_transitions_list.append(Transition(target_uid, condition))

            # iterate through the split types in correct order
            for split_type in module_split_type_order:
                split_type_index = module_split_type_order.index(split_type)
                # determine which split types in the order are left ("previous") of the current split type
                types_left_of_split_type = module_split_type_order[:split_type_index]
                # determine which split types in the order are right ("following") of the current split type
                types_right_of_split_type = module_split_type_order[split_type_index + 1:]
                split_type_start_page = module_data[SPLIT_TYPE_DICT][split_type][START_PAGE].strip()
                if split_type_start_page == "":
                    continue

                # add a backwardsblog page for split start page
                backwardsblock_pages_dict[module_page_name_startswith].add(split_type_start_page)

                # remove previous split types from "currentSplit" when we are on a split type start page
                if types_left_of_split_type != []:
                    trigger_element = delete_from_current_split_trigger_element(types_left_of_split_type,
                                                                                frag_var_list)
                    page_trigger_list_dict_ins_prior[split_type_start_page].append(trigger_element)

                split_type_end_pages_list = [page for page in
                                             module_data[SPLIT_TYPE_DICT][split_type][END_PAGES].keys()]

                for end_page in split_type_end_pages_list:
                    conditions_list = module_data[SPLIT_TYPE_DICT][split_type][END_PAGES][end_page]
                    # deal with triggers & transitions
                    #
                    #  end page candidates
                    if conditions_list != [{}]:
                        remove_from_current_split_type_trigger = \
                            delete_from_current_split_trigger_element(split_type,
                                                                      frag_var_list)
                        tmp_conditions_list = []
                        for condition_entry in conditions_list:
                            for var_name, var_val in condition_entry.items():
                                if q.variables[var_name].type == 'enum':
                                    tmp_conditions_list.append(f"({var_name}.valueId == '{var_val}')")
                                else:
                                    tmp_conditions_list.append(f"({var_name}.value == '{var_val}')")

                        page_candidate_condition = ' and '.join(tmp_conditions_list)

                        # trigger for deleteCurrentSplit()
                        remove_from_current_split_type_trigger.attrib["condition"] = page_candidate_condition
                        page_trigger_list_dict_ins_after[end_page].append(remove_from_current_split_type_trigger)

                        # trigger for splitEpisode() - condition has to be concatenated with:
                        #  "-> and has no other following split types in currentSplit"
                        split_condition = page_candidate_condition + \
                                          ' and (' + \
                                          do_split_on_end_page_candidate_function(types_right_of_split_type,
                                                                                  frag_var_list) + ')'
                        split_episode_trigger = auto_generate_split_episode_trigger_element(module_split_type_dict,
                                                                                            frag_var_list,
                                                                                            split_condition)

                        page_trigger_list_dict_ins_after[end_page].append(split_episode_trigger)

                        # prepare transition condition
                        iter_condition = " and ".join(
                            [has_current_split_list_zofar_function(module_split_type_order, frag_var_list),
                             page_candidate_condition])

                    #  end pages
                    else:
                        remove_from_current_split_type_trigger = \
                            delete_from_current_split_trigger_element(split_type,
                                                                      frag_var_list)
                        page_trigger_list_dict_ins_after[end_page].append(remove_from_current_split_type_trigger)

                        # trigger for splitEpisode() - condition has to be concatenated with:
                        #   "-> and has no other following split types in currentSplit"
                        split_condition = do_split_on_end_page_candidate_function(types_right_of_split_type,
                                                                                  frag_var_list)
                        split_episode_trigger = auto_generate_split_episode_trigger_element(module_split_type_dict,
                                                                                            frag_var_list,
                                                                                            split_condition)
                        page_trigger_list_dict_ins_after[end_page].append(split_episode_trigger)

                        # prepare transition condition
                        iter_condition = has_current_split_list_zofar_function(module_split_type_order, frag_var_list)

                    # deal with transitions - implement transition condition
                    landing_page_name = f'splitLanding_{module_page_name_startswith}01'
                    page_transitions_list_dict[end_page].append(create_transition('episodeDispatcher',
                                                                                  'zofar.asNumber(episode_index) lt 0'))
                    page_transitions_list_dict[end_page].append(create_transition(landing_page_name,
                                                                                  iter_condition))

            # also process module end pages
            for module_end_page in module_end_pages:
                # deal with triggers
                if module_end_page not in page_trigger_list_dict_ins_after.keys():
                    # trigger for splitEpisode()
                    split_episode_trigger = auto_generate_split_episode_trigger_element(module_split_type_dict,
                                                                                        frag_var_list)
                    page_trigger_list_dict_ins_after[module_end_page].append(split_episode_trigger)

                # deal with transitions: to episodedispatcher
                page_transitions_list_dict[module_end_page].append(create_transition('episodeDispatcher', 'true'))

    # delete old split data dictionary
    for element in template_root.iter():
        if is_comment_element(element):
            try:
                split_data_dict = json.loads(element.text.strip())
                if 'SPLIT_DATA' in split_data_dict.keys():
                    element.addprevious(etree.Comment(json.dumps(split_data_dict, indent='  ')))
                    element.getparent().remove(element)
                    break
            except json.JSONDecodeError as e:
                print(e)
    processed_pages_list = []

    # ##################
    # XML MODIFICATION #
    # ##################

    # clean up the ascii art comments
    remove_all_ascii_art_comments(template_root)

    # delete all backwardsblock pages
    remove_backwardsblock_pages(template_root)

    # add all necessary backwardsblock pages
    add_backwardsblock_pages(template_root, backwardsblock_pages_dict)

    # remove old and add newly created splitlanding pages; copy old bodies and headers (if present) to new pages
    remove_and_add_splitlanding_pages(template_root, split_data_dict[SPLIT_DATA], True)

    # iterate over all pages in XML object
    for page in template_root.iterchildren(ZOFAR_PAGE_TAG):
        page_uid = get_element_attrib(page, 'uid')
        ascii_art_comments = create_ascii_art_comments(page_uid)
        for ascii_art_comment in ascii_art_comments:
            page.addprevious(ascii_art_comment)

        # PROCESS ALL MODULE PAGES
        if page_uid in list_all_module_pages(q):

            # remove previously generated debug section
            for section_tag in page.find(ZOFAR_BODY_TAG).iterchildren():
                if "uid" in section_tag.attrib:
                    if section_tag.attrib['uid'].startswith("automaticallygenerated"):
                        section_tag.getparent().remove(section_tag)
            # add debug info
            if DEBUG:
                add_debug_info_to_page(page, split_data_dict[SPLIT_DATA])

        # automatically generated triggers
        remove_mode_switch = False
        if page_uid in list_all_module_pages(q):
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

                            # first trigger: redirect if index < 0
                            frag_var_list_str = ','.join(frag_var_list)
                            redirect = create_redirect_action(target="calendar",
                                                              on_exit="false",
                                                              condition="zofar.asNumber(episode_index) lt 0 or "
                                                                        "zofar.asNumber(episode_index) ge "
                                                                        "zofar.toInteger("
                                                                        "zofar.str2jsonArr(zofar.defrac("
                                                                        f"zofar.list({frag_var_list_str}))).size())")
                            trigger.addprevious(redirect)
                            # input new trigger - edit in-place, does not return anything
                            # other trigger prior to regular (clean up currentSplit)
                            if page_uid in page_trigger_list_dict_ins_prior.keys():
                                [trigger.addprevious(page_trigger) for page_trigger in
                                 page_trigger_list_dict_ins_prior[page_uid]]

                            # regular
                            if any([page_uid.startswith(start_str) for start_str in calendar_modules_startswith_list]):
                                auto_generate_regular_trigger(xml_element=trigger, input_xml=xml_input_path,
                                                              input_page_uid=page_uid)
                            # other trigger after regular (deleteCurrentSplit, splitEpisode)
                            if page_uid in page_trigger_list_dict_ins_after.keys():
                                [trigger.addprevious(page_trigger) for page_trigger in
                                 page_trigger_list_dict_ins_after[page_uid]]
                            break

                        if remove_mode_switch:
                            if automation_comment_switch(trigger) != AUTOMATION_COMMENT_END:
                                trigger_to_delete = trigger
                                continue
                        if automation_comment_switch(trigger) == AUTOMATION_COMMENT_START:
                            remove_mode_switch = True
                else:
                    raise ValueError(f'Missing Automated Trigger Comments for Page:"{page_uid}"')

        # deal with transitions - delete old transitions
        if page.find(ZOFAR_TRANSITIONS_TAG) is not None:
            for transition in page.find(ZOFAR_TRANSITIONS_TAG).iterchildren():
                if transition.tag == ZOFAR_TRANSITION_TAG:
                    for comment_candidate in transition.iter():
                        if is_comment_element(comment_candidate):
                            if comment_candidate.text == "AUTOMATICALLY GENERATED":
                                transition.getparent().remove(transition)

        # add new transitions
        if page_uid in page_transitions_list_dict.keys():
            if page.find(ZOFAR_TRANSITIONS_TAG) is None:
                raise ValueError(f'no "transitons" tag found on page: {page_uid}')
            else:
                transitions_element = page.find(ZOFAR_TRANSITIONS_TAG)

                # mechanism to ensure that soft-forces (first transition(s) lead(s) to the same page) will be preserved
                highest_tran_index = None
                transition_elements_list = [el for el in transitions_element.iterchildren()]
                for tran_element in transition_elements_list:
                    if hasattr(tran_element, "attrib"):
                        if "target" in tran_element.attrib:
                            if tran_element.attrib["target"] == page_uid:
                                highest_tran_index = transitions_element.index(tran_element)

                if highest_tran_index is None:
                    highest_tran_index = 0
                else:
                    highest_tran_index += 1

                for transition_index, transition_element in enumerate(page_transitions_list_dict[page_uid]):
                    transitions_element.insert(transition_index + highest_tran_index, transition_element)

    print(f'{processed_pages_list=}')

    output_xml_string = etree.tostring(template_root, pretty_print=True, method='xml').decode('utf-8')

    def _fix_line_beginnings(index: int, input_str: str, fix_indent: Optional[int], last_closing: bool) -> Tuple[
        str, Optional[int], bool]:
        tmp_str = re.sub(r'^ +', _duplicate_str, input_str)
        length_beginning_space = 0
        for i, char in enumerate(tmp_str):
            if char != ' ':
                if char == '<':
                    if tmp_str[i + 1] == '/':
                        if fix_indent is not None:
                            if fix_indent >= 1:
                                if last_closing:
                                    return re.sub(r'^ +', '\t' * (fix_indent - 1), input_str), fix_indent - 1, True
                                else:
                                    return re.sub(r'^ +', '\t' * fix_indent, input_str), fix_indent, True

                    length_beginning_space = i
                    break
                else:
                    if fix_indent is not None and fix_indent >= 0:
                        return re.sub(r'^ +', '\t' * (fix_indent + 1), input_str), fix_indent, False
                    return input_str, fix_indent, False
        if length_beginning_space > 0:
            input_str_stripped = tmp_str[length_beginning_space:]
            tab_count = math.ceil(length_beginning_space / 4)
            tmp_str = '\t' * tab_count + input_str_stripped

            return tmp_str, tab_count, False
        return tmp_str, fix_indent, False

    results_list = []
    last_indent = None
    last_closing = False
    new_line = None
    name_tag_reached = False
    for index, line in enumerate(output_xml_string.split('\n')):
        if str(line).strip().startswith('<zofar:name'):
            name_tag_reached = True
        if not name_tag_reached:
            results_list.append(line)
            continue
        new_line, last_indent, last_closing = _fix_line_beginnings(index, line, last_indent, last_closing)
        results_list.append(new_line)

    output_xml_string = '\n'.join(results_list)
    # output_xml_string = '\n'.join([_fix_line_beginnings(index, line) for index, line in enumerate(output_xml_string.split('\n'))])

    # umlaute etc. get automatically replaced by their html escape codes when being written by the parser
    # replace them back (remove html escapes and replace by non-ascii characters)
    matches = re.findall(r'(&#.{,5};)', output_xml_string)
    matches_set = set(matches)
    if len(matches_set) > 0:
        print('\n' + f'The following characters will be replaced:')
        for match in matches_set:
            print(f'    {match=} -> {html.unescape(match)}')
            output_xml_string = output_xml_string.replace(match, html.unescape(match))
        print()

    # write XML to file
    output_xml_file = Path(xml_output_path)

    if sys.version_info.major == 3 and sys.version_info.minor >= 10:
        output_xml_file.write_text(data=output_xml_string, encoding='utf-8', newline='\n')
    else:
        output_xml_file.write_text(data=output_xml_string, encoding='utf-8')


if __name__ == '__main__':
    main(XML_INPUT_PATH, XML_OUTPUT_PATH)
