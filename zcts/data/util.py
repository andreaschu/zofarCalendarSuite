import random
import string

# pip install python-snappy
import snappy


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
