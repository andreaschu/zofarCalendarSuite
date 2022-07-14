import os.path
from pathlib import Path
from zcs.data.qml import generate_trigger
from zcs.util.calc import calculate

XML_INPUT_PATH = os.environ['XML_INPUT_PATH']

if __name__ == '__main__':
    xml_source = os.environ[XML_INPUT_PATH]
    calculate(XML_INPUT_PATH)
    output_folder = Path(os.path.abspath(''), 'output')
    if not output_folder.exists(): output_folder.mkdir(exist_ok=True, parents=True)
    pagename_startswith = 'nset'
    fragment_var_list = ['episodes_fragment_1',
                         'episodes_fragment_2',
                         'episodes_fragment_3',
                         'episodes_fragment_4']
    Path(output_folder, 'out_trigger.txt').write_text(
        data=generate_trigger(input_xml=xml_source,
                              page_name_startswith=pagename_startswith,
                              fragment_var_list=fragment_var_list),
        encoding='utf-8')
