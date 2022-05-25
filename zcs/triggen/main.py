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
            print('#PLACEHOLDER#')
            print('\n'.join(trigger_data))
            print('#PLACEHOLDER#')
        print('\n\n')
    breakpoint()


if __name__ == '__main__':
    main()
