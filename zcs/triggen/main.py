from zcs.data.xml import read_questionnaire
from tkinter.filedialog import asksaveasfilename
from pathlib import Path
import os
from zcs.caljson.main import Question_QML_generator, Question_QML_JSON_Trigger_generator
import shutil


def main():
    if 'PROJECTFOLDER' in os.environ.keys():
        target_project_folder = Path(os.getenv('PROJECTFOLDER'), 'src', 'main', 'resources')
        assert target_project_folder.exists()
        target_project_xml = Path(target_project_folder, 'questionnaire.xml')

    else:
        target_project_xml = asksaveasfilename(filetypes=[('questionnaire*.xml', 'questionnaire*.xml')])

    x = Question_QML_generator('matrixQuestionSingleChoice', varname_stem='v32', index=1)
    x.question_text = """Wie hoch schätzen Sie die Akzeptanz Ihrer Tätigkeit ein?"""
    x.list_of_answer_option_labels = ['Regionalwissenschaften', 'Politikwissenschaften', 'Sozialwissenschaften',
                                      'Sozialwesen', 'Rechtswissenschaften', 'Verwaltungswissenschaften',
                                      'Wirtschaftswissenschaften',
                                      'Wirtschaftsingenieurwesen mit wirtschaftswiss. Schwerpunkt', 'Psychologie',
                                      'Erziehungswissenschaften', 'Anderes, und zwar']
    x.list_of_answer_option_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    x.list_of_answer_option_uids = ['ao' + str(i + 1) for i in range(0, len(x.list_of_answer_option_labels))]

    x.list_of_missing_answer_option_labels = []
    x.list_of_missing_answer_option_values = []
    x.list_of_missing_answer_option_uids = ['ao' + str(i + 1) for i in range(len(x.list_of_answer_option_labels),
                                                                             len(x.list_of_missing_answer_option_labels) + len(
                                                                                 x.list_of_answer_option_labels))]

    x.list_of_item_questions = ['seitens der Universitätsleitung', 'seitens der Berufungskommissionen',
                                'seitens der Berufungskommissionsvorsitzenden', 'seitens der Dekanate/Fakultäten',
                                'seitens der Fakultätsräte', 'seitens des akademischen Senats',
                                'seitens des Hochschulrats',
                                'seitens des zuständigen Ministeriums', 'seitens der Hochschulverwaltung',
                                'seitens der Bewerber_innen']

    y = Question_QML_generator('questionOpen', varname_stem='var001', index=1)
    y.generate_question_open()

    open_question_count = 101

    trigger_generator = Question_QML_JSON_Trigger_generator(number_of_fragment_variables=200)

    for i in range(open_question_count):
        count_str = len(str(open_question_count))
        tmp_varname_stem = 'testvar' + str(i).zfill(count_str)
        tmp_question_generator_object = Question_QML_generator(question_type='questionOpen',
                                                               question_text=f'{tmp_varname_stem}: ',
                                                               varname_stem=tmp_varname_stem,
                                                               index=i + 1)
        trigger_generator.add_question_qml_generator(tmp_question_generator_object)

    trigger_generator.write_to_qml_file()

    if 'PROJECTFOLDER' in os.environ.keys():
        source_file = Path(os.path.abspath('output'), 'questionnaire.xml')
        assert source_file.exists()
        shutil.copy(source_file, target_project_xml)


if __name__ == '__main__':
    main()
