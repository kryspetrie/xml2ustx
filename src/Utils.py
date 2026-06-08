"""Utility functions for XML to USTX conversion."""
import jsonpickle


def dumps(obj):
    """Serialize an object to a JSON string."""
    return jsonpickle.dumps(obj, indent=2, unpicklable=False)
