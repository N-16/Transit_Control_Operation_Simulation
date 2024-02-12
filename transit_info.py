from datetime import time, timedelta

TRANSIT_INFO = [{'id':1,'capacity':40},
                {'id':2, 'capacity':40}]

TRANSIT_SCHEDULE = [{'transit_id':1, 'time':time(7,0,0)},
                    {'transit_id':2, 'time':time(7,5,0)}]

TRANSIT_TRIP_TIME = [{'capacity': 40, '1-2': timedelta(minutes=4, seconds=25), '2-3': timedelta(minutes=7)}]