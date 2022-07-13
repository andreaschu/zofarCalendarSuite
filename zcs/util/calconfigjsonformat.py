import re
import sys
from tkinter import Tk, scrolledtext, Frame
import tkinter
from util.log import Loggable
from zcs.util.util import use_clipboard
import json
import pprint
import codecs

def prepare_json_str(input_str: str, text_to_replace: str) -> str:
    input_str = input_str.strip()
    input_str = re.sub('\s', '', input_str)
    input_str = re.sub('\n', '', input_str)
    input_str = re.sub('\r', '', input_str)
    try:
        assert input_str.startswith('"')
        assert input_str.endswith('"')
    except AssertionError as err:
        print(err)
        raise AssertionError("""The input string does not start or does not terminate with '"'! """)
    # strip leading and trailing double quote
    tmp_str = input_str[1:-1]
    # ensure that there are no double quotes left
    assert tmp_str.find('"') == -1
    # replace html quote escapes
    tmp_str = tmp_str.replace('&quot;', '"')

    text_to_replace = '".concat(episode_property_type_value.value).concat("}}")'
    flag_concat = False
    if tmp_str.find(text_to_replace) != -1:
        flag_concat = True
    if flag_concat:
        tmp_str = tmp_str.replace(text_to_replace, '"XXXX"}}"')
    tmp_str = tmp_str[1:-1]
    tmp_str = tmp_str.replace("'", '"')
    return tmp_str

def pretty_print_json_config(input_str: str) -> str:
    tmp_str = prepare_json_str(input_str)
    input_dict = json.loads(tmp_str)
    output_str = json.dumps(input_dict, indent=4, sort_keys=False)
    output_str = output_str.replace('"', "'")
    if flag_concat:
        output_str = output_str[:output_str[:output_str.rfind('}')].rfind('}')]
        output_str = '"' + output_str.replace("'XXXX'", text_to_replace)
    else:
        output_str = '"' + output_str + '"'
    output_str = output_str.replace('"', '&quot;')
    output_str = '"' + output_str + '"'
    output_str = output_str.encode('utf-8').decode( 'unicode-escape' )
    assert identical_without_whitespaces(input_str, output_str)
    return output_str

def identical_without_whitespaces(str1: str, str2: str) -> bool:
    tmp_str1 = re.sub(r'\s', '', str1)
    tmp_str2 = re.sub(r'\s', '', str2)
    return tmp_str1 == tmp_str2

class Window(Loggable, tkinter.Frame):
    """
    main application
    """

    def __init__(self, master=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_error_email = None
        self.logger.info('starting up')

        self.master = master

        # menu = tkinter.Menu(self.master)
        # self.master.config(menu=menu)
        self.label_text_box0 = tkinter.Label(self.master, text='Input:')
        self.label_text_box0.grid(row=0, column=1, sticky='W')
        self.label_text_box1 = tkinter.Label(self.master, text='Output:')
        self.label_text_box1.grid(row=0, column=2, sticky='W')

        self.text0 = scrolledtext.ScrolledText(master, width=40, height=30)
        self.text0.grid(row=1, column=1, rowspan=20, sticky='N')
        self.text1 = scrolledtext.ScrolledText(master, width=40, height=30)
        self.text1.grid(row=1, column=2, rowspan=20, sticky='N')

        self.button0 = tkinter.Button(master, width=15, height=2, text='pretty print',
                                      command=self.process_json_to_pretty_print)
        self.button0.grid(row=1, column=3, sticky='N')
        self.button0 = tkinter.Button(master, width=15, height=2, text='copy output',
                                      command=self.copy_output)
        self.button0.grid(row=2, column=3, sticky='N')

    def process_json_to_pretty_print(self):
        input_str = self.text0.get(1.0, tkinter.END).strip()
        output_str = pretty_print_json_config(input_str)
        self.text1.delete(1.0, tkinter.END)
        self.text1.insert(1.0, output_str)
        # use_clipboard(output_str)



    def copy_output(self):
        print(self.text1.get(1.0, tkinter.END))
        use_clipboard(self.text1.get(1.0, tkinter.END))


def startup_main_window(window_title: str) -> tuple:
    tmp_root = tkinter.Tk()
    tmp_app = Window(master=tmp_root)
    tmp_root.wm_title("zofar calendar suite - " + window_title)
    tmp_root.geometry('800x600')
    tmp_root.mainloop()
    return tmp_app, tmp_root


if __name__ == '__main__':
    startup_main_window('Calendar Config Json Formatter')
