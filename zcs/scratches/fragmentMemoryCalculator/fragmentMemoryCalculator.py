import random
import string

# pip install python-snappy
import snappy

# pip install python-lorem
# import lorem


def hexdecode_and_decompress(input_str: str) -> str:
    hexdecoded_bytes = bytes.fromhex(input_str)
    decompressed_bytes = snappy.decompress(hexdecoded_bytes)
    return decompressed_bytes.decode('utf-8')

#
# def return_lorem_text(length: int = 2000):
#     para1 = ''
#     while len(para1) < length:
#         # noinspection PyTypeChecker
#         para1 += next(lorem.paragraph(count=1, comma=(0, 2), word_range=(12, 13), sentence_range=(30, 35))) + ' '
#     return para1[:1999] + '.'


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


def compress_and_hexencode(input_str: str) -> str:
    return hexencode_bytes(compress(input_str))


def hexencode_and_compress(input_str: str) -> bytes:
    return compress(hexencode_str(input_str))


def hexencode_str(input_str: str) -> str:
    return hexencode_bytes(input_str.encode('utf-8'))


def hexencode_bytes(input_str: bytes) -> str:
    return input_str.hex()


def compress(input_str: str) -> bytes:
    return snappy.compress(input_str.encode('utf-8'))
