from abc import ABC

import datetime
import random
import string
from collections import defaultdict

# pip install python-snappy
import snappy

# pip install python-lorem
import lorem
from dataclasses import dataclass
import abc
import math
import json
import pprint


def hexdecode_and_decompress(input_str: str) -> str:
    hexdecoded_bytes = bytes.fromhex(input_str)
    decompressed_bytes = snappy.decompress(hexdecoded_bytes)
    return decompressed_bytes.decode('utf-8')


def return_lorem_text(length: int = 2000):
    para1 = ''
    while len(para1) < length:
        para1 += next(lorem.paragraph(count=1, comma=(0, 2), word_range=(12, 13), sentence_range=(30, 35))) + ' '
    return para1[:1999] + '.'


def create_test_dict(number_of_keys: int, val_length: int) -> dict:
    tmp_dict = {}
    for i in range(number_of_keys):
        max_str_length_i = len(str(number_of_keys))
        key = f'key' + str(i).zfill(max_str_length_i)
        tmp_dict[key] = return_random_string(val_length)
    return tmp_dict


def return_random_string(length: int) -> string:
    all_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + ' []{}()_-'
    tmp_str = ''
    for i in range(length):
        tmp_str += random.choice(all_chars)
    return tmp_str


def hexencode_and_compress(input_str: str) -> str:
    tmp_byteencoded = input_str.encode('utf-8')
    tmp_hexencoded = tmp_byteencoded.hex()
    return snappy.compress(tmp_hexencoded)


def compress(input_str: str) -> str:
    return snappy.compress(input_str)


class FormalZofarQuestionInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'return_random_ao_json_str') and
                callable(subclass.return_random_ao_json_str))


@dataclass
@FormalZofarQuestionInterface.register
class ZofarQuestion:
    """Superclass for simulating zofar question"""
    list_of_variable_names: list

    def return_random_ao_json_str(self):
        raise NotImplementedError()

    def return_details(self):
        raise NotImplementedError()


@dataclass
class ZofarQuestionSingleChoice(ZofarQuestion, ABC):
    no_of_answer_options: int
    question_type: str = 'questionSingleChoice'
    list_of_answer_options: list = None

    def set_up(self):
        # check interface
        assert issubclass(self.__class__, FormalZofarQuestionInterface)

        # create list of answer options
        self.list_of_answer_options = ['ao' + str(i) for i in range(self.no_of_answer_options)]
        # check if exactly one variable name is given
        assert len(self.list_of_variable_names) == 1
        # check if varname is a str
        assert isinstance(self.list_of_variable_names[0], str)
        # assert that varname is str of length > 0
        assert len(self.list_of_variable_names[0]) > 0

    def return_random_ao_json_str(self):
        self.set_up()
        ao = random.choice(self.list_of_answer_options)
        varname = self.list_of_variable_names[0]
        return f'"{varname}":"{ao}"'

    def return_details(self) -> str:
        output_str = f'{self.question_type=}, {self.list_of_variable_names=}, {self.no_of_answer_options=}'
        return output_str


@dataclass
class ZofarQuestionSingleChoiceMatrix(ZofarQuestion, ABC):
    no_of_answer_options: int
    question_type = 'questionSingleChoiceMatrix'
    list_of_answer_options: list = None
    list_of_sc_question_objects: list = None

    def set_up(self):
        # clear self.list_of_sc_question_objects
        self.list_of_sc_question_objects = []
        # check interface
        assert issubclass(self.__class__, FormalZofarQuestionInterface)

        # create list of answer options
        self.list_of_answer_options = ['ao' + str(i) for i in range(self.no_of_answer_options)]
        # check if exactly one variable name is given
        assert len(self.list_of_variable_names) > 0
        # iterate over all varnames
        for varname in self.list_of_variable_names:
            try:
                # check if varname is a str
                assert isinstance(varname, str)
                # assert that varname is str of length > 0
                assert len(varname) > 0
            except AssertionError as e:
                print(f'{varname=}')
                print(f'{e=}')
            self.list_of_sc_question_objects.append(
                ZofarQuestionSingleChoice(no_of_answer_options=self.no_of_answer_options,
                                          list_of_variable_names=[varname]))

    def return_random_ao_json_str(self):
        self.set_up()
        list_of_json_strings = []
        for question_object in self.list_of_sc_question_objects:
            list_of_json_strings.append(question_object.return_random_ao_json_str())
        return ','.join(list_of_json_strings)

    def return_details(self) -> str:
        output_str = f'{self.question_type=}, {self.list_of_variable_names=}, {self.no_of_answer_options=}'
        return output_str


@dataclass
class ZofarQuestionMultipleChoice(ZofarQuestion, ABC):
    question_type: str = 'questionMultipleChoice'
    list_of_answer_options: tuple = tuple(['True', 'False'])

    def return_random_ao_json_str(self):
        list_of_json_strings = []
        for varname in self.list_of_variable_names:
            value = random.choice(self.list_of_answer_options)
            list_of_json_strings.append(f'"{varname}":"{value}"')
        return ','.join(list_of_json_strings)

    def return_details(self) -> str:
        output_str = f'{self.question_type=}, {self.list_of_variable_names=}, {self.list_of_answer_options=}'
        return output_str


@dataclass
class ZofarQuestionMultipleChoiceMatrix(ZofarQuestion, ABC):
    no_of_answer_options: int
    question_type = 'questionMultipleChoiceMatrix'

    list_of_indexed_variable_names: list = None
    list_of_mc_question_objects: list = None

    def set_up(self):
        # clear self.list_of_mc_question_objects
        self.list_of_mc_question_objects = []
        # check interface
        assert issubclass(self.__class__, FormalZofarQuestionInterface)

        # create list of items
        self.list_of_indexed_variable_names = [f'{j}_{k}' for j in self.list_of_variable_names for k in
                                               range(self.no_of_answer_options)]
        # check if exactly one variable name is given
        assert len(self.list_of_variable_names) > 0
        # iterate over all varnames
        for varname in self.list_of_indexed_variable_names:
            try:
                # check if varname is a str
                assert isinstance(varname, str)
                # assert that varname is str of length > 0
                assert len(varname) > 0
            except AssertionError as e:
                print(f'{varname=}')
                print(f'{e=}')
            self.list_of_mc_question_objects.append(
                ZofarQuestionMultipleChoice(list_of_variable_names=[varname]))

    def return_random_ao_json_str(self):
        self.set_up()
        list_of_json_strings = []
        for question_object in self.list_of_mc_question_objects:
            list_of_json_strings.append(question_object.return_random_ao_json_str())
        return ','.join(list_of_json_strings)

    def return_details(self) -> str:
        output_str = f'{self.question_type=}, {self.list_of_variable_names=}, {self.no_of_answer_options=}'
        return output_str


@dataclass
class ZofarQuestionOpen(ZofarQuestion, ABC):
    question_type: str = 'questionOpen'
    length_of_text: int = 2000
    random_characters: bool = True

    def return_random_ao_json_str(self):
        varname = self.list_of_variable_names[0]

        if self.random_characters:
            return f'"{varname}":"{return_random_string(self.length_of_text)}"'
        else:
            return f'"{varname}":"{return_lorem_text(self.length_of_text)}"'

    def return_details(self) -> str:
        output_str = f'{self.question_type=}, {self.list_of_variable_names=}, {self.length_of_text=}'
        return output_str


class Timestamp:
    def __init__(self, min_date: datetime.date, max_date: datetime.date):
        self.min_date = min_date
        self.max_date = max_date

    def return_random_timestamp_inbetween(self) -> str:
        tmp_timedelta = self.max_date - self.min_date
        random_diff = tmp_timedelta * random.random()
        output = self.min_date + random_diff
        return output.strftime("%Y-%m-%dT%H-%M-%SZ")


a = Timestamp(min_date=datetime.date(year=2018, month=2, day=23),
              max_date=datetime.date(year=2028, month=12, day=31))
a.return_random_timestamp_inbetween()


class ZofarQuestionCollection:
    def __init__(self, numer_of_episodes: int = 1, chars_per_db_variable: int = 1500):
        self.list_of_zofar_questions = []
        self.number_of_episodes = numer_of_episodes
        self.chars_per_db_variable = chars_per_db_variable
        self.min_date = datetime.date(year=2018, month=2, day=23)
        self.max_date = datetime.date(year=2028, month=12, day=31)
        self.timestamp_object = Timestamp(min_date=self.min_date, max_date=self.max_date)

    def add_question_object(self, question_object: ZofarQuestion):
        self.list_of_zofar_questions.append(question_object)

    def return_random_ao_json_str(self):
        output_list_of_jsons = []
        for i in range(self.number_of_episodes):
            header = f'"id": {i}, '
            header += f'"startDate":"{self.timestamp_object.return_random_timestamp_inbetween()}",'
            header += f'"endDate":"{self.timestamp_object.return_random_timestamp_inbetween()}",'
            header += f'"typeColor":"black",'
            header += f'"type":"Slot2",'
            header += f'"state":"new"'
            list_of_random_json = [header]
            for question in self.list_of_zofar_questions:
                list_of_random_json.append(question.return_random_ao_json_str())
            output_list_of_jsons.append(', '.join(list_of_random_json))
        return '[{' + '},{'.join(output_list_of_jsons) + '}]'

    def print_statistics(self):
        print('\n\n')
        raw_output = self.return_random_ao_json_str()
        print(f'JSON string: {raw_output}')
        list_of_json_objects = json.loads(raw_output)
        new_list = []
        for json_object in list_of_json_objects:
            new_dict = {}
            for key, val in json_object.items():
                tmp_val = val
                if isinstance(val, str):
                    if len(val) > 25:
                        tmp_val = tmp_val[:10] + '...' + tmp_val[-10:] + '(length=2000)'
                new_dict[key] = tmp_val
            new_list.append(new_dict)
        pprint.pprint(new_list)
        print('\n'*2)
        print('#'*80)

        print(f'{self.number_of_episodes=}')
        tmp_details_list = [question_object.return_details() for question_object in self.list_of_zofar_questions]
        tmp_details_str = '\n'.join(tmp_details_list)
        print(tmp_details_str)

        print(f'{len(raw_output)=}')
        hexencoded_and_compressed = hexencode_and_compress(raw_output)
        print(f'{len(hexencoded_and_compressed)=}')
        print(f' would need: {math.ceil(len(hexencoded_and_compressed) / self.chars_per_db_variable)} zofar variables.')
        compressed = compress(raw_output)
        print(f'{len(compressed)=}')
        print(f' would need: {math.ceil(len(compressed) / self.chars_per_db_variable)} zofar variables.')


y = ZofarQuestionCollection(numer_of_episodes=20)

y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=10, list_of_variable_names=['var01']))
y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=5, list_of_variable_names=['var02']))
y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=3, list_of_variable_names=['var03']))
y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=10, list_of_variable_names=['var15']))
y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=5, list_of_variable_names=['var16']))
y.add_question_object(ZofarQuestionSingleChoice(no_of_answer_options=3, list_of_variable_names=['var17']))

y.add_question_object(ZofarQuestionMultipleChoice(list_of_variable_names=['var04', 'var05', 'var06']))
y.add_question_object(ZofarQuestionMultipleChoice(list_of_variable_names=['var18', 'var19', 'var20']))
y.add_question_object(
    ZofarQuestionMultipleChoiceMatrix(no_of_answer_options=5, list_of_variable_names=['var07', 'var08', 'var09']))

y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var10'], random_characters=False))
y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var11'], random_characters=False))
y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var12'], random_characters=False))
y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var13'], random_characters=False))
y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var14'], random_characters=False))
y.add_question_object(ZofarQuestionOpen(list_of_variable_names=['var15'], random_characters=False))

y.print_statistics()

print('###')

if False:
    s = 'bc02685b7b226964223a302c227374617465223a226e6577222c22747970010d10536c6f74320d0f2c436f6c6f72223a2272656422052f08727444093374323032302d30332d30315430313a30303a30302e3030305a222c22656e64192518332d30322d32384225004473665f7661613031223a66616c73657d2c7b111300350d13002c05a600310577fea600fea60011a6005d'
    b = bytes.fromhex(s)

    t = snappy.decompress(b)
    r = t.decode('utf-8')
    print(r)

    test_dict = create_test_dict(number_of_keys=100, val_length=2000)

    print(len(str(test_dict)))

    x = hexencode_and_compress(str(test_dict))
    print(len(x))
    y = compress(str(test_dict))
    print(len(y))
    print()

    print(f'{len(r*1000)=}')
    z1 = hexencode_and_compress(input_str=r * 1000)
    z2 = compress(input_str=r * 1000)
    print(f'{len(z1)=}')
    print(f'{len(z2)=}')
    print()
