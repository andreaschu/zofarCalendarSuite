# pip install python-snappy
import snappy
import random
import string
from collections import defaultdict


def hexdecode_and_decompress(input_str: str) -> str:
    hexdecoded_bytes = bytes.fromhex(input_str)
    decompressed_bytes = snappy.decompress(hexdecoded_bytes)
    return decompressed_bytes.decode('utf-8')


s = 'bc02685b7b226964223a302c227374617465223a226e6577222c22747970010d10536c6f74320d0f2c436f6c6f72223a2272656422052f08727444093374323032302d30332d30315430313a30303a30302e3030305a222c22656e64192518332d30322d32384225004473665f7661613031223a66616c73657d2c7b111300350d13002c05a600310577fea600fea60011a6005d'
b = bytes.fromhex(s)

t = snappy.decompress(b)
r = t.decode('utf-8')
print(r)


def create_test_dict(number_of_keys: int, val_length: int) -> dict:
    tmp_dict = {}
    for i in range(number_of_keys):
        max_str_length_i = len(str(number_of_keys))
        key = f'key' + str(i).zfill(max_str_length_i)
        tmp_dict[key] = random_string_generator(val_length)
    return tmp_dict


def random_string_generator(length: int) -> string:
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
