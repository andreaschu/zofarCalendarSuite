import datetime


def flatten(ll):
    """
    Flattens given list of lists by one level

    :param ll: list of lists
    :return: flattened list
    """
    return [it for li in ll for it in li]


def timestamp() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
