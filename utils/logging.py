from datetime import datetime

from wrappers import botConfig


def log(*args):
    print(end="\r")
    print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args)
    if botConfig.LOG_FILE != "":
        with open(botConfig.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args, file=f)


def dlog(*args):
    if botConfig.ENABLE_DEBUG:
        print(end="\r")
        print("\033[90m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, end="\033[97m\n")
        if botConfig.LOG_FILE != "":
            with open(botConfig.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, file=f)


def elog(*args):
    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, end="\033[97m\n")
    if botConfig.LOG_FILE != "":
        with open(botConfig.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, file=f)
