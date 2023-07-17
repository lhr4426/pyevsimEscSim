from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from NPCModel import NPCModel
from random import randint
from enum import Enum
import os

class EndPointDirection(Enum) :
    up = 0
    down = 1
    left = 2
    right = 3

class GameModel(BehaviorModelExecutor) :
    '''
        1. Init때 10*10의 맵을 만들고, 테두리 중 하나를 탈출구로 지정함 
        2. NpcGen때 NPC들을 만듬
        3. CD때 충돌을 확인함  
    '''

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size = 10, agent_count = 3) :
        '''
        주어진 크기의 맵을 만듬
        '''
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("NpcGen", 1)
        self.insert_state("Action", 1)
        self.insert_state("ColliDetec", 1)

        self.insert_input_port("start")
        self.insert_output_port("move")
        self.insert_output_port("you_are_bumped")

        self.map_size = map_size
        self.map = [['ㅁ'] * self.map_size for _ in range(self.map_size)]
        self.end_point = self.get_endPoint()

        self.map[self.end_point[0]][self.end_point[1]] = '문' # 탈출구 설정

        self.agent_count = agent_count # 에이전트의 수
        self.agent_location_arr = []

        self.print()

    def get_endPoint(self) -> int :
        '''
        탈출구의 위치를 반환함
        '''
        direction_of_EP = randint(0,3)
        where_is_EP = randint(1, self.map_size - 2)

        if direction_of_EP == EndPointDirection.up.value :
            return [0, where_is_EP]

        elif direction_of_EP == EndPointDirection.down.value :
            return [self.map_size - 1, where_is_EP]
        
        elif direction_of_EP == EndPointDirection.left.value :
            return [where_is_EP, 0]
        
        elif direction_of_EP == EndPointDirection.right.value :
            return [where_is_EP, self.map_size - 1]
        
    def print(self) :
        '''
        맵 정보를 출력함
        '''
        print(*self.map, sep="\n")
            
    def ext_trans(self, port, msg) :
        if port == "start" :
            self._cur_state = "NpcGen"

    def output(self) :
        if self.get_cur_state() == "NpcGen" :
            engine = SystemSimulator.get_engine(self.get_engine_name())
            for idx in range(self.agent_count) :
                '''
                지정한 agent 수 대로 0부터 해서 agent를 생성하고 연결함
                '''
                os.system("clear")
                npc = NPCModel(0, Infinite, f"{idx}", self.engine_name, self.map_size, self.end_point)
                print(f"npc_{idx} registered")
                engine.register_entity(npc)
                engine.coupling_relation(self, "move", npc, "move")
                # you_are_bumped => 누군가랑 부딛쳤다는 뜻
                engine.coupling_relation(self, "you_are_bumped", npc, "you_are_bumped") 
                # 생성하자마자 겹치지는 않도록 설정함
                while (npc.get_location() in self.agent_location_arr) :
                    npc.reset_location()
                self.agent_location_arr.append(npc.get_location())
            self.draw_agent()
            self.print()
                
    def draw_agent(self) :
        idx = 0
        for loc in self.agent_location_arr :
            self.map[loc[0]][loc[1]] = idx
            idx += 1

    def int_trans(self) :
        if self.get_cur_state() == "NpcGen" :
            self._cur_state = "Action"
        elif self.get_cur_state() == "Action" :
            self._cur_state = "ColliDetec"
        elif self.get_cur_state() == "ColliDetec" :
            self._cur_state = "Action"

