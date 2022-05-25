from zcs.data.xml import read_questionnaire
from tkinter.filedialog import askopenfilename
from pathlib import Path
import os
from zcs.data.qml import gen_trigger_dict
import shutil


def main():
    input_xml = askopenfilename()
    trig_gen = gen_trigger_dict(input_xml=input_xml, page_name_startswith='')

    for page_name, trigger_dict in trig_gen.items():
        print(f'<!-- {page_name} -->')
        for trigger_name, trigger_data in trigger_dict.items():
            print(f'<!-- {trigger_name.upper()} TRIGGER -->')

            if trigger_name == 'reset':
                print("""<zofar:action command="zofar.nothing()" onExit="false">\n""")
                print("""<!-- reset page variables -->\n""")
            elif trigger_name == 'load':
                print()
            elif trigger_name == 'save':
                print()
            print('\n'.join(trigger_data))


            print("""</zofar:action>\n""")
        print('\n\n')
    breakpoint()


if __name__ == '__main__':
    main()
