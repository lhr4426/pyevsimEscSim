from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from NPCModel import MovingDirection
import os
import json
import copy
class ResultViewer(BehaviorModelExecutor) :
    '''
    json 파싱해서 움직임을 그대로 재현
    '''

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size, agent_count) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("PrintMap", 1)
        self.insert_state("Move", 1)
        self.insert_state("SimEnd", 1)

        self.insert_input_port("GAME2VIEWER")

        self.file = None
        

        self.map_size = map_size
        self.current_map = [['O'] * map_size for _ in range(map_size)]
        self.end_point = []

        self.move_count = 0
        self.agent_count = agent_count
        
        self.agent_location = [] # 2차원 
        self.agent_move_log = [] # 2차원
        self.old_agent_location = []

        
    def get_moving_location(self, current_loc, direction) -> list :
        '''
        좌표랑 방향 주어지면 그거에 맞는 이동된 위치를 반환함
        '''
        next_loc = []

        if direction == MovingDirection.u.value :
            next_loc = [current_loc[0] - 1, current_loc[1]]
        elif direction == MovingDirection.d.value :
            next_loc = [current_loc[0] + 1, current_loc[1]]
        elif direction == MovingDirection.l.value :
            next_loc = [current_loc[0], current_loc[1] - 1]
        elif direction == MovingDirection.r.value :
            next_loc = [current_loc[0], current_loc[1] + 1]
        elif direction == MovingDirection.s.value :
            next_loc = current_loc

        return next_loc

    def out_of_range_check(self) :
        for i in range(self.agent_count) :
            if self.agent_location[i][0] < 0 or self.agent_location[i][0] > self.map_size - 1 or self.agent_location[i][1] < 0 or self.agent_location[i][1] > self.map_size - 1 :
                self.agent_location[i] = self.old_agent_location[i]
                



    def ext_trans(self, port, msg):
        if port == "GAME2VIEWER" :
            file_path = msg.retrieve()[0]
            self.file = json.load(open(file_path, "r"))

            self.end_point = self.file['end_point']
            self.current_map[self.end_point[0]][self.end_point[1]] = 'H'

            for i in range(self.agent_count) :
                self.agent_location.append(self.file[f"{i}"]["start_loc"])
                self.agent_move_log.append(self.file[f"{i}"]["best_arr"])
         

            self.old_agent_location = copy.deepcopy(self.agent_location)
            self._cur_state = "PrintMap"
    
    def output(self):
        if self.get_cur_state() == "PrintMap" :
            idx = 0
            for loc in self.agent_location :
                if loc != self.end_point :
                    self.current_map[loc[0]][loc[1]] = str(idx)
                idx += 1
            os.system("clear") # 맥용
            # os.system("cls") # 윈도우용
            print(*self.current_map, sep="\n")
            print("=========================")

        elif self.get_cur_state() == "Move" :
            for i in range(self.agent_count) :
                if self.agent_location[i] == self.end_point :
                    self.current_map[self.agent_location[i][0]][self.agent_location[i][1]] = 'H'
                else :
                    self.current_map[self.agent_location[i][0]][self.agent_location[i][1]] = 'O'
                if self.move_count < len(self.agent_move_log[i]) :
                    self.old_agent_location[i] = self.agent_location[i]
                    self.agent_location[i] = self.get_moving_location(self.agent_location[i], self.agent_move_log[i][self.move_count])
            self.move_count += 1
            self.out_of_range_check()

        elif self.get_cur_state() == "SimEnd" :
            exit()

    def int_trans(self):
        # if self.move_count >= len(self.agent_move_log[0]) :
        #     self._cur_state
        if self.get_cur_state() == "PrintMap" :
            self._cur_state = "Move"
        elif self.get_cur_state() == "Move" and self.move_count >= len(self.agent_move_log[0]):
            self._cur_state = "SimEnd"
        elif self.get_cur_state() == "Move" :
            self._cur_state = "PrintMap"

        