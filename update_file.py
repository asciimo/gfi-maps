"""
A module for reading and writing to updated.dat
"""
import dateutil.parser


def get_last_update(default_datetime):
    """
    Return a datetime object representing the timestamp stored in updated.dat
    :param default_datetime:
    :return:
    """

    last_updated_datetime = None

    try:
        with open('updated.dat', 'r') as update_file:
            # RFC 3339 format e.g. 2017-07-05T03:15:14.024Z
            last_updated = update_file.read().strip()
            if last_updated:
                try:
                    last_updated_datetime = dateutil.parser.parse(last_updated)
                except ValueError as error:
                    print("Can't parse %s into datetime: %s" % (last_updated, str(error)))
                    return default_datetime
    except IOError as error:
        print("There was a problem reading updated.dat: %s" % str(error))
        return default_datetime

    return last_updated_datetime


def set_last_update(timestamp):
    """
    Write a timestamp to updated.dot
    :param timestamp: string
    :return: boolean
    """

    try:
        with open('updated.dat', 'w') as update_file:
            update_file.write(timestamp)
    except IOError as error:
        print("There was a problem writing to updated.dat: %s" % str(error))

    return True
