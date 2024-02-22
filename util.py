from datetime import datetime, time, timedelta, date

def add_time(t, t_delta):
    return (datetime.combine(date.today(), t) + t_delta).time()