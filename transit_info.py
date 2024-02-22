from datetime import time, timedelta

TRANSIT_INFO = [{'id':1,'capacity':40},
                {'id':2, 'capacity':40}]

TRANSIT_SCHEDULE = [{'transit_id':1, 'time':time(7,0,0)},
                    {'transit_id':2, 'time':time(7,5,0)}]

TRANSIT_TRIP_TIME = [{'capacity': 40,
                    '1-2': timedelta(minutes=3, seconds=25),
                    '2-3': timedelta(minutes=3),
                    '3-4': timedelta(minutes=3),
                    '4-5': timedelta(minutes=3),
                    '5-6': timedelta(minutes=3),
                    '6-7': timedelta(minutes=3),
                    '7-8': timedelta(minutes=3),
                    '8-9': timedelta(minutes=3),
                    '9-10': timedelta(minutes=3),
                    '10-11': timedelta(minutes=3),
                    '11-12': timedelta(minutes=3),
                    '12-13': timedelta(minutes=3),
                    '13-14': timedelta(minutes=3),
                    '14-15': timedelta(minutes=3),
                    '15-16': timedelta(minutes=3),
                    '16-17': timedelta(minutes=3),
                    '17-18': timedelta(minutes=3),
                    '18-1': timedelta(minutes=3)}]