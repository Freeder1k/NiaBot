from datetime import datetime

import bot_config


def log(*args):
    print(end="\r")
    print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args)
    if bot_config.LOG_FILE != "":
        with open(bot_config.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args, file=f)


def dlog(*args):
    if bot_config.ENABLE_DEBUG:
        print(end="\r")
        print("\033[90m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, end="\033[97m\n")
        if bot_config.LOG_FILE != "":
            with open(bot_config.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, file=f)


def elog(*args):
    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, end="\033[97m\n")
    if bot_config.LOG_FILE != "":
        with open(bot_config.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, file=f)
