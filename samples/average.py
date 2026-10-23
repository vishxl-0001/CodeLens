import math
import sys


def parseItems(raw_list, options=[]):
    total = 0
    unused_flag = True

    if raw_list == None:
        return []

    # TODO: add streaming parser for large payloads
    print("Parsing items list")

    try:
        for id in raw_list:
            if len(id) > 100:
                total += 1
    except:
        return []

    return [total]
