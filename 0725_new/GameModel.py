from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from NPCModel import NPCModel
from random import randint
from enum import Enum
import os
import json
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

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size = 10, agent_count = 3, max_epoch = 1, max_move = 50, random_percent = 0.5) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("NpcGen", 1)
        self.insert_state("EpochStart", 1)
        self.insert_state("Move", 1)
        self.insert_state("ColliDetec", 1)
        self.insert_state("PrintMap", 1)
        self.insert_state("SimEnd", 1)
        self.insert_state("Wait", 1)

        self.insert_input_port("start")
        self.insert_input_port("NPC2GAME")
        self.insert_output_port("GAME2NPC")
        self.insert_output_port("GAME2VIEWER")


        self.engine = SystemSimulator.get_engine(self.get_engine_name())

        self.sim_end = 0

        self.max_epoch = max_epoch
        self.map_size = map_size
        self.max_move = max_move # 한 개체 당 최대 움직임 수
        self.move_count = 0
        self.epoch = 0
        self.random_percent = random_percent
        self.current_map = [['■'] * self.map_size for _ in range(self.map_size)]
        self.end_point = self.get_endPoint()

        self.current_map[self.end_point[0]][self.end_point[1]] = '□'

        self.agent_count = agent_count # 에이전트의 수
        self.agent_location_arr = []
        self.ended_agent = []
        self.moved_agent = []
        self.detect_end_agent = []
        self.colli_agent = []
        self.need_to_move_agent_count = copy.deepcopy(self.agent_count)

        # 가장 괜찮았던 이동 로그(+ 점수변화율) / 점수 / 탈출 에이전트 수
        self.best_move_log = [[[] for _ in range(2)] for _ in range(self.agent_count)]
        self.best_game_score = -9999
        self.best_escaped_count = -1
        self.best_escaped_agent = [0 for _ in range(self.agent_count)]

        # 이번 에포크 이동 로그 / 점수 / 탈출 에이전트 수
        self.this_epoch_move_log = copy.deepcopy(self.best_move_log)
        self.this_epoch_game_score = 500
        self.this_epoch_escaped_count = 0
        self.this_epoch_escaped_agent = [0 for _ in range(self.agent_count)]

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
        os.system("clear") # 맥용
        # os.system("cls") # 윈도우용
        print(*self.current_map, sep="\n")
        print("=============================")
        print(f"Best Score : {self.best_game_score}")
        print(f"Best Escaped Agent Count : {self.best_escaped_count}")
        print(f"Current Score : {self.this_epoch_game_score}")
        print(f"Current Epoch : {self.epoch + 1}")

    def draw_agent(self) :
        idx = 0
        for loc in self.agent_location_arr :
            if loc != self.end_point and str(idx) not in self.ended_agent:
                self.current_map[loc[0]][loc[1]] = str(idx)
            idx += 1

    def update_best(self) :
        self.best_move_log = copy.deepcopy(self.this_epoch_move_log)
        self.best_game_score = copy.deepcopy(self.this_epoch_game_score)
        self.best_escaped_count = copy.deepcopy(self.this_epoch_escaped_count)
        self.best_escaped_agent = copy.deepcopy(self.this_epoch_escaped_agent)


    def ext_trans(self, port, msg) :
        if port == "start" :
            self._cur_state = "NpcGen"
        elif port == "NPC2GAME" :
            if self.sim_end == 1 :
                self._cur_state = "Wait"
            else :
                end_npc = self.engine.get_entity(f"{msg.retrieve()[1]}")[0]
                if msg.retrieve()[0] == "move_end" :
                    self.moved_agent.append(end_npc.get_name())
                    if len(self.moved_agent) == self.need_to_move_agent_count :
                        self.moved_agent = []
                        self._cur_state = "ColliDetec"
                elif msg.retrieve()[0] == "detect_end" :
                    self.detect_end_agent.append(int(end_npc.get_name()))
                    if list(set(self.detect_end_agent)).sort() == list(set(self.colli_agent)).sort() :
                        self.detect_end_agent = []
                        self.colli_agent = []
                        self._cur_state = "PrintMap"
                    
                elif msg.retrieve()[0] == "epoch_end" :
                    end_npc_location = end_npc.get_location()
                    # 이 NPC가 탈출에 성공해서 조기종료 한 것인지?
                    # 조기종료에서 부딛쳤으면 우짬
                    if end_npc.escaped == 1 :
                        self.this_epoch_game_score += 200
                        self.this_epoch_escaped_count += 1
                        self.this_epoch_escaped_agent[int(end_npc.get_name())] = 1
                        self.current_map[end_npc_location[0]][end_npc_location[1]] = '문'
                        self.agent_location_arr[int(msg.retrieve()[1])] = [None, None]
                    # 끝난 에이전트 모음에 추가
                    if msg.retrieve()[1] not in self.ended_agent :
                        # 다 움직인 에이전트 모음 + 이번 에포크 이동로그 모음에 추가함
                        self.ended_agent.append(msg.retrieve()[1])
                        self.need_to_move_agent_count -= 1
                        # 이동로그
                        self.this_epoch_move_log[int(msg.retrieve()[1])][0] = msg.retrieve()[2][0]
                        # 점수 변화율
                        self.this_epoch_move_log[int(msg.retrieve()[1])][1] = msg.retrieve()[2][1]

                    # 이 에이전트가 끝났을 시점에 모든 에이전트가 끝났고, 에포크도 다 돌았다면
                    # SimEnd로 상태천이
                    if len(self.ended_agent) == self.agent_count and self.epoch == self.max_epoch - 1 :
                        self._cur_state = "SimEnd"
                        self.sim_end = 1
                    elif len(self.ended_agent) == self.agent_count and self.epoch < self.max_epoch - 1 :
                        # 다음 에포크 돌도록 상태천이
                        # 그 전에, 좋았던 game_score를 찾아야됨
                        # 괜찮았던 move log를 찾는 방법
                        # 1. 탈출한 에이전트가 가장 많은 순
                        # 2. 점수가 더 높은 순
                        # 3. 더 빨리 끝난 순
                        if self.best_escaped_count < self.this_epoch_escaped_count :
                            # 탈출 에이전트 많은 순
                            self.update_best()
                        elif self.best_escaped_count == self.this_epoch_escaped_count :
                            if self.best_game_score < self.this_epoch_game_score :
                                # 점수 더 높은 순
                                self.update_best()
                            elif self.best_game_score == self.this_epoch_game_score :
                                max_best_move_log_len = max([len(self.best_move_log[i][0]) for i in range(len(self.best_move_log))])
                                max_this_move_log_len = max([len(self.this_epoch_move_log[i][0]) for i in range(len(self.this_epoch_move_log))])
                                if max_best_move_log_len > max_this_move_log_len :
                                    # 빨리 끝난 순
                                    self.update_best()

                        self.need_to_move_agent_count = copy.deepcopy(self.agent_count)
                        self.moved_agent = []
                        self.ended_agent = []
                        self.epoch += 1
                        self._cur_state = "EpochStart"

                elif msg.retrieve()[0] == "out_of_range" :
                    self.this_epoch_game_score -= 20
                    self.moved_agent.append(end_npc.get_name())
                    if len(self.moved_agent) == self.need_to_move_agent_count :
                        self._cur_state = "ColliDetec"
                        self.moved_agent = []



    def output(self) :
        if self.get_cur_state() == "NpcGen" :
            for idx in range(self.agent_count) :
                ''' 
                지정한 agent 수 대로 0부터 해서 생성하고 연결
                ''' 
                os.system("clear") # 맥용 
                # os.system("cls") # 윈도우용
                npc = NPCModel(0, Infinite, f"{idx}", self.engine_name, self.map_size, self.end_point, self.max_epoch, self.max_move, self.random_percent)
                self.engine.register_entity(npc)
                self.engine.coupling_relation(self, "GAME2NPC", npc, "GAME2NPC")
                self.engine.coupling_relation(npc, "NPC2GAME", self, "NPC2GAME")
                while (npc.get_location() in self.agent_location_arr or npc.get_location() == self.end_point) :
                    npc.reset_location()
                self.agent_location_arr.append(npc.get_location())
            self.draw_agent()
            self.print()

        elif self.get_cur_state() == "EpochStart" :
            self.this_epoch_game_score = 500
            self.this_epoch_escaped_count = 0
            
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("EpochStart")
            msg.insert(self.epoch)
            msg.insert(self.best_move_log)
            msg.insert(self.best_escaped_agent)
            return msg
        
        elif self.get_cur_state() == "Move" :
            self.move_count += 1
            self.this_epoch_game_score -= 5
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("Move")
            msg.insert(self.ended_agent)
            return msg
        
        elif self.get_cur_state() == "ColliDetec" :
            for i in range(len(self.agent_location_arr)) :
                npc = self.engine.get_entity(f"{i}")[0]
                self.agent_location_arr[i] = npc.get_location()

            agent_arr = list(range(self.agent_count))
            colli_arr = []
            msg = SysMessage(self.get_name(), "GAME2NPC")
            msg.insert("Bumped")
            
            while(agent_arr) :
                idx = 0
                temp = [agent_arr[0]]
                for i in range(idx + 1, len(agent_arr)) :
                    if self.agent_location_arr[agent_arr[0]] == self.agent_location_arr[agent_arr[i]] and self.agent_location_arr[agent_arr[i]] != [None, None]:
                        temp.append(agent_arr[i])
                        # 부딛친 에이전트 당 50점씩 빼기
                        self.this_epoch_game_score -= 50

                if len(temp) != 1 :
                    for x in temp :
                        self.colli_agent.append(x)
                    colli_arr.append(temp)
                
                for j in temp :
                    del agent_arr[agent_arr.index(j)]            
                    
            if len(colli_arr) != 0 :
                msg.insert(colli_arr)
                return msg
            
        elif self.get_cur_state() == "PrintMap" :
            self.current_map = [['■'] * self.map_size for _ in range(self.map_size)]
            self.current_map[self.end_point[0]][self.end_point[1]] = '□'

            self.draw_agent()
            self.print()

        elif self.get_cur_state() == "SimEnd" :
            # Json 파일로 저장하는 방법 --------------------------
            dict_data = {
                "end_point" : self.end_point,
                "escaped_count" : self.best_escaped_count,
                "best_score" : self.best_game_score
            }
            
            for i in range(self.agent_count) :
                npc = self.engine.get_entity(f"{i}")[0]
                temp_dict = {
                    "start_loc" : npc.start_location,
                    "best_arr" : self.best_move_log[i][0],
                    "score_delta" : self.best_move_log[i][1],
                    "escaped" : self.best_escaped_agent[i],
                }
                dict_data[f'{i}'] = temp_dict

            json_data = json.dumps(dict_data)
            print(json_data)

            with open("Result.json", "w") as file:
                file.write(json_data)


            # 텍스트 파일로 저장하는 방법 --------------------------
            # with open("Result.txt", "w") as file :
            #     file.write("Best Move Log and Score\n\n")
            #     file.write(f"End Point : {self.end_point}\n\n")
            #     file.write("===========================================\n")
            #     for i in range(self.agent_count) :
            #         npc = self.engine.get_entity(f"{i}")[0]
            #         best_arr = npc.best_move_arr
            #         file.write(f"Agent {i}\n")
            #         file.write(f"- Start Location : {npc.start_location}\n")
            #         file.write(f"- Move Log : ")
            #         for direction in best_arr :
            #                 file.write(f"{MovingDirection(direction).name} ")
            #         file.write(f"\n- Raw Move Log : {best_arr}")
            #         file.write(f"\n- Escaped : ")
            #         if npc.best_escaped == 1 :
            #             file.write("True")
            #         else :
            #             file.write("False")
            #         file.write(f"\n- Final Score : {npc.best_score}\n\n")
            #         file.write("===========================================\n")
            
            # exit()
            msg = SysMessage(self.get_name(), "GAME2VIEWER")
            msg.insert("Result.json")
            self.engine.sim_mode = "REAL_TIME"

            return msg
        
        elif self._cur_state == "Wait" :
            pass

    def int_trans(self) :
        if self.get_cur_state() == "NpcGen" :
            self._cur_state = "EpochStart"
        elif self.get_cur_state() == "EpochStart" :
            self._cur_state = "Move"
        elif self.get_cur_state() == "Move" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "ColliDetec" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "PrintMap" :
            self._cur_state = "Move"
        elif self.get_cur_state() == "SimEnd" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Wait" and len(self.moved_agent) == self.need_to_move_agent_count:
            self.moved_agent = []
            self._cur_state = "ColliDetec"
        elif self.get_cur_state() == "Wait" and list(set(self.detect_end_agent)) == list(set(self.colli_agent)):
            self._cur_state = "PrintMap"
        elif self.get_cur_state() == "Wait" :
            self._cur_state = "Wait"