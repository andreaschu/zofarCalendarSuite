from zcs.data.xml import read_questionnaire
from tkinter.filedialog import askopenfilename
from pathlib import Path
import os
from zcs.data.qml import gen_trigger_dict
import shutil


def main():
    input_xml = askopenfilename()
    trig_gen = gen_trigger_dict(input_xml=input_xml, page_name_startswith='')
    breakpoint()


if __name__ == '__main__':
    main()
