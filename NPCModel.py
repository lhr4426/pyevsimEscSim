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

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.init_state("Init", Infinite)
        self.init_state("Move", 0)

        self.insert_input_port("move")

        self.map_size = map_size
        self.location = self.reset_location()
        self.move_log = []
        self.score = 500 # 스코어 500에서 시작
        self.old_location = [] # 이전 위치를 저장 (나중에 충돌났을때 이전 위치로 돌리고 멈추게 하려고)
        
    def return_location(self) :
        return self.location
    
    def reset_location(self) :
        '''
        에이전트의 위치를 변경하고 그 값을 반환함
        '''
        self.location = [randint(0, self.map_size - 1), randint(0, self.map_size - 1)]
        return self.location
