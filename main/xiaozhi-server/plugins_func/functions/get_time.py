from datetime import datetime
import cnlunar
from plugins_func.register import register_function, ToolType, ActionResponse, Action

# Add weekday mapping dictionary
WEEKDAY_MAP = {
    "Monday": "Monday",
    "Tuesday": "Tuesday",
    "Wednesday": "Wednesday",
    "Thursday": "Thursday",
    "Friday": "Friday",
    "Saturday": "Saturday",
    "Sunday": "Sunday",
}

get_time_function_desc = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get today's date or current time information",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

@register_function("get_time", get_time_function_desc, ToolType.WAIT)
def get_time():
    """
    Get current date and time information
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    current_weekday = WEEKDAY_MAP[now.strftime("%A")]
    
    response_text = (
        f"Current date: {current_date}, current time: {current_time}, {current_weekday}"
    )
    
    return ActionResponse(Action.REQLLM, response_text, None)

get_lunar_function_desc = {
    "type": "function",
    "function": {
        "name": "get_lunar",
        "description": (
            "Used to get today's lunar calendar and almanac information. "
            "Users can specify query content, such as: lunar date, heavenly stems and earthly branches, solar terms, zodiac, constellation, eight characters, appropriate and taboo activities, etc. "
            "If no query content is specified, defaults to querying stem-branch year and lunar date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Content to query, e.g., lunar date, heavenly stems and earthly branches, festivals, solar terms, zodiac, constellation, eight characters, appropriate and taboo activities, etc",
                }
            },
            "required": [],
        },
    },
}

@register_function("get_lunar", get_lunar_function_desc, ToolType.WAIT)
def get_lunar(query=None):
    """
    Used to get current lunar calendar, heavenly stems and earthly branches, solar terms, zodiac, constellation, eight characters, appropriate and taboo activities and other almanac information
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%Y-%m-%d")
    current_weekday = WEEKDAY_MAP[now.strftime("%A")]
    
    # If query is None, use default text
    if query is None:
        query = "Default query for stem-branch year and lunar date"
    
    response_text = f"Based on the following information, respond to user's query request and provide information related to {query}:\n"
    
    lunar = cnlunar.Lunar(now, godType="8char")
    response_text += (
        f"Current Gregorian date: {current_date}, current time: {current_time}, {current_weekday}\n"
        "Lunar information:\n"
        "%s year %s%s\n" % (lunar.lunarYearCn, lunar.lunarMonthCn[:-1], lunar.lunarDayCn)
        + "Stems and branches: %s year %s month %s day\n" % (lunar.year8Char, lunar.month8Char, lunar.day8Char)
        + "Zodiac: %s\n" % (lunar.chineseYearZodiac)
        + "Eight characters: %s\n"
        % (
            " ".join(
                [lunar.year8Char, lunar.month8Char, lunar.day8Char, lunar.twohour8Char]
            )
        )
        + "Today's festivals: %s\n"
        % (
            ",".join(
                filter(
                    None,
                    [
                        *lunar.get_legalHolidays(),
                        *lunar.get_otherHolidays(),
                        *lunar.get_otherLunarHolidays(),
                    ],
                )
            )
        )
        + "Today's solar term: %s\n" % (lunar.todaySolarTerms)
        + "Next solar term: %s %s year %s month %s day\n"
        % (
            lunar.nextSolarTerm,
            lunar.nextSolarTermYear,
            lunar.nextSolarTermDate[0],
            lunar.nextSolarTermDate[1],
        )
        + "This year's solar term table: %s\n"
        % (
            ", ".join(
                [
                    f"{term}({date[0]}月{date[1]}日)"
                    for term, date in lunar.thisYearSolarTermsDic.items()
                ]
            )
        )
        + "Zodiac conflict: %s\n" % (lunar.chineseZodiacClash)
        + "Constellation: %s\n" % (lunar.starZodiac)
        + "Nayin: %s\n" % lunar.get_nayin()
        + "Peng Zu taboos: %s\n" % (lunar.get_pengTaboo(delimit=", "))
        + "Day officer: %s position\n" % lunar.get_today12DayOfficer()[0]
        + "Deity on duty: %s(%s)\n"
        % (lunar.get_today12DayOfficer()[1], lunar.get_today12DayOfficer()[2])
        + "28 constellations: %s\n" % lunar.get_the28Stars()
        + "Lucky gods direction: %s\n" % " ".join(lunar.get_luckyGodsDirection())
        + "Today's fetal god: %s\n" % lunar.get_fetalGod()
        + "Appropriate: %s\n" % "、".join(lunar.goodThing[:10])
        + "Taboo: %s\n" % "、".join(lunar.badThing[:10])
        + "(Default returns stem-branch year and lunar date; only returns today's appropriate and taboo activities when specifically requested for such information)"
    )
    
    return ActionResponse(Action.REQLLM, response_text, None)
