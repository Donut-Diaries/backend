from datetime import datetime


def id_from_datetime() -> str:
    """
    Creates a unique id from the current timestamp.

    Format used: `%Y%m%d%H%M%S%f`

    Example id: `20240419000056631770`

    Returns:
        str: Current timestamp down to microseconds.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S%f")
