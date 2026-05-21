from datetime import datetime
from zoneinfo import ZoneInfo

# fuso de lisboa para horarios e etas
LISBON_TZ = ZoneInfo("Europe/Lisbon")

def gtfs_time_to_seconds(time_value: str) -> int:
    #gtfs permite horas mas tipo 25:30:00, por isso nao uamos datetime.time
    hh, mm, ss = map(int, time_value.split(":"))
    return hh * 3600 + mm * 60 + ss

# volta segundos para formato hh:mm:ss do gtfs
def seconds_to_gtfs_time(total_seconds: int) -> str:
    if total_seconds < 0:
        total_seconds = 0
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"

# hora atual em segundos desde meia noite
def now_local_seconds() -> int:
    now = datetime.now(LISBON_TZ)
    return now.hour * 3600 + now.minute * 60 + now.second

def minutes_until(target_seconds: int, now_seconds: int) -> int:
    delta = target_seconds - now_seconds
    if delta <= 0:
        return 0
    # arredonda por excesso para ETA mais intuitivo
    return (delta + 59) // 60