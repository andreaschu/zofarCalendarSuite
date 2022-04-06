__version__ = '0.0.2'

import re
import string
import math
from pathlib import Path
import os
import shutil

here = Path(__file__).parent
if 'PROJECTFOLDER' in os.environ.keys():
    target_project_folder = Path(os.getenv('PROJECTFOLDER'), 'src', 'main', 'resources')
    assert target_project_folder.exists()
    target_project_xml = Path(target_project_folder, 'questionnaire.xml')


output_directory = Path(here, r'output')


class Question_QML_generator:
    def __init__(self, question_type: str, varname_stem: str, index: int = 1, question_text: str = ''):
        self.question_type = question_type
        self.valid_question_types = ['matrixDouble', 'matrixMultipleChoice', 'matrixQuestionMixed',
                                     'matrixQuestionOpen', 'matrixQuestionSingleChoice', 'multipleChoice',
                                     'questionOpen', 'questionSingleChoice']

        assert self.question_type in self.valid_question_types

        self.question_text = question_text
        self.dict_of_question_types = {}
        self.create_dict_of_question_types()
        self.generated_qml_string = ''

        self.index = index

        self.list_of_answer_option_uids = []
        self.list_of_answer_option_labels = []
        self.list_of_answer_option_values = []
        self.list_of_missing_answer_option_labels = []
        self.list_of_missing_answer_option_values = []
        self.list_of_missing_answer_option_uids = []
        self.list_of_item_questions = []
        self.varname_stem = varname_stem
        self.list_of_varnames = []
        self.variable_declaration_string = ''

    # def print_question_menu(self, index=None):
    #     if index is None:
    #         for i in range(0, len(self.dict_of_question_types)):
    #             print(str(i+1) + '  ' + self.dict_of_question_types[list(self.dict_of_question_types.keys())[i]])
    #         tmp_selection_input = input('please enter a number')
    #         print(tmp_selection_input)
    #         tmp_selected_question_type = self.valid_question_types[int(tmp_selection_input) - 1]
    #     else:
    #         tmp_selected_question_type = self.valid_question_types[int(index) - 1]
    #         print(tmp_selected_question_type)

    def create_question_qml(self) -> None:
        if self.question_type == 'matrixQuestionSingleChoice':
            self.generate_matrix_question_single_choice()
        elif self.question_type == 'questionOpen':
            self.generate_question_open()
        elif self.question_type == 'matrixDouble':
            self.generate_matrix_double()
        elif self.question_type == 'matrixMultipleChoice':
            self.generate_matrix_multiple_choice()
        elif self.question_type == 'matrixQuestionMixed':
            self.generate_matrix_question_mixed()
        elif self.question_type == 'matrixQuestionOpen':
            self.generate_matrix_question_open()
        elif self.question_type == 'multipleChoice':
            self.generate_multiple_choice()
        elif self.question_type == 'questionSingleChoice':
            self.generate_question_single_choice()
        else:
            raise NotImplementedError('Question type "' + self.question_type + '" not yet implemented.')

    def create_dict_of_question_types(self):
        for i in range(0, len(self.valid_question_types)):
            self.dict_of_question_types[i] = self.valid_question_types[i]

    def generate_question_open(self):
        self.generated_qml_string = f"""\t\t\t<zofar:questionOpen uid="qo{self.index}" variable="{self.varname_stem}" size="4" type="text">\n"""
        self.generated_qml_string += """\t\t\t\t<zofar:header>\n"""
        if self.question_text.strip() != '':
            self.generated_qml_string += f"""\t\t\t\t\t<zofar:question uid="q1" block="true">{self.question_text}</zofar:question>\n"""
        self.generated_qml_string += """\t\t\t\t</zofar:header>\n"""
        self.generated_qml_string += """\t\t\t</zofar:questionOpen>\n\n"""

        self.list_of_varnames.append(self.varname_stem)
        self.variable_declaration_string += f'<zofar:variable name="{self.varname_stem}" type="string"/>\n'

    def generate_matrix_double(self):
        raise NotImplementedError()

    def generate_matrix_multiple_choice(self):
        raise NotImplementedError()

    def generate_matrix_question_mixed(self):
        raise NotImplementedError()

    def generate_matrix_question_open(self):
        raise NotImplementedError()

    def generate_multiple_choice(self):
        raise NotImplementedError()

    def generate_question_single_choice(self):
        raise NotImplementedError

    def generate_matrix_question_single_choice(self):
        self.generated_qml_string = ''
        self.generated_qml_string += """\t\t\t<zofar:matrixQuestionSingleChoice uid="mqsc">\n\t\t\t\t<zofar:header>\n\t\t\t\t\t<zofar:question uid="q">\n"""
        self.generated_qml_string += '\t\t\t\t\t\t' + self.question_text + '\n'
        self.generated_qml_string += '''\t\t\t\t\t</zofar:question>\n\t\t\t\t</zofar:header>\n\t\t\t\t<zofar:responseDomain noResponseOptions="'''
        self.generated_qml_string += str(
            len(self.list_of_answer_option_labels) + len(self.list_of_missing_answer_option_labels))
        self.generated_qml_string += '''" uid="rd">\n\t\t\t\t\t<zofar:header>\n'''
        for i in range(0, len(self.list_of_answer_option_labels)):
            self.generated_qml_string += '\t\t\t\t\t\t<zofar:title uid="ti' + str(i + 1) + '">' + \
                                         self.list_of_answer_option_labels[i] + '</zofar:title>\n'
        self.generated_qml_string += '\t\t\t\t\t</zofar:header>\n\n'
        if len(self.list_of_missing_answer_option_labels) > 0:
            self.generated_qml_string += '\t\t\t\t\t<zofar:missingHeader>\n'
            for i in range(0, len(self.list_of_missing_answer_option_labels)):
                self.generated_qml_string += '\t\t\t\t\t\t<zofar:title uid="ti' + str(
                    i + 1 + len(self.list_of_answer_option_labels)) + '">' + \
                                             self.list_of_missing_answer_option_labels[i] + '</zofar:title>\n'
            self.generated_qml_string += '\t\t\t\t\t</zofar:missingHeader>\n\n'

        for i in range(0, len(self.list_of_item_questions)):
            self.generated_qml_string += '\t\t\t\t\t<zofar:item uid="it' + str(
                i + 1) + '">\n\t\t\t\t\t\t<zofar:header>\n\t\t\t\t\t\t\t<zofar:question uid="q">\n\t\t\t\t\t\t\t\t'
            self.generated_qml_string += self.list_of_item_questions[
                                             i] + '\n\t\t\t\t\t\t\t</zofar:question>\n\t\t\t\t\t\t</zofar:header>\n'
            self.generated_qml_string += '\t\t\t\t\t\t<zofar:responseDomain variable="'

            tmp_varname = self.varname_stem

            # assign letter suffixes to varname
            factor = math.floor(i / 26)
            if factor >= 1 and factor <= 26:
                tmp_varname += string.ascii_lowercase[factor - 1]
            elif factor == 0:
                pass
            else:
                raise IndexError('Index out or range: ' + str(i) + ' - cannot assign a letter!')
            tmp_varname += string.ascii_lowercase[i % 26]

            self.generated_qml_string += tmp_varname
            self.list_of_varnames.append(tmp_varname)

            self.generated_qml_string += '" uid="rd">\n'
            for i in range(0, len(self.list_of_answer_option_labels)):
                self.generated_qml_string += '\t\t\t\t\t\t\t<zofar:answerOption uid="ao' + str(
                    i + 1) + '" value="' + str(
                    self.list_of_answer_option_values[i]) + '" label="' + \
                                             self.list_of_answer_option_labels[i] + '"></zofar:answerOption>\n'

            for i in range(0, len(self.list_of_missing_answer_option_labels)):
                self.generated_qml_string += '\t\t\t\t\t\t\t<zofar:answerOption uid="ao' + str(
                    i + 1 + len(self.list_of_answer_option_labels)) + '" value="' + str(
                    self.list_of_missing_answer_option_values[i]) + '" label="' + \
                                             self.list_of_missing_answer_option_labels[
                                                 i] + '" missing="true"></zofar:answerOption>\n'

            self.generated_qml_string += '''\t\t\t\t\t\t</zofar:responseDomain>\n\t\t\t\t\t</zofar:item>\n\n'''

        self.generated_qml_string += '\t\t\t\t</zofar:responseDomain>\n\t\t\t</zofar:matrixQuestionSingleChoice>\n\n'

        for i in range(0, len(self.list_of_varnames)):
            self.variable_declaration_string += '<zofar:variable name="'
            self.variable_declaration_string += self.list_of_varnames[i]
            self.variable_declaration_string += '" type="singleChoiceAnswerOption"/>\n'

    def print_variable_declaration(self):
        print(self.variable_declaration_string)


class Question_QML_JSON_Trigger_generator:
    def __init__(self, number_of_fragment_variables: int = 10, fragment_variable_name_stem: str = 'episodes_fragment_'):
        self.list_of_question_qml_generator_objects = []
        self.json_function_code_load = ''
        self.json_function_code_save = ''

        self.number_of_fragment_variables = number_of_fragment_variables
        self.fragment_variable_name_stem = fragment_variable_name_stem
        self.list_of_fragment_variables_names = []

    def display_whole_json(self) -> str:
        tmp_display_whole_json = '<!-- display whole json -->'
        return tmp_display_whole_json

    def reset_whole_json(self) -> str:
        tmp_reset_whole_json_str = '			<!-- reset whole json -->\n'
        tmp_reset_whole_json_str += f"""			<zofar:action
				command="zofar.frac(zofar.list({','.join(self.list_of_fragment_variables_names)}),zofar.jsonArr2str(defrac))" onExit="true" direction="forward">
				<zofar:scriptItem value="zofar.assign('defrac',zofar.str2jsonArr(''))" />
			</zofar:action>\n\n"""
        return tmp_reset_whole_json_str

    def write_to_qml_file(self):
        # load template
        tmp_xml_str = Path(r'../template/template_questionnaire.xml').read_text(encoding='utf-8')

        # create questionOpen for index page (setting of episode_index)
        tmp_question_open_episode_index_str = """
			<zofar:questionOpen uid="mqsc" variable="episode_index" size="4" type="text">
                <zofar:header>
                    <zofar:question uid="q1">episode_index</zofar:question>
                </zofar:header>
			</zofar:questionOpen>\n"""

        replacement_dict = {'variable_declaration': 'XXX_VARIABLE_DECLARATION_PLACEHOLDER_XXX',
                            'index_body': 'XXX_INDEX_BODY_PLACEHOLDER_XXX',
                            'index_trigger': 'XXX_INDEX_TRIGGERS_PLACEHOLDER_XXX',
                            'set_episode_index_body': 'XXX_SET_EPISODE_INDEX_BODY_PLACEHOLDER_XXX',
                            'set_episode_index_trigger': 'XXX_SET_EPISODE_INDEX_TRIGGERS_PLACEHOLDER_XXX',
                            'set_episode_data_body': 'XXX_SET_EPISODE_DATA_BODY_PLACEHOLDER_XXX',
                            'set_episode_data_trigger': 'XXX_SET_EPISODE_DATA_TRIGGERS_PLACEHOLDER_XXX',
                            'reset_json_array_body': 'XXX_RESET_JSON_ARRAY_BODY_PLACEHOLDER_XXX',
                            'reset_json_array_trigger': 'XXX_RESET_JSON_ARRAY_TRIGGERS_PLACEHOLDER_XXX',
                            'check_episode_data_header': 'XXX_CHECK_EPISODE_DATA_HEADER_PLACEHOLDER_XXX',
                            'check_episode_data_body': 'XXX_CHECK_EPISODE_DATA_BODY_PLACEHOLDER_XXX',
                            'check_episode_data_trigger': 'XXX_CHECK_EPISODE_DATA_TRIGGERS_PLACEHOLDER_XXX'}

        # assert that all expected placeholder are found within the xml template
        for key, val in replacement_dict.items():
            try:
                assert re.findall(val, tmp_xml_str) != []
            except AssertionError as e:
                print('\n\n')
                print('#' * 100)
                print(tmp_xml_str)
                print('#' * 100)
                print('\n\n')
                print(f'NOT FOUND:  {key=}, {val=}')
                print('#' * 100)
                print('\n\n')
                raise AssertionError(e)

        # assert that all placeholders found within the xml template are accounted for in replacement_dict values
        for placeholder in re.findall(r'XXX_.+?_XXX', tmp_xml_str):
            try:
                assert placeholder in replacement_dict.values()
            except AssertionError as e:
                print('\n\n')
                print('#' * 100)
                print(tmp_xml_str)
                print('\n\n')
                print('#' * 100)
                print(f'NOT FOUND: {placeholder}')
                raise AssertionError(e)

        # replace placeholder strings
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['variable_declaration'],
                                          self.return_variable_declaration_str())
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['index_body'],
                                          '<!-- index_body-->')
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['index_trigger'],
                                          '<!-- index_trigger-->')

        tmp_xml_str = tmp_xml_str.replace(replacement_dict['set_episode_index_body'],
                                          tmp_question_open_episode_index_str)
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['set_episode_index_trigger'],
                                          '<!-- set_episode_index_trigger-->')

        tmp_xml_str = tmp_xml_str.replace(replacement_dict['reset_json_array_body'],
                                          '<!-- reset_variables_body-->')
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['reset_json_array_trigger'],
                                          self.reset_whole_json())

        tmp_xml_str = tmp_xml_str.replace(replacement_dict['set_episode_data_body'],
                                          self.return_all_qml_code())
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['set_episode_data_trigger'],
                                          self.return_json_load() + self.return_json_save())

        tmp_xml_str = tmp_xml_str.replace(replacement_dict['check_episode_data_header'],
                                          self.return_debug_info())
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['check_episode_data_body'],
                                          '<!-- check_episode_data_body-->')
        tmp_xml_str = tmp_xml_str.replace(replacement_dict['check_episode_data_trigger'],
                                          self.return_json_load() + self.return_json_save())

        try:
            assert re.findall(r'XXX_.+?_XXX', tmp_xml_str) == []
        except AssertionError as e:
            print(tmp_xml_str)
            raise AssertionError(e)


        output_file = Path(r'../output/questionnaire.xml')
        output_file.write_text(data=tmp_xml_str, encoding='utf-8')

    def print_variable_declaration_str(self) -> None:
        print(self.return_variable_declaration_str())

    def return_variable_declaration_str(self) -> str:
        tmp_variable_declaration_str = '<zofar:variable name="episode_index" type="string"/>\n'

        # make sure list of fragment variables is up to date
        self.create_list_of_fragment_variables_names()

        for fragment_variable_name in self.list_of_fragment_variables_names:
            tmp_variable_declaration_str += f"""<zofar:variable name="{fragment_variable_name}" type="string"/>\n"""

        for question_generator_object in self.list_of_question_qml_generator_objects:
            assert isinstance(question_generator_object, Question_QML_generator)
            question_generator_object.create_question_qml()
            tmp_variable_declaration_str += question_generator_object.variable_declaration_string

        return tmp_variable_declaration_str

    def create_list_of_fragment_variables_names(self) -> None:
        self.list_of_fragment_variables_names = []

        zfill_length = len(str(self.number_of_fragment_variables))

        for i in range(self.number_of_fragment_variables):
            self.list_of_fragment_variables_names.append(
                f'{self.fragment_variable_name_stem}{str(i + 1).zfill(zfill_length)}')

    def add_question_qml_generator(self, qml_generator_object: Question_QML_generator) -> None:
        self.list_of_question_qml_generator_objects.append(qml_generator_object)

    def return_all_qml_code(self) -> str:
        tmp_output_str = ''
        for question_qml_generator_object in self.list_of_question_qml_generator_objects:
            assert isinstance(question_qml_generator_object, Question_QML_generator)
            question_qml_generator_object.create_question_qml()
            tmp_output_str += question_qml_generator_object.generated_qml_string
        return tmp_output_str

    def print_all_qml_code(self) -> None:
        print(self.return_all_qml_code())

    def print_json_load(self) -> None:
        print(self.return_json_load())

    def return_debug_info(self) -> str:
        tmp_debug_info_str = ''
        tmp_debug_info_str += f"""			<zofar:title container="true" uid="t1">
        				episode_index: #{{episode_index.value}} 
        				#{{layout.BREAK}}
                        whole json array:
				        #{{zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(self.list_of_fragment_variables_names)})))}}
				        #{{layout.BREAK}}
			        </zofar:title>\n\n"""
        return tmp_debug_info_str

    def return_json_load(self) -> str:
        # make sure that the list of fragment variable names is up to date
        self.create_list_of_fragment_variables_names()

        self.json_function_code_load = ""
        self.json_function_code_load += """			<zofar:action command="zofar.nothing()" onExit="false">\n"""
        self.json_function_code_load += """				<!-- reset page variables -->\n"""
        self.json_function_code_load += """				<!-- initialize empty list -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('toReset',zofar.list())" />\n"""
        self.json_function_code_load += """				\n"""
        self.json_function_code_load += """				<!-- add page variables one after another to the list -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="toReset.add('v_startmonth')" />\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="toReset.add('v_startyear')" />\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="toReset.add('v_endmonth')" />\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="toReset.add('v_endyear')" />\n"""
        for qml_generator_object in self.list_of_question_qml_generator_objects:
            assert isinstance(qml_generator_object, Question_QML_generator)
            for variable_name in qml_generator_object.list_of_varnames:
                self.json_function_code_load += f"""				<zofar:scriptItem value="toReset.add('{variable_name}')" />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += """				<!-- reset all variables stored in list -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.resetVars(toReset)" />\n"""
        self.json_function_code_load += """			</zofar:action>\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += """			<!-- BAUKASTEN: BASIC page setup within loop when LOADING page -->\n"""
        self.json_function_code_load += """			<zofar:action command="zofar.nothing()" onExit="false">\n"""
        self.json_function_code_load += """				<!-- ToDo: make generic zofar function from those two commands -->\n"""
        self.json_function_code_load += """				<!-- generic json setup - load whole json array (all episodes) -->\n"""
        self.json_function_code_load += f"""				<zofar:scriptItem value="zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(self.list_of_fragment_variables_names)}))))" />\n"""
        self.json_function_code_load += """				<!-- load specific episode json object from json array (by episode index) -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) " />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += """				<!-- page-specific -->\n"""
        self.json_function_code_load += """				<!-- initiales variables (according to page qml) -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('monthMap',zofar.map('1=ao1,2=ao2,3=ao3,4=ao4,5=ao5,6=ao6,7=ao7,8=ao8,9=ao9,10=ao10,11=ao11,12=ao12'))" />\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('yearMap',zofar.map('2018=ao1,2019=ao2,2020=ao3,2021=ao4,2022=ao5,2023=ao6,2024=ao7'))" />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('startDate',zofar.getJsonProperty(episodeObj,'startDate')) " />\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('endDate',zofar.getJsonProperty(episodeObj,'endDate')) " />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += "\n"
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.assign('toLoad',zofar.list())" />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += "\n"
        for qml_generator_object in self.list_of_question_qml_generator_objects:
            assert isinstance(qml_generator_object, Question_QML_generator)
            for variable_name in qml_generator_object.list_of_varnames:
                self.json_function_code_load += f"""				<zofar:scriptItem value="toLoad.add('{variable_name}')" />\n"""
        self.json_function_code_load += "\n"
        self.json_function_code_load += """				<!-- load all values from episodeObj -->\n"""
        self.json_function_code_load += """				<zofar:scriptItem value="zofar.getJsonProperties(episodeObj,toLoad)" />\n"""
        self.json_function_code_load += """			</zofar:action>\n"""
        self.json_function_code_load += "\n\n"

        return self.json_function_code_load

    def print_json_save(self) -> None:
        print(self.return_json_save())

    def return_json_save(self) -> str:
        # make sure that the list of fragment variable names is up to date
        self.create_list_of_fragment_variables_names()

        self.json_function_code_save += "\n"
        self.json_function_code_save += """			<!-- BAUKASTEN: BASIC page setup within loop when EXITING page -->\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """			<!-- last command: fragment json object into several variables -->\n"""
        self.json_function_code_save += """			<zofar:action\n"""
        self.json_function_code_save += f"""				command="zofar.frac(zofar.list({','.join(self.list_of_fragment_variables_names)}),zofar.jsonArr2str(defrac))"\n"""
        self.json_function_code_save += """				onExit="true">\n"""
        self.json_function_code_save += """				<!-- generic json setup -->\n"""
        self.json_function_code_save += """				<zofar:scriptItem\n"""
        self.json_function_code_save += f"""					value="zofar.assign('defrac',zofar.str2jsonArr(zofar.defrac(zofar.list({','.join(self.list_of_fragment_variables_names)}))))" />\n"""
        self.json_function_code_save += """				<zofar:scriptItem\n"""
        self.json_function_code_save += """					value="zofar.assign('episodeObj',zofar.getOrCreateJson(defrac,zofar.toInteger(episode_index.value))) " />\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """				<!--  initialize a map of variables to write to DB -->\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """				<zofar:scriptItem value="zofar.assign('toPersist',zofar.map())" />\n"""
        self.json_function_code_save += """					<!-- add variablenames and values to save to DB -->\n"""
        self.json_function_code_save += """						<!-- Syntax: toPersist.put('VARIABLENAME',VALUE) -->\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """					<!-- !!Important!! for SC to use valueID instead of Value -->\n"""
        self.json_function_code_save += """						<!-- Syntax: toPersist.put('VARIABLENAME',VARIABLENAME.valueId) -->\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """					<!-- all other variables: use value -->\n"""
        self.json_function_code_save += """						<!-- Syntax: toPersist.put('VARIABLENAME',VARIABLENAME.value) -->\n"""
        for qml_generator_object in self.list_of_question_qml_generator_objects:
            assert isinstance(qml_generator_object, Question_QML_generator)
            for variable_name in qml_generator_object.list_of_varnames:
                self.json_function_code_load += f"""				<zofar:scriptItem value="toPersist.put('{variable_name}',{variable_name}.value)" />\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """				<!-- write all values to episodeObj (still in RAM) -->\n"""
        self.json_function_code_save += """				<zofar:scriptItem value="zofar.setJsonProperties('episodeObj',episodeObj,toPersist)" />\n"""
        self.json_function_code_save += "\n"
        self.json_function_code_save += """				<!-- generic json setup -->\n"""
        self.json_function_code_save += """				<!-- save episode object into json array to DB -->\n"""
        self.json_function_code_save += """				<zofar:scriptItem value="zofar.assign('defrac',zofar.addOrReplaceJson(defrac,episodeObj,zofar.toInteger(episode_index.value)))" />\n"""
        self.json_function_code_save += """			</zofar:action>\n"""
        self.json_function_code_save += "\n\n"

        return self.json_function_code_save


x = Question_QML_generator('matrixQuestionSingleChoice', varname_stem='v32', index=1)
x.question_text = """Wie hoch schätzen Sie die Akzeptanz Ihrer Tätigkeit ein?"""
x.list_of_answer_option_labels = ['Regionalwissenschaften', 'Politikwissenschaften', 'Sozialwissenschaften',
                                  'Sozialwesen', 'Rechtswissenschaften', 'Verwaltungswissenschaften',
                                  'Wirtschaftswissenschaften',
                                  'Wirtschaftsingenieurwesen mit wirtschaftswiss. Schwerpunkt', 'Psychologie',
                                  'Erziehungswissenschaften', 'Anderes, und zwar']
x.list_of_answer_option_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
# x.list_of_answer_option_values = [i+1 for i in range(0, len(x.list_of_answer_option_labels))]
x.list_of_answer_option_uids = ['ao' + str(i + 1) for i in range(0, len(x.list_of_answer_option_labels))]

x.list_of_missing_answer_option_labels = []
x.list_of_missing_answer_option_values = []
x.list_of_missing_answer_option_uids = ['ao' + str(i + 1) for i in range(len(x.list_of_answer_option_labels),
                                                                         len(x.list_of_missing_answer_option_labels) + len(
                                                                             x.list_of_answer_option_labels))]

x.list_of_item_questions = ['seitens der Universitätsleitung', 'seitens der Berufungskommissionen',
                            'seitens der Berufungskommissionsvorsitzenden', 'seitens der Dekanate/Fakultäten',
                            'seitens der Fakultätsräte', 'seitens des akademischen Senats', 'seitens des Hochschulrats',
                            'seitens des zuständigen Ministeriums', 'seitens der Hochschulverwaltung',
                            'seitens der Bewerber_innen']

# x.print_question_qml()

y = Question_QML_generator('questionOpen', varname_stem='var001', index=1)
y.generate_question_open()
# y.print_question_qml()

# y.print_variable_declaration()
# x.print_variable_declaration()

list_of_question_generator_objects = []

open_question_count = 101

tmp_qml_list = []

trigger_generator = Question_QML_JSON_Trigger_generator(number_of_fragment_variables=200)

for i in range(open_question_count):
    count_str = len(str(open_question_count))
    tmp_varname_stem = 'testvar' + str(i).zfill(count_str)
    tmp_question_generator_object = Question_QML_generator(question_type='questionOpen',
                                                           question_text=f'{tmp_varname_stem}: ',
                                                           varname_stem=tmp_varname_stem,
                                                           index=i + 1)
    trigger_generator.add_question_qml_generator(tmp_question_generator_object)

# trigger_generator.print_all_qml_code()

# # trigger_generator.create_list_of_fragment_variables_names()
# trigger_generator.print_json_load()
# trigger_generator.print_json_save()
#
# trigger_generator.print_variable_declaration_str()
trigger_generator.write_to_qml_file()

if 'PROJECTFOLDER' in os.environ.keys():
    source_file = Path(here.parent, 'output', 'questionnaire.xml')
    assert source_file.exists()
    shutil.copy(source_file, target_project_xml)
