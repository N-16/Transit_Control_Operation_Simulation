from datetime import time, timedelta

TRANSIT_INFO = [{'id':1,'capacity':100, 'controllable':True},
                {'id':2, 'capacity':100, 'controllable':True},
                {'id':3, 'capacity':100, 'controllable':True},
                {'id':4, 'capacity':100, 'controllable':True},
                {'id':5, 'capacity':100, 'controllable':True},
                {'id':6, 'capacity':100, 'controllable':True}]

TRANSIT_SCHEDULE = [{'transit_id':1, 'time':time(6,30,0)},
                    {'transit_id':2, 'time':time(6,40,0)},
                    {'transit_id':3, 'time':time(6,50,0)},
                    {'transit_id':4, 'time':time(7,0,0)},
                    {'transit_id':5, 'time':time(7,10,0)},
                    {'transit_id':6, 'time':time(7,20,0)}]

TRANSIT_TRIP_TIME = [{'capacity': 100,
                    '1-2': timedelta(minutes=3),
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