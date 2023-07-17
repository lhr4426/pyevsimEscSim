from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from random import randint
from enum import Enum

class MovingDirection(Enum) :
    up = 0
    down = 1
    left = 2
    right = 3
    stop = 4

class NPCModel(BehaviorModelExecutor) :
    '''
        1. Init때 랜덤 위치에 소환
        2. 이동할 위치를 설정함 (상/하/좌/우/안움직임)
    '''

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size, end_point) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("Move", 0)
        self.insert_state("Wait", Infinite)

        self.insert_input_port("move")
        self.insert_input_port("you_are_bumped")

        self.map_size = map_size
        self.location = self.reset_location()
        self.move_log = []
        self.score = 500 # 스코어 500에서 시작
        self.old_location = [] # 이전 위치를 저장 (나중에 충돌났을때 이전 위치로 돌리고 멈추게 하려고)
        self.end_point = end_point
        self.next_decision_arr = [0, 1, 2, 3, 4]
        self.current_decision = None
        
    def get_location(self) :
        return self.location
    
    def reset_location(self) :
        '''
        에이전트의 위치를 변경하고 그 값을 반환함
        '''
        self.location = [randint(0, self.map_size - 1), randint(0, self.map_size - 1)]
        return self.location

    def move_location(self, choice) :
        self.old_location = self.location
        if choice == MovingDirection.up.value :
            self.location = [self.old_location[0]+1, self.old_location[1]]
        elif choice == MovingDirection.down.value :
            self.location = [self.old_location[0]-1, self.old_location[1]]
        elif choice == MovingDirection.left.value :
            self.location = [self.old_location[0], self.old_location[1]-1]
        elif choice == MovingDirection.right.value :
            self.location = [self.old_location[0], self.old_location[1]+1]
        elif choice == MovingDirection.stop.value :
            self.location = self.old_location
        
    def out_of_range_check(self) :
        if self.location[0] < 0 or self.location[0] > self.map_size - 1 or self.location[1] < 0 or self.location[1] > self.map_size - 1 :
            self.location = self.old_location
            self.score -= 10

    def ext_trans(self, port, msg) :
        if port == "move" :
            self._cur_state = "Move"
    
    def output(self) :
        pass

    def int_trans(self) :
        if self.get_cur_state() == "Move" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Wait" :
            self._cur_state = "Wait"

            