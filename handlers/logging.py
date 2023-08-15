import traceback
from datetime import datetime

from discord import Client, Embed

from wrappers import botConfig

_client: Client


def log(*args):
    print(end="\r")
    print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args)
    if botConfig.LOG_FILE != "":
        with open(botConfig.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "]", *args, file=f)


def log_debug(*args):
    if botConfig.ENABLE_DEBUG:
        print(end="\r")
        print("\033[90m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, end="\033[97m\n")
        if botConfig.LOG_FILE != "":
            with open(botConfig.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (DEBUG)", *args, file=f)


def log_error(*args):
    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, end="\033[97m\n")
    if botConfig.LOG_FILE != "":
        with open(botConfig.LOG_FILE, 'a') as f:
            print("[" + datetime.now().strftime("%H:%M:%S") + "] (ERROR)", *args, file=f)


async def log_exception(e: Exception, discord: bool = True):
    tb = traceback.format_exc()

    if discord:
        devs = {uid: _client.get_user(uid) for uid in botConfig.DEV_USER_IDS}

        embed = Embed(
            color=botConfig.ERROR_COLOR,
            title=f"A wild ``{e.__class__.__name__}`` appeared!",
            description=f"```\n{tb[-4000:]}```"
        )
        for uid, dev in devs.items():
            try:
                await dev.send(embed=embed)
            except Exception as e:
                log_error(f"Couldn't contact dev with user ID {uid}.\n{e.__class__.__name__}: {e}")

    print(end="\r")
    print("\033[91m" + "[" + datetime.now().strftime("%H:%M:%S") + "] (EXCEPTION)", tb, end="\033[97m\n")
    if botConfig.LOG_FILE != "":
        try:
            with open(botConfig.LOG_FILE, 'a') as f:
                print("[" + datetime.now().strftime("%H:%M:%S") + "] (EXCEPTION)", tb, file=f)
        except:
            traceback.print_exc()


def init_logger(client: Client):
    global _client
    _client = client
