import psutil
import math
from hashlib import md5


def bytes_conversion(number):
    if number == 0:
        return '0 B'

    unit_dict = {
        0: "B",  1: "kB",
        2: "MB", 3: "GB",
        4: "TB", 5: "PB",
        6: "EB"
    }

    length_number = int(math.log10(number))
    num_length = length_number // 3
    number = '%.2f' % (int(number)/(1 << (length_number//3) * 10))

    return "%s %s" % (number, unit_dict[num_length])


def cpu_percent():
    return psutil.cpu_percent(interval=1)


def total_memory():
    mem = psutil.virtual_memory()
    return mem.total


def compute_gravatar_url(email):
    email = email.strip().lower()
    hash = md5(email.encode("utf8")).hexdigest()
    return 'https://www.gravatar.com/avatar/{hash}?s=128'.format(hash=hash)
