import threading

import discord
import gspread

from common import logging

WAR_ROLES = {
    901347453062758400: 0,  # Tank
    901347037424017429: 1,  # DPS
    901346718669479967: 2,  # Healer
    1191217022546231446: 3,  # HQ War
}

sa = gspread.service_account(filename="data/google_cred.json")
sheet = sa.open_by_key("1_88gZ3JoH3amJprIyxw4oT-vDUwbISoV5l1hRYdGKVI").sheet1

lock = threading.Lock()


async def on_member_role_update(member: discord.Member, added: list[discord.Role], removed: list[discord.Role]):
    roles = [[False, False, False, False]]
    for role in member.roles:
        if role.id in WAR_ROLES:
            roles[0][WAR_ROLES[role.id]] = True

    updated_war_roles = [role for role in added + removed if role.id in WAR_ROLES]
    if len(updated_war_roles) == 0:
        return

    username = member.nick.split(" ")[-1]

    with lock:
        existing_users = sheet.col_values(1)

        last_row = len(existing_users) + 1
        for i, user in enumerate(existing_users):
            if user.lower() == username.lower():
                last_row = i + 1
                break

        sheet.update_acell(f"A{last_row}", username)
        sheet.update(roles, f"C{last_row}:F{last_row}")

        logging.info(f"Updated war roles for {username}: {roles[0]}")
