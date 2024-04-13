from datetime import datetime

time_units_map = {
    "s": "seconds",
    "sec": "seconds",
    "secs": "seconds",
    "second": "seconds",
    "seconds": "seconds",

    "m": "minutes",
    "min": "minutes",
    "mins": "minutes",
    "minute": "minutes",
    "minutes": "minutes",

    "h": "hours",
    "hr": "hours",
    "hrs": "hours",
    "hour": "hours",
    "hours": "hours",

    "d": "days",
    "day": "days",
    "days": "days",

    "w": "weeks",
    "week": "weeks",
    "weeks": "weeks",

    "M": "months",
    "mon": "months",
    "month": "months",
    "months": "months",

    "y": "years",
    "yr": "years",
    "yrs": "years",
    "year": "years",
    "years": "years",
}


def _parse_date(date_str: str) -> datetime:
    date_str.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
    return datetime.strptime(date_str, "%B %d, %Y")


seasons = [(_parse_date(d1), _parse_date(d1)) for d1, d2 in [
    # https://wynncraft.wiki.gg/wiki/Guild_Seasons
    ("July 5th, 2021", "July 7th, 2021"),  # 0
    ("July 9th, 2021", "September 20th, 2021"),  # 1
    ("September 24th, 2021", "November 8th, 2021"),  # 2
    ("November 12th, 2021", "December 23rd, 2021"),  # 3
    ("December 27th, 2021", "February 28th, 2022"),  # 4
    ("March 3rd, 2022", "May 2nd, 2022"),  # 5
    ("May 6th, 2022", "July 4th, 2022"),  # 6
    ("July 8th, 2022", "August 22th, 2022"),  # 7
    ("September 12th, 2022", "October 24th, 2022"),  # 8
    ("October 28th, 2022", "December 23rd, 2022"),  # 9
    ("December 26th, 2022", "February 20th, 2023"),  # 10
    ("February 24th, 2023", "April 8th, 2023"),  # 11
    ("April 14th, 2023", "June 11th, 2023"),  # 12
    ("June 16th, 2023", "August 20th, 2023"),  # 13
    ("August 25th, 2023", "October 29th, 2023"),  # 14
    ("November 3rd, 2023", "December 23rd, 2023"),  # 15
    ("January 5th, 2024", "February 19th, 2024"),  # 16
    ("February 23rd, 2024", "April 22nd, 2024"),  # 17
]]
