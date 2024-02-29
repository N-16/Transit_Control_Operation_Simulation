from datetime import datetime, time, timedelta, date

def add_time(t, t_delta):
    return (datetime.combine(date.today(), t) + t_delta).time()

def time_diff(t1, t2):
    return (datetime.combine(date.today(), t1) - datetime.combine(date.today(), t2))