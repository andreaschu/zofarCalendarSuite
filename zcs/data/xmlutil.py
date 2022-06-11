import json
from typing import Dict, List, Union, Optional, Tuple, Any
from xml.etree import ElementTree
from dataclasses import dataclass, field
from pathlib import Path
from zcs.util import flatten
import re

ns = {'zofar': 'http://www.his.de/zofar/xml/questionnaire'}

var_type_map = {
    'singleChoiceAnswerOption': 'enum'
}


@dataclass
class Transition:
    target_uid: str
    # condition as spring expression that has to be fulfilled on order to follow the transition
    condition: Optional[str] = None


@dataclass
class _VariableBase:
    name: str


@dataclass
class Variable(_VariableBase):
    type: str
    is_preload: bool = False


@dataclass
class _VarRefBase:
    pass


@dataclass
class VarRef(_VarRefBase):
    variable: Variable
    dropdown: bool = False
    # list of conditions (as spring expression) that have to be fulfilled in order to reach the variable reference
    condition: List[str] = field(default_factory=list)


@dataclass
class _JsonAttrString:
    type: str = 'string'


@dataclass
class JsonAttr(_JsonAttrString, _VariableBase):
    pass


@dataclass
class JsonAttrRef(_VarRefBase):
    variable: JsonAttr
    value: str


@dataclass
class Page:
    uid: str
    transitions: List[Transition]
    var_refs: List[_VarRefBase]
    json_attr: List[_VarRefBase]


@dataclass
class Questionnaire:
    variables: Dict[str, Variable]
    pages: List[Page]
    split_data: Dict[str, Dict[str, Any]]
    module_dict: Optional[Dict[str, List[str]]] = None
    submodule_dict: Optional[Dict[str, List[str]]] = None


def variable_declarations(root: ElementTree.Element) -> Dict[str, Variable]:
    """
    Reads variables from `zofar:variables` and `zofar:preloads` sections

    :param root: root xml element
    :return: dictionary mapping from variable name to a `Variable`
    """
    variable_dict = {}

    # read `preloads` section
    preloads = root.find('zofar:preloads', ns)
    if preloads is not None:
        for preload in preloads.findall("zofar:preload", ns):
            for preload_item in preload.findall("zofar:preloadItem", ns):
                variable_name = preload_item.get('variable')
                if variable_name is not None:
                    variable_dict[f'PRELOAD{variable_name}'] = Variable(f'PRELOAD{variable_name}', 'string', True)

    # read `variables` section
    variables = root.find('zofar:variables', ns)
    if variables is not None:
        for variable in variables.findall("zofar:variable", ns):
            if variable.get('name') is not None and variable.get('type') is not None:
                var_type = var_type_map.get(variable.get('type'), variable.get('type'))
                variable_dict[variable.get('name')] = Variable(variable.get('name'), var_type, False)

    return variable_dict


def var_refs(page: ElementTree.Element, variables: Dict[str, Variable]) -> List[VarRef]:
    """
    Extract variable references from a given page

    :param page: page xml element
    :param variables: dictionary mapping variable names to a `Variable` (see `variable_declarations`)
    :return: list of `VarRef`s
    """

    # define function for recursive search
    def _var_refs(_element: ElementTree.Element, _variables: Dict[str, Variable], _visible: List[str]) -> List[VarRef]:
        # add `visible` predicate if available
        if _element.get('visible') is not None:
            _visible = _visible + [_element.get('visible').strip()]

        # if a variable attribute exists, return one-element list containing the `VarRef`. Otherwise, an empty list
        if _element.get('variable') is not None:
            # check if referenced variable is declared
            if _element.get('variable') not in variables:
                raise ValueError(f"variable {_element.get('variable')} was referenced but not declared")

            if any([True for key, val in _element.attrib.items() if key == 'type' and val == 'dropdown']):
                ref_list = [VarRef(variables[_element.get('variable')], True, _visible[:])]
            else:
                ref_list = [VarRef(variables[_element.get('variable')], False, _visible[:])]

        else:
            ref_list = []

        # apply recursive call and flat map on all child elements
        return ref_list + flatten([_var_refs(ch, variables, _visible) for ch in _element])

    # call recursive function on body, if it exists
    body = page.find('zofar:body', ns)
    if body is None:
        return []
    else:
        return _var_refs(body, variables, [])


def transitions(page: ElementTree.Element) -> List[Transition]:
    """
    Extract transitions from a given page

    :param page: page xml element
    :return: list of `Transition`s
    """
    trans = page.find('zofar:transitions', ns)

    if trans is None:
        return []
    else:
        return [Transition(tr.get('target'), tr.get('condition'))
                for tr in trans.findall('zofar:transition', ns)]


def json_attrs(page: ElementTree.Element, variables: Dict[str, Variable]) -> List[JsonAttrRef]:
    """
    Extract json attributes that could have been set from a given page

    :param page: page xml element
    :param variables: dictionary mapping variable names to a `Variable` (see `variable_declarations`)
    :return: dict of json_key: `json_attr` list
    """

    # define function for recursive search
    def _json_attrs(_element: ElementTree.Element, _variables: Dict[str, Variable]) -> List[JsonAttrRef]:

        # if the element is a script item with toPersist.put(), return one-element list containing the `json_attr`.
        # Otherwise, an empty list.
        attr_list = []
        if _element.tag == f'{{{ns["zofar"]}}}scriptItem':
            # check if referenced variable is declared
            if _element.get('value') is not None:
                key_value_list = [(key, value) for key, value in
                                  re.findall(r"^toPersist.put\('([a-zA-Z0-9_]+)\s*',\s*(.+)\)\s*$",
                                             _element.get('value'))]
                for key, val in key_value_list:
                    if key in variables:
                        attr_list.append(VarRef(variable=variables[key]))
                    else:
                        attr_list.append(JsonAttrRef(variable=JsonAttr(name=key), value=val))

        # apply recursive call and flat map on all child elements
        return attr_list + flatten([_json_attrs(ch, variables) for ch in _element])

    # call recursive function on body, if it exists
    body = page.find('zofar:triggers', ns)
    if body is None:
        return []
    else:
        return _json_attrs(body, variables)


def get_json_data(element: ElementTree.Element,
                  root_key: str) -> Union[Dict[str, Dict[str, List[Dict[str, str]]]],
                                          Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]]:
    if element.text.find(root_key) != -1:
        try:
            raw_split_data_dict = json.loads(element.text.replace('\n', '').replace(' ', ''))
            if root_key in raw_split_data_dict.keys():
                return raw_split_data_dict[root_key]
        except json.decoder.JSONDecodeError as err:
            print('input data:')
            print(f'{err.doc}')
            print('error message:')
            print(f'{err.msg}')
            raise json.decoder.JSONDecodeError(err.msg, err.doc, err.pos)
    return {}


def get_split_data(root: ElementTree.Element) -> \
        Dict[str, Dict[str, Dict[str, Any]]]:
    split_types_dict = {}
    split_data_dict = {}
    module_pagename_prefixes = []
    for element in root.iter():
        if hasattr(element, "text"):
            if element.text is not None:
                if "SPLIT_DATA" in element.text:
                    if split_data_dict == {}:
                        if get_json_data(element, "SPLIT_DATA") != {}:
                            split_data_dict = get_json_data(element, "SPLIT_DATA")
                            break
    return split_data_dict


def questionnaire(root: ElementTree.Element) -> Questionnaire:
    """
    Extract questionnaire from xml root element

    :param root: xml root element
    :return: `Questionnaire`
    """
    variables = variable_declarations(root=root)

    pages = [Page(page.attrib['uid'], transitions(page), var_refs(page, variables), json_attrs(page, variables))
             for page in root.findall("zofar:page", ns)]

    split_data_dict = get_split_data(root=root)

    return Questionnaire(variables, pages, split_data_dict)


def read_questionnaire(input_path: Union[Path, str], with_comments: bool = False) -> Questionnaire:
    """
    Reads file from `input_path` and converts it into a `Questionnaire`

    :param with_comments: enables parsing of comments
    :param input_path: path to input file as `str` or `Path`
    :return: `Questionnaire`
    """
    if with_comments:
        # noinspection PyArgumentList
        parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))
        xml_root = ElementTree.parse(input_path, parser)

    else:
        xml_root = ElementTree.parse(input_path)

    return questionnaire(xml_root.getroot())

