import jsonpickle


def dumps(obj):
    return jsonpickle.dumps(obj, indent=2, unpicklable=False)
