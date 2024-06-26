from datetime import time, timedelta, datetime, date
from transit_info import *
from stop_info import *
from pax_info import *
from sim_classes import *
import hyper_params
import matplotlib.pyplot as plt
import traceback

def get_trip_time(stop_id_from, stop_id_to, capacity):
    times_for_cap = next((item for item in TRANSIT_TRIP_TIME if item['capacity'] == capacity), None)
    #if stop_id_from > stop_id_to:
        #print("Invalid stops request")
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

class SimData:
    def __init__(self, transit, stops, control) -> None:
        self.time_data = []
        self.unserved_pax_data = []
        self.skip_pattern = {}
        self.total_skip_instances = {}
        self.transit = transit
        self.stops = stops
        self.control = control
        if control:
            for t in transit:
                self.skip_pattern[t.id] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                self.total_skip_instances[t.id] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def register_time_data(self, id, waiting_time, ride_time):
        self.time_data.append({'id':id, 'waiting_time': waiting_time, 'ride_time': ride_time})
    
    def register_unserved_pax_data(self, id, arr_time, board_from):
        self.unserved_pax_data.append({'id':id, 'arr_time': arr_time, 'board_from': board_from})
    
    def register_skip_data(self, t_id, stop_id, skip):
        if skip:
            self.skip_pattern[t_id][stop_id - 1] += 1
        self.total_skip_instances[t_id][stop_id - 1] += 1
     
    def save(self, name=str(datetime.now())):
        with open('sim_run_data/'+name+'_time.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, self.time_data[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(self.time_data)
            print("Average waiting time:", self.get_avg_waiting())
        with open('sim_run_data/'+name+'_unserved.csv', 'w', newline='') as output_file:
            if len(self.unserved_pax_data) == 0:
                dict_writer = csv.DictWriter(output_file, ['no', 'unserved', 'passengers'])
            else:
                print("Unserved passengers:", len(self.unserved_pax_data))
                dict_writer = csv.DictWriter(output_file, self.unserved_pax_data[0].keys())
                dict_writer.writeheader()
                dict_writer.writerows(self.unserved_pax_data)
        if self.control: 
            with open('sim_run_data/'+name+'_skipping_pattern.csv', 'w', newline='') as output_file:
                stops = []
                for s in self.stops:
                    stops.append('stop_' + str(s.index))
                dict_writer = csv.DictWriter(output_file, ['transit_id', *stops])
                dict_writer.writeheader()
                skipping_data = []
                for t in self.transit:
                    t_stops = {} 
                    for s in self.stops:
                        t_stops['stop_'+str(s.index)] = self.skip_pattern[t.id][s.index - 1] / self.total_skip_instances[t.id][s.index - 1]
                    skipping_data.append({'transit_id':t.id, **t_stops})
                dict_writer.writerows(skipping_data)

            

    def get_avg_waiting(self):
        times = [d['waiting_time'] for d in self.time_data]
        return sum(times) / len(times)

class SimulationEnv:
    def __init__(self, transit_info: list, dispatch_schedule: list, stop_info: list
                 , pax_info: list,start_time: time, end_time: time, log_file, 
                 load_models = False, save_models=True, control_op = True, save_data = False):
        self.transit_info = transit_info
        self.dispatch_schedule = dispatch_schedule
        self.stop_info = stop_info
        self.pax_info = pax_info
        self.start_time = start_time
        self.transit = []
        for transit in transit_info:
            t = RLTransit(**transit)
            if load_models:
                t.load_models('transit_'+str(t.id))
            self.transit.append(t)

        self.stops = []
        for stop in stop_info:
            self.stops.append(Stop(**stop))
        self.terminal_index = self.stops[0].index
        self.pax = []
        for pax in pax_info:
            self.pax.append(Passenger(**pax))
        self.time = start_time
        self.event_schedule = [{'time': start_time, 'event': SimulationEvent(1, None, EventType.INIT)}]
        self.end_time = end_time
        self.log_file = log_file
        for dispatch in dispatch_schedule:
            transit = next((item for item in self.transit if item.id == dispatch['transit_id']), None)
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DISPATCH)
            self.event_schedule.append({'time': dispatch['time'], 'event': new_event})
        self.save_models = save_models
        self.control_op = control_op
        self.save_data = save_data
        self.sim_data = SimData(self.transit, self.stops, control_op)
        self.hourly_intervals = []
        temp_time = start_time
        while temp_time < self.end_time:
            temp_time = util.add_time(temp_time, timedelta(hours=1))
            self.hourly_intervals.append(temp_time)
        self.hourly_intervals.append(time(23,59,59))
        self.current_interval = 0
    
    def reset(self):

        for transit in self.transit:
            transit.reset()
        self.stops = []
        for stop in self.stop_info:
            self.stops.append(Stop(**stop))
        self.terminal_index = self.stops[0].index
        self.pax = []
        self.pax_info = generate_pax_demand()
        for pax in self.pax_info:
            self.pax.append(Passenger(**pax))
        self.time = self.start_time
        self.event_schedule = [{'time': self.start_time, 'event': SimulationEvent(1, None, EventType.INIT)}]
        for dispatch in self.dispatch_schedule:
            transit = next((item for item in self.transit if item.id == dispatch['transit_id']), None)
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DISPATCH)
            self.event_schedule.append({'time': dispatch['time'], 'event': new_event})
        self.sim_data= SimData(self.transit, self.stops, self.control_op)
        self.current_interval = 0
    
    def step(self, epsilon= 0.0, learn=True, hourly_notice=True):
        event_schedule_to_exec = self.skip_to_next_event()
        event_type = event_schedule_to_exec['event'].event_type
        transit = event_schedule_to_exec['event'].transit
        reward = 0
        if event_type == EventType.INIT:
            print(str(self.time) + ": SIMULATION HAS BEGUN", file=self.log_file)
            # Add more information like passenger demand, bus schedule etc.
        elif event_type == EventType.DISPATCH:
            print(str(self.time) + ": Dispatching transit " + str(transit.id), file=self.log_file)
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
            if transit.last_stop_index == self.terminal_index and self.time > self.end_time:
                print(str(self.time) + ": Transit "+ str(transit.id) +
                       " has completed it's trip", file=self.log_file)
                transit.store_terminal_transition(self.get_state(transit))
                if self.save_models:
                    transit.save_models('transit_'+str(transit.id))
                transit.state = TransitState.SERVED
                # To check if reached all trip finished
                end_sim = True
                for t in self.transit:
                    if t.state != TransitState.SERVED:
                        end_sim = False
                        break
                if end_sim: 
                    self.event_schedule.remove(event_schedule_to_exec)
                    print(str(self.time) + ": SIMULATION IS COMPLETED", file=self.log_file)
                    
                    served = 0
                    on_board = 0
                    for p in self.pax:
                        if p.state == PaxState.ARRIVED:
                            served += 1
                        elif p.state == PaxState.ON_BOARD:
                            on_board += 1
                        else: #to_board
                            self.sim_data.register_unserved_pax_data(p.id, p.arr_time, p.board_from)
                    print("Served " + str(served) + ' out of ' + str(len(self.pax)), file=self.log_file)
                    #reward -= (len(self.pax) - served) * 1000
                    print(str(on_board) + ' passengers are still on board', file=self.log_file)
                    if self.save_data:
                        self.sim_data.save(name=str(datetime.now()))
                    if hourly_notice:
                        return True, reward, True
                    else:
                        return True, reward 
            
            else:
                print(str(self.time) + ": Transit "+ str(transit.id) + " departing from stop " + str(transit.last_stop_index), file=self.log_file)
                # Switch transit state to MOVING
                transit.state = TransitState.MOVING
                # Schedule event based on arrival time
                new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.STOP)
                arr_time = (datetime.combine(date.today(), self.time) + get_trip_time(transit.last_stop_index, (transit.last_stop_index % len(self.stops))+ 1, transit.capacity)).time()
                self.event_schedule.append({'time': arr_time,
                                            'event': new_event})
        elif event_type == EventType.STOP:
            # request skip control operation
            state = self.get_state(transit)
            print("State = " + str(state), file=self.log_file)
            skip = False
            operate = True
            for t in self.transit:
                if t.state == TransitState.TO_DISPATCH or t.state == TransitState.SERVED:
                    operate = False
                    break
            upcoming_stop = (transit.last_stop_index % len(self.stops)) + 1
            stop_index = None
            for s in range(0,len(self.stops)):
                if upcoming_stop == self.stops[s].index:
                    stop_index = s
                    break

            if self.stops[stop_index].skipped_last :
                print("Skipping control operation restricted", file=self.log_file)
                operate = False
                self.stops[stop_index].skipped_last = False
            
            if (self.time > self.end_time and upcoming_stop == self.terminal_index):
                operate = False

            boarding_pax, av_pax = self.board_pax(stop_index=(transit.last_stop_index % len(self.stops)) + 1, transit=transit, update=False)        
            
            if transit.controllable and operate and self.control_op:
                skip = transit.get_action(list(state), learn=learn)
                transit.last_action = skip
                transit.last_reward = self.get_boarding_reward(boarding_pax, av_pax, skip, transit)
                reward += transit.last_reward
                
                

            # Switch transit state to STOP
            transit.state = TransitState.STOP
            transit.last_stop_index = (transit.last_stop_index % len(self.stops)) + 1
            self.sim_data.register_skip_data(transit.id, transit.last_stop_index, skip)
            print(str(self.time) + ": Transit "+ str(transit.id) + " reached stop " + str((transit.last_stop_index)), file=self.log_file)
            if skip:
                self.stops[stop_index].skipped_last = True
                print("Transit " + str(transit.id) + " is not boarding at stop " + str(transit.last_stop_index), file=self.log_file)
            # Schedule departing event based on dwell time
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DEPART)
            al_pax, total_travel_time = self.alight_pax(stop_index=transit.last_stop_index, transit=transit)
            al_count = len(al_pax)
            #reward -= total_travel_time
            #transit.last_reward = -total_travel_time
            b_count = 0 if skip or (self.time > self.end_time and transit.last_stop_index == self.terminal_index)\
                        else len(boarding_pax)
            transit.occupancy += b_count
            departure_time = (datetime.combine(date.today(), self.time) + get_dwell(to_alight_count=al_count, to_board_count=b_count)).time()
            self.event_schedule.append({'time': departure_time, 'event': new_event})
        self.event_schedule.remove(event_schedule_to_exec)
        if hourly_notice:
            notice = False
            if self.time > self.hourly_intervals[self.current_interval]:
                print(" Time: ", self.time)
                notice = True
                self.current_interval = min(1 + self.current_interval, len(self.hourly_intervals) - 1)
            return False, reward, notice
            

    def board_pax(self, stop_index: int, transit: Transit, update=True):
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
            p.boarding_transit_time = self.time
            print("     '----Passenger " + str(p.id) + " has boarded transit " + str(transit.id), file=self.log_file)
        # update transit occupancy
        if update:
            transit.occupancy += len(boarding_pax)
        return boarding_pax, av_pax
    
    def get_boarding_reward(self, boarding_pax, waiting_pax, skip, transit, weight=3):
        state = self.get_state(transit)
        headway = state[1] + 1
        # reward = -(waiting time for all boarding pax + headway * weight * passengers that cannot be boarded)
        sum_of_waiting_boarding_pax = 0
        for p in boarding_pax:
            sum_of_waiting_boarding_pax += util.time_diff(p.boarding_transit_time, p.arr_time).total_seconds()/60
        reward =  -(sum_of_waiting_boarding_pax + (weight *  (len(waiting_pax) - len(boarding_pax)) * headway))
        #reward =  -(sum_of_waiting_boarding_pax)
        if skip:
            #reward -= headway  * weight * (boarding_pax)
            reward -= weight * headway * (len(boarding_pax))
        return reward
    
    def alight_pax(self, stop_index: int, transit: Transit):
        # get all boarded passengers, that are traveling in specific transit, with specific destination
        total_time_to_reach = 0
        al_pax = []
        for p in self.pax:
            #print(self.time, p.arr_time)
            if p.state == PaxState.ON_BOARD and p.on_transit_id == transit.id and p.alight_to == stop_index:
                al_pax.append(p)
                # update pax state
                p.state = PaxState.ARRIVED
                p.on_transit_id = -1
                self.sim_data.register_time_data(p.id, util.time_diff(p.boarding_transit_time, p.arr_time).total_seconds()/60,
                                        util.time_diff(self.time, p.boarding_transit_time).total_seconds()/60)
                time_to_reach = util.time_diff(self.time, p.arr_time).total_seconds()/60
                total_time_to_reach += time_to_reach
                print("     '----Passenger " + str(p.id) + " from " + str(p.board_from) + " has arrived at it's destination stop " + str(stop_index) + " in "+ str(time_to_reach)+ " minutes", file=self.log_file) 
        # update transit occupancy
        transit.occupancy -= len(al_pax)
        return al_pax, total_time_to_reach
    def skip_to_next_event(self):
        latest_event_schedule = min(self.event_schedule, key=lambda x:x['time'])
        if self.time > latest_event_schedule['time']:
            print("Event time " + str(latest_event_schedule['time']) + " has passed somehow")
            print("current time:", self.time)
            print("Event: ", latest_event_schedule)
            return 
        self.time = latest_event_schedule['time']
        return latest_event_schedule
   
    def initialize_transit(self):
        pass

    def get_state(self, focus_transit):
        transit_loc_capacity = []
        for t in self.transit:
            if t.id != focus_transit.id:
                transit_loc_capacity.append({'id': t.id, 'last_stop_index': t.last_stop_index,
                                              'normalized occupancy': t.occupancy / t.capacity,
                                                'occupancy': t.occupancy, 'capacity': t.capacity})
        # Forward headway of 2 upcoming transits
        transit_loc_capacity = sorted(transit_loc_capacity, key=lambda d: d['last_stop_index'])
        #print(transit_loc_capacity, file=self.log_file)
        index = 0
        for loc in transit_loc_capacity:
            if loc['last_stop_index'] > focus_transit.last_stop_index:
                break
            index += 1
        transit_z = transit_loc_capacity[index - 1]
        transit_y = transit_loc_capacity[index - 2]
        if focus_transit.last_stop_index >= transit_z['last_stop_index']:
            h_z = focus_transit.last_stop_index - transit_z['last_stop_index']      
        else:
            h_z = focus_transit.last_stop_index + len(self.stops) - transit_z['last_stop_index']
        if focus_transit.last_stop_index >= transit_y['last_stop_index']:
            h_y = focus_transit.last_stop_index - transit_y['last_stop_index']
        else:
            h_y = focus_transit.last_stop_index + len(self.stops) - transit_y['last_stop_index']


        occ_z = transit_z['normalized occupancy']
        occ_y = transit_y['normalized occupancy']
        free_a = focus_transit.capacity - focus_transit.occupancy
        free_z = transit_z['capacity'] - transit_z['occupancy']
        free_y = transit_y['capacity'] - transit_y['occupancy']
        #print("free_Z=",free_z)
        cap_z = transit_z['capacity']
        cap_y = transit_y['capacity']
        
        # Passenger demand at all stops starting from current stop
        pax_demand = {}
        for s in self.stops:
            pax_demand[s.index] = 0
        for p in self.pax:
            if p.state == PaxState.TO_BOARD and p.arr_time < self.time:
                pax_demand[p.board_from] += 1
        pd = []
        for i in range(focus_transit.last_stop_index, len(pax_demand) + 1):
            pd.append(pax_demand[i])
        for i in range(1, focus_transit.last_stop_index):
            pd.append(pax_demand[i])
        return int(free_a), h_z, int(free_z), h_y, int(free_y), *pd
    
class SingleAgentSimEnv(SimulationEnv):
    def __init__(self, transit_info: list, dispatch_schedule: list, stop_info: list,
                pax_info: list, start_time: time, end_time: time, log_file,
                load_models=False, save_models=True, control_op=True, save_data=False):
        self.transit_info = transit_info
        self.dispatch_schedule = dispatch_schedule
        self.stop_info = stop_info
        self.pax_info = pax_info
        self.start_time = start_time
        self.transit = []
        for transit in transit_info:
            t = RLTransit(**transit)
            self.transit.append(t)
        self.agent = Agent(**hyper_params.single_agent_para)
        if load_models:
            self.agent.load_models()
        self.stops = []
        for stop in stop_info:
            self.stops.append(Stop(**stop))
        self.terminal_index = self.stops[0].index
        self.pax = []
        for pax in pax_info:
            self.pax.append(Passenger(**pax))
        self.time = start_time
        self.event_schedule = [{'time': start_time, 'event': SimulationEvent(1, None, EventType.INIT)}]
        self.end_time = end_time
        self.log_file = log_file
        for dispatch in dispatch_schedule:
            transit = next((item for item in self.transit if item.id == dispatch['transit_id']), None)
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DISPATCH)
            self.event_schedule.append({'time': dispatch['time'], 'event': new_event})
        self.save_models = save_models
        self.control_op = control_op
        self.save_data = save_data
        self.sim_data = SimData()

    def reset(self):
        self.agent.reset()
        for transit in self.transit:
            transit.reset()
        self.stops = []
        for stop in self.stop_info:
            self.stops.append(Stop(**stop))
        self.terminal_index = self.stops[0].index
        self.pax = []
        self.pax_info = generate_pax_demand()
        for pax in self.pax_info:
            self.pax.append(Passenger(**pax))
        self.time = self.start_time
        self.event_schedule = [{'time': self.start_time, 'event': SimulationEvent(1, None, EventType.INIT)}]
        for dispatch in self.dispatch_schedule:
            transit = next((item for item in self.transit if item.id == dispatch['transit_id']), None)
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DISPATCH)
            self.event_schedule.append({'time': dispatch['time'], 'event': new_event})
        self.sim_data=SimData()
    
    def step(self, epsilon= 0.0, learn=True):
        event_schedule_to_exec = self.skip_to_next_event()
        event_type = event_schedule_to_exec['event'].event_type
        transit = event_schedule_to_exec['event'].transit
        reward = 0
        if event_type == EventType.INIT:
            print(str(self.time) + ": SIMULATION HAS BEGUN", file=self.log_file)
            # Add more information like passenger demand, bus schedule etc.
        elif event_type == EventType.DISPATCH:
            print(str(self.time) + ": Dispatching transit " + str(transit.id), file=self.log_file)
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
            if transit.last_stop_index == self.terminal_index and self.time > self.end_time:
                print(str(self.time) + ": Transit "+ str(transit.id) +
                       " has completed it's trip", file=self.log_file)
                transit.state = TransitState.SERVED
                # To check if reached all trip finished
                end_sim = True
                for t in self.transit:
                    if t.state != TransitState.SERVED:
                        end_sim = False
                        break
                if end_sim: 
                    self.event_schedule.remove(event_schedule_to_exec)
                    print(str(self.time) + ": SIMULATION IS COMPLETED", file=self.log_file)
                    served = 0
                    on_board = 0
                    for p in self.pax:
                        if p.state == PaxState.ARRIVED:
                            served += 1
                        elif p.state == PaxState.ON_BOARD:
                            on_board += 1
                        else: #to_board
                            self.sim_data.register_unserved_pax_data(p.id, p.arr_time, p.board_from)
                    print("Served " + str(served) + ' out of ' + str(len(self.pax)), file=self.log_file)
                    self.agent.last_reward -= (len(self.pax) - served) * 500
                    self.agent.store_terminal_transition(self.get_state(transit))
                    if self.save_models:
                        self.agent.save_models()
                    reward -= (len(self.pax) - served) * 500
                    print(str(on_board) + ' passengers are still on board', file=self.log_file)
                    if self.save_data:
                        self.sim_data.save(name=str(datetime.now()))
                    return True, reward
            
            else:
                print(str(self.time) + ": Transit "+ str(transit.id) + " departing from stop " + str(transit.last_stop_index), file=self.log_file)
                # Switch transit state to MOVING
                transit.state = TransitState.MOVING
                # Schedule event based on arrival time
                new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.STOP)
                arr_time = (datetime.combine(date.today(), self.time) + get_trip_time(transit.last_stop_index, (transit.last_stop_index % len(self.stops))+ 1, transit.capacity)).time()
                self.event_schedule.append({'time': arr_time,
                                            'event': new_event})
        elif event_type == EventType.STOP:
            # request skip control operation
            state = self.get_state(transit)
            print("State = " + str(state), file=self.log_file)
            skip = False
            operate = True
            for t in self.transit:
                if t.state == TransitState.TO_DISPATCH or t.state == TransitState.SERVED:
                    operate = False
                    break
            if (self.time > self.end_time and transit.last_stop_index == self.terminal_index):
                operate = False
            upcoming_stop = (transit.last_stop_index % len(self.stops)) + 1
            stop_index = None
            for s in range(0,len(self.stops)):
                if upcoming_stop == self.stops[s].index:
                    stop_index = s
                    break

            if self.stops[stop_index].skipped_last:
                print("Skipping control operation restricted", file=self.log_file)
                operate = False
                self.stops[stop_index].skipped_last = False
                    
            if transit.controllable and operate and self.control_op:
                skip = self.agent.get_action(list(state), learn=learn)
                self.agent.last_action = skip

            # Switch transit state to STOP
            transit.state = TransitState.STOP
            transit.last_stop_index = (transit.last_stop_index % len(self.stops)) + 1
            print(str(self.time) + ": Transit "+ str(transit.id) + " reached stop " + str((transit.last_stop_index)), file=self.log_file)
            if skip:
                self.stops[stop_index].skipped_last = True
                print("Transit " + str(transit.id) + " is not boarding at stop " + str(transit.last_stop_index), file=self.log_file)
            # Schedule departing event based on dwell time
            new_event = SimulationEvent(self.event_schedule[-1]['event'].id + 1, transit, EventType.DEPART)
            al_pax, _ = self.alight_pax(stop_index=transit.last_stop_index, transit=transit)
            al_count = len(al_pax)
            total_waiting_time = 0
            if skip or (self.time > self.end_time and transit.last_stop_index == self.terminal_index):
                b_count = 0 
            else:
                boarding, total_waiting_time = self.board_pax(stop_index=transit.last_stop_index, transit=transit)
                b_count = len(boarding)
            self.agent.last_reward = -total_waiting_time
            reward -= total_waiting_time
            departure_time = (datetime.combine(date.today(), self.time) + get_dwell(to_alight_count=al_count, to_board_count=b_count)).time()
            self.event_schedule.append({'time': departure_time, 'event': new_event})
        self.event_schedule.remove(event_schedule_to_exec)
        return False, reward
            

    def board_pax(self, stop_index: int, transit: Transit):
        # get available passengers
        av_pax = []
        total_waiting_time = 0
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
            p.boarding_transit_time = self.time
            total_waiting_time += util.time_diff(self.time, p.arr_time).total_seconds()/60
            print("     '----Passenger " + str(p.id) + " has boarded transit " + str(transit.id), file=self.log_file)
        # update transit occupancy
        transit.occupancy += len(boarding_pax)
        return boarding_pax, total_waiting_time

    def alight_pax(self, stop_index: int, transit: Transit):
        # get all boarded passengers, that are traveling in specific transit, with specific destination
        total_time_to_reach = 0
        al_pax = []
        for p in self.pax:
            #print(self.time, p.arr_time)
            if p.state == PaxState.ON_BOARD and p.on_transit_id == transit.id and p.alight_to == stop_index:
                al_pax.append(p)
                # update pax state
                p.state = PaxState.ARRIVED
                p.on_transit_id = -1
                self.sim_data.register_time_data(p.id, util.time_diff(p.boarding_transit_time, p.arr_time).total_seconds()/60,
                                        util.time_diff(self.time, p.boarding_transit_time).total_seconds()/60)
                time_to_reach = util.time_diff(self.time, p.arr_time).total_seconds()/60
                print("     '----Passenger " + str(p.id) + " from " + str(p.board_from) + " has arrived at it's destination stop " + str(stop_index) + " in "+ str(time_to_reach)+ " minutes", file=self.log_file) 
        # update transit occupancy
        transit.occupancy -= len(al_pax)
        return al_pax, total_time_to_reach
    def skip_to_next_event(self):
        latest_event_schedule = min(self.event_schedule, key=lambda x:x['time'])
        if self.time > latest_event_schedule['time']:
            print("Event time " + str(latest_event_schedule['time']) + " has passed somehow")
            print("current time:", self.time)
            print("Event: ", latest_event_schedule)
            return 
        self.time = latest_event_schedule['time']
        return latest_event_schedule
   
    def initialize_transit(self):
        pass

    def get_state(self, focus_transit):
        transit_loc_capacity = []
        for t in self.transit:
            if t.id != focus_transit.id:
                transit_loc_capacity.append({'id': t.id, 'last_stop_index': t.last_stop_index,
                                              'normalized occupancy': t.occupancy / t.capacity,
                                                'occupancy': t.occupancy, 'capacity': t.capacity})
        # Forward headway of 2 upcoming transits
        transit_loc_capacity = sorted(transit_loc_capacity, key=lambda d: d['last_stop_index'])
        #print(transit_loc_capacity, file=self.log_file)
        index = 0
        for loc in transit_loc_capacity:
            if loc['last_stop_index'] > focus_transit.last_stop_index:
                break
            index += 1
        transit_z = transit_loc_capacity[index - 1]
        transit_y = transit_loc_capacity[index - 2]
        if focus_transit.last_stop_index >= transit_z['last_stop_index']:
            h_z = focus_transit.last_stop_index - transit_z['last_stop_index']      
        else:
            h_z = focus_transit.last_stop_index + len(self.stops) - transit_z['last_stop_index']
        if focus_transit.last_stop_index >= transit_y['last_stop_index']:
            h_y = focus_transit.last_stop_index - transit_y['last_stop_index']
        else:
            h_y = focus_transit.last_stop_index + len(self.stops) - transit_y['last_stop_index']


        occ_z = transit_z['normalized occupancy']
        occ_y = transit_y['normalized occupancy']
        free_a = focus_transit.capacity - focus_transit.occupancy
        free_z = transit_z['capacity'] - transit_z['occupancy']
        free_y = transit_y['capacity'] - transit_y['occupancy']
        #print("free_Z=",free_z)
        cap_z = transit_z['capacity']
        cap_y = transit_y['capacity']
        
        # Passenger demand at all stops starting from current stop
        pax_demand = {}
        for s in self.stops:
            pax_demand[s.index] = 0
        for p in self.pax:
            if p.state == PaxState.TO_BOARD and p.arr_time < self.time:
                pax_demand[p.board_from] += 1
        pd = []
        for i in range(focus_transit.last_stop_index, len(pax_demand) + 1):
            pd.append(pax_demand[i])
        for i in range(1, focus_transit.last_stop_index):
            pd.append(pax_demand[i])
        return int(free_a), h_z, int(free_z), h_y, int(free_y), *pd

       


