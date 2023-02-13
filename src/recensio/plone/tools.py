def convertToString(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, list):
        return [convertToString(x) for x in obj]
    elif isinstance(obj, dict):
        retval = {}
        for key, value in obj.items():
            retval[key] = convertToString(value)
        return retval
    else:
        return obj
