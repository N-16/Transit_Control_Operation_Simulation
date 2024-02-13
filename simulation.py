from datetime import time, timedelta, datetime, date
from transit_info import *
from stop_info import *
from pax_info import *
from sim_classes import *
import traceback

def get_trip_time(stop_id_from, stop_id_to, capacity):
    times_for_cap = next((item for item in TRANSIT_TRIP_TIME if item['capacity'] == capacity), None)
    if stop_id_from > stop_id_to:
        print("Invalid stops request")
        # Change this if considering simulating return trips as well
    if stop_id_to - stop_id_from == 1:
        link = str(stop_id_from) + '-' + str(stop_id_to)
        return times_for_cap[link]
    else:
        curr_stop_id = stop_id_from
        total_time = timedelta(minutes=0, seconds=0)
        while (curr_stop_id < stop_id_to):
            link = str(curr_stop_id) + '-' + str(curr_stop_id + 1) 
            total_time += times_for_cap[link]
        return total_time

def get_dwell(to_alight_count: int, to_board_count: int):
    # per passenger, 5 seconds for boarding and 3 seconds for alighting. Taken from Mau-Luen Tham et al
    return timedelta(seconds=(to_alight_count * 3) + (to_board_count * 5))

class SimulationEnv:
    def __init__(self, transit_info: list, dispatch_schedule: list, stop_info: list, pax_info: list,start_time: time):
        self.transit = []
        for transit in transit_info:
            self.transit.append(Transit(**transit))
        self.stops = []
        for stop in stop_info:
            self.stops.append(Stop(**stop))
        self.terminal_index = self.stops[-1].index
        self.pax = []
        for pax in pax_info:
            self.pax.append(Passenger(**pax))
        self.time = start_time
        self.event_schedule = [{'time': start_time, 'event': SimulationEvent(1, None, EventType.INIT)}]

        for dispatch in dispatch_schedule:
            transit = next((item for item in self.transit if item.id == dispatch['transit_id']), None)
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DISPATCH)
            self.event_schedule.append({'time': dispatch['time'], 'event': new_event})
    
    def step(self):
        event_schedule_to_exec = self.skip_to_next_event()
        event_type = event_schedule_to_exec['event'].event_type
        transit = event_schedule_to_exec['event'].transit
        if event_type == EventType.INIT:
            print(str(self.time) + ": SIMULATION HAS BEGUN")
            # Add more information like passenger demand, bus schedule etc.
        elif event_type == EventType.DISPATCH:
            print(str(self.time) + ": Dispatching transit " + str(transit.id))
            # Switch transit state to STOP
            transit.last_stop_index = 1
            transit.state = TransitState.STOP
            # Schedule event after Dwell
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DEPART)
            b_count = len(self.board_pax(stop_index=transit.last_stop_index, transit=transit))
            departure_time = (datetime.combine(date.today(), self.time) + get_dwell(to_alight_count=0, to_board_count=b_count)).time() 
            self.event_schedule.append({'time': departure_time, 'event': new_event})
        elif event_type == EventType.DEPART:
            
            # Check if reached trip end
            if transit.last_stop_index == self.terminal_index:
                print(str(self.time) + ": Transit "+ str(transit.id) + " has completed it's trip")
                transit.state = TransitState.SERVED
                # To check if reached all trip finished
                end_sim = True
                for t in self.transit:
                    if t.state != TransitState.SERVED:
                        end_sim = False
                        break
                if end_sim: 
                    self.event_schedule.remove(event_schedule_to_exec)
                    print(str(self.time) + ": SIMULATION IS COMPLETED")
                    return end_sim
            else:
                print(str(self.time) + ": Transit "+ str(transit.id) + " departing from stop " + str(transit.last_stop_index))
                # Switch transit state to MOVING
                transit.state = TransitState.MOVING
                # Schedule event based on arrival time
                new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.STOP)
                arr_time = (datetime.combine(date.today(), self.time) + get_trip_time(transit.last_stop_index, transit.last_stop_index + 1, transit.capacity)).time()
                self.event_schedule.append({'time': arr_time,
                                            'event': new_event})
        elif event_type == EventType.STOP:
            print(str(self.time) + ": Transit "+ str(transit.id) + " reached stop " + str(transit.last_stop_index + 1))
            # Switch transit state to STOP
            transit.state = TransitState.STOP
            transit.last_stop_index += 1
            # Schedule departing event based on dwell time
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DEPART)
            al_count = len(self.alight_pax(stop_index=transit.last_stop_index, transit=transit))
            b_count = len(self.board_pax(stop_index=transit.last_stop_index, transit=transit))
            departure_time = (datetime.combine(date.today(), self.time) + get_dwell(to_alight_count=al_count, to_board_count=b_count)).time()
            self.event_schedule.append({'time': departure_time, 'event': new_event})
        self.event_schedule.remove(event_schedule_to_exec)
        return False
            

    def board_pax(self, stop_index: int, transit: Transit):
        # get available passengers
        av_pax = []
        for p in self.pax:
            #print(self.time, p.arr_time)
            if p.state == PaxState.TO_BOARD and p.arr_time < self.time and p.board_from == stop_index:
                av_pax.append(p)
        #print("Available pax:", av_pax)
        # check transit occupancy
        boarding_pax = av_pax[:transit.capacity - transit.occupancy]
        # update pax state
        for p in boarding_pax:
            p.state = PaxState.ON_BOARD
            p.on_transit_id = transit.id
            print("     '----Passenger " + str(p.id) + " has boarded transit " + str(transit.id))
        # update transit occupancy
        transit.occupancy += len(boarding_pax)
        return boarding_pax

    def alight_pax(self, stop_index: int, transit: Transit):
        # get all boarded passengers, that are traveling in specific transit, with specific destination
        al_pax = []
        for p in self.pax:
            #print(self.time, p.arr_time)
            if p.state == PaxState.ON_BOARD and p.on_transit_id == transit.id and p.alight_to == stop_index:
                al_pax.append(p)
                # update pax state
                p.state = PaxState.ARRIVED
                p.on_transit_id = -1
                print("     '----Passenger " + str(p.id) + " has arrived at it's destination stop: " + str(stop_index))        
        # update transit occupancy
        transit.occupancy -= len(al_pax)
        return al_pax
    
    def skip_to_next_event(self):
        latest_event_schedule = min(self.event_schedule, key=lambda x:x['time'])
        if self.time > latest_event_schedule['time']:
            print("Event time" + str(latest_event_schedule['time']) + " has passed somehow")
            return
        self.time = latest_event_schedule['time']
        return latest_event_schedule
   
    def initialize_transit(self):
        pass

