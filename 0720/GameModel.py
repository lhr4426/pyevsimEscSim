from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from NPCModel import NPCModel, MovingDirection
from random import randint
from enum import Enum
import os, sys
import copy

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

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size = 10, agent_count = 3, max_epoch = 1, max_move = 50) :
        '''
        주어진 크기의 맵을 만듬
        '''
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("NpcGen", 1)
        self.insert_state("EpochStart", 1)
        self.insert_state("Action", 1)
        self.insert_state("ColliDetec", 1)
        self.insert_state("PrintMap", 1)
        self.insert_state("SimEnd")

        self.insert_input_port("start")
        self.insert_input_port("location")
        self.insert_input_port("agent_end")
        self.insert_output_port("move")
        self.insert_output_port("you_are_bumped")
        self.insert_output_port("epoch_start")

        self.engine = SystemSimulator.get_engine(self.get_engine_name())

        self.max_epoch = max_epoch
        self.map_size = map_size
        self.max_move = max_move # 한 개체 당 최대 움직임 수
        self.move_count = 0
        self.epoch = 0
        self.current_map = [['ㅁ'] * self.map_size for _ in range(self.map_size)]
        self.end_point = self.get_endPoint()

        self.current_map[self.end_point[0]][self.end_point[1]] = '문' # 탈출구 설정

        self.agent_count = agent_count # 에이전트의 수
        self.agent_location_arr = []
        self.escaped_agent = []

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
        os.system("clear")
        print(*self.current_map, sep="\n")
        print("=============================")

            
    def ext_trans(self, port, msg) :
        if port == "start" :
            self._cur_state = "NpcGen"
        elif port == "agent_end" :
            end_npc = self.engine.get_entity(f"{msg.retrieve()[0]}")[0]
            end_npc_location = end_npc.get_location()
            if end_npc.escaped == 1 :
                self.current_map[end_npc_location[0]][end_npc_location[1]] = '문'
            if msg.retrieve()[0] not in self.escaped_agent :
                self.escaped_agent.append(msg.retrieve()[0])
            if len(self.escaped_agent) == self.agent_count and self.epoch < self.max_epoch:
                self.escaped_agent = []
                self.epoch += 1
                self._cur_state = "EpochStart"
            elif self.epoch >= self.max_epoch :
                self._cur_state = "SimEnd"




    def output(self) :
        if self.get_cur_state() == "NpcGen" :
            for idx in range(self.agent_count) :
                '''
                지정한 agent 수 대로 0부터 해서 agent를 생성하고 연결함
                '''
                os.system("clear")
                npc = NPCModel(0, Infinite, f"{idx}", self.engine_name, self.map_size, self.end_point, self.max_epoch, self.max_move)
                print(f"npc_{idx} registered")
                self.engine.register_entity(npc)
                self.engine.coupling_relation(self, "epoch_start", npc, "epoch_start")
                self.engine.coupling_relation(self, "move", npc, "move")
                # you_are_bumped => 누군가랑 부딛쳤다는 뜻
                self.engine.coupling_relation(self, "you_are_bumped", npc, "you_are_bumped") 
                self.engine.coupling_relation(self, "epoch_end", npc, "epoch_end")
                self.engine.coupling_relation(npc, "agent_end", self, "agent_end")
                # 생성하자마자 겹치지는 않도록 설정함
                while (npc.get_location() in self.agent_location_arr) :
                    npc.reset_location()
                self.agent_location_arr.append(npc.get_location())
            self.draw_agent()
            self.print()

        elif self.get_cur_state() == "EpochStart" :
            msg = SysMessage(self.get_name, "epoch_start")
            msg.insert(None)
            return msg

        elif self.get_cur_state() == "Action" :
            msg = SysMessage(self.get_name(), "move")
            msg.insert("move")
            return msg
        
        elif self.get_cur_state() == "ColliDetec" :
            self.move_count += 1
            for i in range(len(self.agent_location_arr) - 1) :
                for j in range(i + 1, len(self.agent_location_arr)) :
                    if self.agent_location_arr[i] == self.agent_location_arr[j] :
                        msg = SysMessage(self.get_name(), "you_are_bumped")
                        msg.insert(f"{i}")
                        msg.insert(f"{j}")
                        return msg
                    
        elif self.get_cur_state() == "PrintMap" :
            '''
            여기서 업데이트된 agent들의 위치정보를 가져옴과 동시에 맵을 그릴거임 
            근데 그 전에 위치를 다시 'ㅁ' 로 바꿔야됨
            '''
            for loc in self.agent_location_arr :
                if loc == self.end_point :
                    self.current_map[loc[0]][loc[1]] = '문'
                else :
                    self.current_map[loc[0]][loc[1]] = 'ㅁ'

            for i in range(len(self.agent_location_arr)) :
                npc = self.engine.get_entity(f"{i}")[0]
                self.agent_location_arr[i] = npc.get_location()

            self.draw_agent()
            self.print()    
        
        elif self.get_cur_state() == "SimEnd" :
            with open("end.txt", "w") as file :
                    file.write("Best Move Log and Score\n")
                    for i in range(self.agent_count) :
                        npc = self.engine.get_entity(f"{i}")[0]
                        best_arr = npc.best_move_arr
                        file.write(f"Agent {i}\n")
                        file.write(f"- Start Location : {npc.start_location}\n")
                        file.write("- Move Log : ")
                        for direction in best_arr :
                            file.write(f"{MovingDirection(direction).name} ")
                        file.write(f"\n- Raw Move Log : {best_arr}")
                        file.write(f"\n- Final Score : {npc.best_score}\n\n")
            exit()


    def draw_agent(self) :
        idx = 0
        for loc in self.agent_location_arr :
            self.current_map[loc[0]][loc[1]] = idx
            idx += 1

    def int_trans(self) :
        if self.get_cur_state() == "NpcGen" :
            self._cur_state = "EpochStart"
        elif self.get_cur_state() == "EpochStart" :
            self._cur_state = "Action"
        elif self.get_cur_state() == "Action" :
            self._cur_state = "ColliDetec"
        elif self.get_cur_state() == "ColliDetec" :
            self._cur_state = "PrintMap"
        elif self.get_cur_state() == "PrintMap" :
            self._cur_state = "Action"
        elif self.get_cur_state() == "SimEnd" :
            self._cur_state = "Init"
