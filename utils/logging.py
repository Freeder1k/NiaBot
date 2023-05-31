from datetime import datetime

import const


def log(*args):
    print(end="\r")
    print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args)
    if const.LOG_FILE != "":
        with open(const.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args, file=f)


def dlog(*args):
    if const.ENABLE_DEBUG:
        print(end="\r")
        print("\033[90m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, end="\033[97m\n")
        if const.LOG_FILE != "":
            with open(const.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, file=f)


def elog(*args):
    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, end="\033[97m\n")
    if const.LOG_FILE != "":
        with open(const.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, file=f)
