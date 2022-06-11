import re
import copy
import os.path
from pathlib import Path
from typing import Union, Dict, List, Optional, Any
from lxml import etree
import html
from collections import defaultdict
from zcs.data.xmlutil import read_questionnaire, Variable


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


def automation_comment_switch(elemnt: etree.Element) -> Optional[bool]:
    if is_comment_element(elemnt):
        if elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER START'):
            return True
        elif elemnt.text.strip().startswith('AUTOMATICALLY GENERATED JSON TRIGGER END'):
            return False
    return None


def gen_trigger_dict(xml_element: etree.Element, input_xml: Union[str, Path], input_page_uid: str) -> None:
    def _return_script_item(val: str) -> etree.Element:
        return etree.Element('{http://www.his.de/zofar/xml/questionnaire}scriptItem',
                             attrib={"value": val})

    def _create_reset_trigger_element(var_list: list) -> etree.Element:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": "zofar.nothing()", "onExit": "false"})

        script_item_list = ["zofar.assign('toReset',zofar.list())"]

        for variable in var_list:
            if variable.dropdown:
                script_item_list += [
                    f"toReset.add('{variable.variable.name}')",
                    f"toReset.add('{variable.variable.name}dropDown')",
                    f"toReset.add('{variable.variable.name}missing')"]
            else:
                script_item_list.append(f"toReset.add('{variable.variable.name}')")

        script_item_list.append("zofar.resetVars(toReset)")

        [new_action_element.append(_return_script_item(script_item)) for script_item in script_item_list if
         script_item is not None]
        return new_action_element

    def _create_load_trigger_element(var_list: list) -> etree.Element:
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": "zofar.nothing()", "onExit": "false"})

        script_item_list = [
            f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_list)}))))",
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
                script_item_list.append(f"toLoad.add('{variable.variable.name}')")
                script_item_list.append(f"toLoad.add('{variable.variable.name}dropDown')")
                script_item_list.append(f"toLoad.add('{variable.variable.name}missing')")
            else:
                script_item_list.append(f"toLoad.add('{variable.variable.name}')")
        script_item_list.append("zofar.getJsonProperties(episodeObj,toLoad)")

        [new_action_element.append(_return_script_item(script_item)) for script_item in script_item_list if
         script_item is not None]

        return new_action_element

    def _create_save_trigger_element(var_list: list) -> etree.Element:
        new_action_command = f"zofar.frac(zofar.list({','.join(frag_var_list)}),zofar.jsonArr2str(defrac))"
        new_action_element = etree.Element('{http://www.his.de/zofar/xml/questionnaire}action',
                                           attrib={"command": new_action_command,
                                                   "onExit": "true"})

        script_item_list = [
            f"zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(frag_var_list)}))))",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) ",
            "zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) ",
            "zofar.assign('toPersist',zofar.map())"]
        for index, variable in enumerate(var_list):
            if variable.dropdown:
                script_item_list.append(
                    f"toPersist.put('{variable.variable.name}',{variable.variable.name}.valueId)")
                script_item_list.append(
                    f"toPersist.put('{variable.variable.name}dropDown',{variable.variable.name}dropDown.value)")
                script_item_list.append(
                    f"toPersist.put('{variable.variable.name}missing',{variable.variable.name}missing.value)")

            else:
                if variable.variable.type == 'enum':
                    script_item_list.append(
                        f"toPersist.put('{variable.variable.name}',{variable.variable.name}.valueId)")
                else:
                    script_item_list.append(f"toPersist.put('{variable.variable.name}',{variable.variable.name}.value)")

        script_item_list += [
            "zofar.setJsonProperties('episodeObj',episodeObj,toPersist)",
            "zofar.assign('defrac',zofar.addOrReplaceJson(defrac,episodeObj,zofar.toInteger(episode_index.value)))"]

        script_item_list.append("zofar.assign('toLoad',zofar.list())")
        for index, variable in enumerate(var_list):
            script_item_list.append(f"toLoad.add('{variable.variable.name}')")
        script_item_list.append("zofar.getJsonProperties(episodeObj,toLoad)")

        [new_action_element.append(_return_script_item(script_item)) for script_item in script_item_list if
         script_item is not None]

        return new_action_element

    q = read_questionnaire(input_xml, with_comments=True)

    # get the page object for the page uid
    relevant_page = [page_obj for page_obj in q.pages if page_obj.uid == input_page_uid][0]

    frag_var_stem = str(q.split_data["DATA"]["FRAGMENT_VARS_STEM"])
    frag_var_count = int(q.split_data["DATA"]["FRAGMENT_VARS_COUNT"])

    frag_var_list = [frag_var_stem + str(i + 1) for i in
                     range(frag_var_count)]

    xml_element.addprevious(_create_reset_trigger_element(list(relevant_page.var_refs)))
    xml_element.addprevious(_create_load_trigger_element(list(relevant_page.var_refs)))
    xml_element.addprevious(_create_save_trigger_element(list(relevant_page.var_refs)))


if __name__ == '__main__':

    etree.register_namespace('zofar', 'http://www.his.de/zofar/xml/questionnaire')
    etree.register_namespace('display', 'http://www.dzhw.eu/zofar/xml/display')

    # load existing xml file
    xml_file = Path(os.environ.get('XML_PATH'))

    q = read_questionnaire(xml_file, with_comments=True)

    xml_template = bytes(xml_file.read_text(encoding='utf-8'), 'utf-8')

    parser = etree.XMLParser(remove_blank_text=True)
    template_root = etree.fromstring(xml_template, parser)
    for element in template_root.iterchildren():
        if is_comment_element(element):
            pass
            # evaluate comments here, if needed
    template_root_copy = copy.deepcopy(template_root)


    def _create_variable_declaration(var_name: str, var_type: str):
        return etree.Element('{http://www.his.de/zofar/xml/questionnaire}variable',
                             attrib={"name": var_name, "type": var_type})


    def _prepare_fragment_variables(element_tree: etree.Element, fragment_var_stem: str, fragment_var_count: int):
        declared_fragment_var_set = set()
        for elm in element_tree.find('{http://www.his.de/zofar/xml/questionnaire}variables').iterchildren():
            if is_comment_element(elm):
                continue
            var_name = get_element_attrib(elm, 'name')
            var_type = get_element_attrib(elm, 'type')
            if var_name.startswith(fragment_var_stem):
                tmp_str = var_name[len(fragment_var_stem):]
                count_match = re.match(r'^[0-9]+', tmp_str)
                if count_match is not None:
                    if int(count_match[0]) > fragment_var_count or var_name in declared_fragment_var_set:
                        elm.getparent().remove(elm)
                    else:
                        declared_fragment_var_set.add(var_name)

        all_fragment_var_set = {fragment_var_stem + str(i + 1) for i in range(fragment_var_count)}
        not_declared_fragment_var_list = list(all_fragment_var_set.symmetric_difference(declared_fragment_var_set))
        not_declared_fragment_var_list.sort()

        for frag_var_name in not_declared_fragment_var_list:
            element_tree.find('{http://www.his.de/zofar/xml/questionnaire}variables').append(
                _create_variable_declaration(frag_var_name, 'string'))


    frag_var_stem = str(q.split_data["DATA"]["FRAGMENT_VARS_STEM"])
    frag_var_count = int(q.split_data["DATA"]["FRAGMENT_VARS_COUNT"])

    calendar_modules_startswith_list = [val["PAGE_NAME_STARTSWITH"] for key, val in q.split_data["MODULES"].items()]


    _prepare_fragment_variables(template_root, frag_var_stem, frag_var_count)

    processed_pages_list = []

    for page in template_root.iterchildren('{http://www.his.de/zofar/xml/questionnaire}page'):
        page_uid = get_element_attrib(page, 'uid')

        remove_mode_switch = False
        for triggers in page.iterchildren('{http://www.his.de/zofar/xml/questionnaire}triggers'):
            automation_comment_list = [automation_comment_switch(elmn) for elmn in
                                       page.find('{http://www.his.de/zofar/xml/questionnaire}triggers').iter()]
            if True in automation_comment_list and False in automation_comment_list[
                                                            automation_comment_list.index(True) + 1:]:
                # track progress
                processed_pages_list.append(page_uid)

                trigger_to_delete = None
                for trigger in triggers.iterchildren():
                    if trigger_to_delete is not None:
                        trigger_to_delete.getparent().remove(trigger_to_delete)
                        trigger_to_delete = None

                    if automation_comment_switch(trigger) == False:
                        remove_mode_switch = False

                        # input new trigger - edit in-place, does not return anything
                        if any([page_uid.startswith(start_str) for start_str in calendar_modules_startswith_list]):
                            gen_trigger_dict(xml_element=trigger, input_xml=xml_file, input_page_uid=page_uid)
                        break

                    if remove_mode_switch == True:
                        if automation_comment_switch(trigger) != False:
                            trigger_to_delete = trigger
                            continue
                    if automation_comment_switch(trigger) == True:
                        remove_mode_switch = True
            else:
                if any([page_uid.startswith(start_str) for start_str in calendar_modules_startswith_list]):
                    print(f'Missing Automated Trigger Comments for Page:"{page_uid}"')
        # deal with transitions - delete old transitions
        if page.find('{http://www.his.de/zofar/xml/questionnaire}transitions') is not None:
            for transition in page.find('{http://www.his.de/zofar/xml/questionnaire}transitions').iterchildren():
                if transition.tag == '{http://www.his.de/zofar/xml/questionnaire}transition':
                    for comment_candidate in transition.iter():
                        if is_comment_element(comment_candidate):
                            if comment_candidate.text == "AUTOMATICALLY GENERATED":
                                transition.getparent().remove(transition)

        # deal with transitions - add new transitions
        if page.find('{http://www.his.de/zofar/xml/questionnaire}transitions') is not None:
            for transition in page.find('{http://www.his.de/zofar/xml/questionnaire}transitions').iter():
                if transition.tag == '{http://www.his.de/zofar/xml/questionnaire}transition':
                    tmp_elm = etree.Element('{http://www.his.de/zofar/xml/questionnaire}transition',
                                            attrib={
                                                "target": "XYZ",
                                                "condition": "true"})
                    tmp_comm = etree.Comment("AUTOMATICALLY GENERATED")
                    tmp_elm.append(tmp_comm)
                    transition.addprevious(tmp_elm)
                    break


    print(processed_pages_list)

    output_xml_string = etree.tostring(template_root, pretty_print=True, method='xml').decode('utf-8')


    def _duplicate(matchobj: re.Match):
        i = matchobj.group(0)
        return str(i) * 2


    output_xml_string = '\n'.join([re.sub(r'^ +', _duplicate, line) for line in output_xml_string.split('\n')])

    Path('questionnaire_output.xml').write_text(output_xml_string, 'utf-8')
