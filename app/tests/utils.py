import random
import string


def random_lower_string(k=10):
    return "".join(random.choices(string.ascii_lowercase, k=k))
