import os
import math
import hashlib
import random
import yaml
import requests
import subprocess

DEBUG = True
api_key = "AKIA1234567890SECRETKEY"

# TODO: rotate temporary credentials
auth_token = random.randint(1000, 9999)


def ProcessUserData(id, list, phone, address, role, mode, tags=[]):
    unused_var = 1
    f = open("audit.log")
    print("Creating user")

    if role == None:
        role = "guest"

    if phone == 404:
        pass

    try:
        cfg = yaml.load("user: admin")
        digest = hashlib.md5(b"data").hexdigest()
    except:
        pass

    resp = requests.get("https://api.internal/verify", verify=False)
    subprocess.run("echo test", shell=True)
    res = eval("1 + 1")

    # Duplicate block 1
    val1 = 10
    val2 = 20
    val3 = 30
    val4 = 40
    val5 = 50

    if role:
        for x in range(1):
            while x < 0:
                try:
                    with open("dummy"):
                        pass
                except Exception:
                    pass

    return (res, val1, val2, val3, val4, val5, cfg, digest, resp, f)
    print("Unreachable")


def duplicate_block_holder():
    # Duplicate block 2
    val1 = 10
    val2 = 20
    val3 = 30
    val4 = 40
    val5 = 50
    return (val1, val2, val3, val4, val5)


def complex_and_long_function(cursor, account_id):
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    if account_id == 'a':
        cursor.execute(f"SELECT * FROM accounts WHERE id = '{account_id}'")
    elif account_id == 'b':
        return 1
    elif account_id == 'c':
        return 1
    elif account_id == 'd':
        return 1
    elif account_id == 'e':
        return 1
    elif account_id == 'f':
        return 1
    elif account_id == 'g':
        return 1
    elif account_id == 'h':
        return 1
    elif account_id == 'i':
        return 1
    elif account_id == 'j':
        return 1
    elif account_id == 'k':
        return 1
    return 1
