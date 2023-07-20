from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from NPCModel import NPCModel, MovingDirection
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

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size = 10, agent_count = 3, max_epoch = 1, max_move = 50) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("NpcGen", 1)
        self.insert_state("EpochStart", 1)
        self.insert_state("Move", 1)
        self.insert_state("ColliDetec", 1)
        self.insert_state("PrintMap", 1)
        self.insert_state("SimEnd", Infinite)

        self.insert_input_port("start")
        self.insert_input_port("NPC2GAME")
        self.insert_output_port("GAME2NPC")


        self.engine = SystemSimulator.get_engine(self.get_engine_name())

        self.max_epoch = max_epoch
        self.map_size = map_size
        self.max_move = max_move # 한 개체 당 최대 움직임 수
        self.move_count = 0
        self.epoch = 0
        self.current_map = [['ㅁ'] * self.map_size for _ in range(self.map_size)]
        self.end_point = self.get_endPoint()

        self.current_map[self.end_point[0]][self.end_point[1]] = '문'

        self.agent_count = agent_count # 에이전트의 수
        self.agent_location_arr = []
        self.ended_agent = []

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

    def draw_agent(self) :
        idx = 0
        for loc in self.agent_location_arr :
            if loc != self.end_point :
                self.current_map[loc[0]][loc[1]] = idx
            idx += 1

    def ext_trans(self, port, msg) :
        if port == "start" :
            self._cur_state = "NpcGen"
        elif port == "NPC2GAME" :
            if msg.retrieve()[0] == "epoch_end" :
                end_npc = self.engine.get_entity(f"{msg.retrieve()[1]}")[0]
                end_npc_location = end_npc.get_location()
                # 이 NPC가 탈출에 성공해서 조기종료 한 것인지?
                if end_npc.escaped == 1 :
                    self.current_map[end_npc_location[0]][end_npc_location[1]] = '문'
                    self.agent_location_arr[msg.retrieve()[1]] = [None, None]
                # 끝난 에이전트 모음에 추가
                if msg.retrieve()[1] not in self.ended_agent :
                    self.ended_agent.append(msg.retrieve()[1])
                # 이 에이전트가 끝났을 시점에 모든 에이전트가 끝났고, 에포크도 다 돌았다면
                # SimEnd로 상태천이
                if len(self.ended_agent) == self.agent_count and self.epoch >= self.max_epoch :
                    self._cur_state = "SimEnd"
                elif len(self.ended_agent) == self.agent_count and self.epoch < self.max_epoch :
                    # 다음 에포크 돌도록 상태천이
                    self.ended_agent = []
                    self.epoch += 1
                    self._cur_state = "EpochStart"

    def output(self) :
        if self.get_cur_state() == "NpcGen" :
            for idx in range(self.agent_count) :
                ''' 
                지정한 agent 수 대로 0부터 해서 생성하고 연결
                ''' 
                os.system("clear")
                npc = NPCModel(0, Infinite, f"{idx}", self.engine_name, self.map_size, self.end_point, self.max_epoch, self.max_move)
                self.engine.register_entity(npc)
                self.engine.coupling_relation(self, "GAME2NPC", npc, "GAME2NPC")
                self.engine.coupling_relation(npc, "NPC2GAME", self, "NPC2GAME")
                while (npc.get_location() in self.agent_location_arr) :
                    npc.reset_location()
                self.agent_location_arr.append(npc.get_location())
            self.draw_agent()
            self.print()

        elif self.get_cur_state() == "EpochStart" :
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("EpochStart")
            return msg
        
        elif self.get_cur_state() == "Move" :
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("Move")
            return msg
        
        elif self.get_cur_state() == "ColliDetec" :
            collision_detect = []
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("Bumped")
            msg.insert(f"{randint(0,1)}")
            for i in range(len(self.agent_location_arr) - 1) :
                for j in range(i + 1, len(self.agent_location_arr)) :
                    if self.agent_location_arr[i] == self.agent_location_arr[j] :
                        collision_detect.append(f"{i}")
                        collision_detect.append(f"{j}")
                    
            if len(collision_detect) != 0 :
                for idx in collision_detect :
                    msg.insert(f"{idx}")
                return msg
            
        elif self.get_cur_state() == "PrintMap" :
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
            with open("Result.txt", "w") as file :
                file.write("Best Move Log and Score\n")
                for i in range(self.agent_count) :
                    npc = self.engine.get_entity(f"{i}")[0]
                    best_arr = npc.best_move_arr
                    file.write(f"Agent {i}\n")
                    file.write(f"- Start Location : {npc.start_location}\n")
                    for direction in best_arr :
                            file.write(f"{MovingDirection(direction).name} ")
                    file.write(f"\n- Escaped : ")
                    if npc.best_escaped == 1 :
                        file.write("True")
                    else :
                        file.write("False")
                    file.write(f"\n- Raw Move Log : {best_arr}")
                    file.write(f"\n- Final Score : {npc.best_score}\n\n")
                    file.write("===========================================")
            exit()

    def int_trans(self) :
        if self.get_cur_state() == "NpcGen" :
            self._cur_state = "EpochStart"
        elif self.get_cur_state() == "EpochStart" :
            self._cur_state = "Move"
        elif self.get_cur_state() == "Move" :
            self._cur_state = "ColliDetec"
        elif self.get_cur_state() == "ColliDetec" :
            self._cur_state = "PrintMap"
        elif self.get_cur_state() == "PrintMap" :
            self._cur_state = "Move"