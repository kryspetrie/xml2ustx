import importlib.resources


def get_resource_path(resource):
    """
    Returns the absolute path to a resource file within a package.
    """
    return importlib.resources.files(__package__).joinpath(resource)


def read_resource_file(resource):
    """
    Reads and returns the content of a resource file within a package.
    """
    return importlib.resources.files(__package__).joinpath(resource).read_text()