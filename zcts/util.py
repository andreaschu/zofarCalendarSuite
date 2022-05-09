def flatten(ll):
    """
    Flattens given list of lists by one level

    :param ll: list of lists
    :return: flattened list
    """
    return [it for li in ll for it in li]

