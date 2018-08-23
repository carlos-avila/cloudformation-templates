import random
import string


def gen_random_string(length, allowed_chars):
    """
    Returns a securely generated random string.
    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """

    return ''.join(random.SystemRandom().choice(allowed_chars) for i in range(length))


def gen_secret_key():
    return gen_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)')


def gen_honeypot_name():
    return gen_random_string(16, string.ascii_letters + string.digits)


def gen_db_password():
    return gen_random_string(64, string.ascii_letters + string.digits)


def gen_email_pass():
    return gen_random_string(64, string.ascii_letters + string.digits)
