import json


def json_print(sentence, args=None):
    """
        To json print for receiving data from javascript JSON parser
    """
    if args:
        sentence += json.dumps(str(args))
    print(json.dumps(sentence, ensure_ascii=False))