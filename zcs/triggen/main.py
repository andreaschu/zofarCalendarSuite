from tkinter.filedialog import askopenfilename, asksaveasfilename
from pathlib import Path
from zcs.data.qml import gen_trigger_dict, gen_trigger_str


def main():
    input_xml = askopenfilename()
    trigger_dict = gen_trigger_dict(input_xml=input_xml, page_name_startswith='vaa')

    fragment_var_name_stem = 'episodes_fragment'
    number_of_fragments = 4
    fragment_var_list = [fragment_var_name_stem+str(i+1) for i in range(number_of_fragments)]

    trigger_string = gen_trigger_str(trigger_dict, fragment_list=fragment_var_list)

    output_file_str = asksaveasfilename(initialfile='trigger_output.txt', )
    if output_file_str != '':
        Path(output_file_str).write_text(trigger_string, encoding='utf-8')

    print(trigger_string)


if __name__ == '__main__':
    main()
