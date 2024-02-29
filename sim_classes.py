from enum import Enum
from datetime import time
import random
class TransitState(Enum):
    TO_DISPATCH = 1
    STOP = 2
    MOVING = 3
    SERVED = 5

class EventType(Enum):
    INIT = 1
    DISPATCH = 2
    STOP = 3
    DEPART = 4

class PaxState(Enum):
    TO_BOARD = 1
    ON_BOARD = 2
    ARRIVED = 3
    
class Transit:
    def __init__(self, id: int, capacity: int, controllable = False):
        self.capacity = capacity
        self.state = TransitState.TO_DISPATCH 
        self.id = id
        self.last_stop_index = 0
        self.occupancy = 0
        self.controllable = controllable
    def get_action(self):
        if random.uniform(0, 1) > 0.75:
            return True
        return False
    
class RLTransit(Transit):
    def __init__(self, id: int, capacity: int, controllable=False):
        super().__init__(id, capacity, controllable)

    
    def get_skip_action(self, transit_loc_capacity: list, pax_demand: list):
        pass
         


        

class Stop:
    def __init__(self, index: int):
        self.index = index

class Passenger:
    def __init__(self, id: int, board_from: int, alight_to: int, arr_time: time):
        self.id = id
        self.board_from = board_from
        self.alight_to = alight_to
        self.arr_time = arr_time
        self.state = PaxState.TO_BOARD
        self.on_transit_id = -1

class SimulationEvent:
    def __init__(self, id: int, transit: Transit, event_type: EventType):
        self.id = id
        self.transit = transit
        self.event_type = event_type

    '''def execute(self) -> list:
        pass
    

class DispatchEvent(SimulationEvent):
    def __init__(self, id: int, transit: Transit, event_type: EventType):
        super().__init__(id, transit, event_type)
    
    def execute(self) -> list:
        events_to_schedule = []'''
        

        


