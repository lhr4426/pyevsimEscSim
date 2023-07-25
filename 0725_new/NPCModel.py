from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage
from random import randint, random
from enum import Enum
from copy import deepcopy

class MovingDirection(Enum) :
    u = 0 # up
    d = 1 # down
    l = 2 # left
    r = 3 # right
    s = 4 # stop

class NPCModel(BehaviorModelExecutor) :
    '''
        1. Init때 랜덤 위치에 소환
        2. 이동할 위치를 설정함 (상/하/좌/우/안움직임)
        3. 1 에포크당 움직인 내역 + 움직였을때 점수 저장
    '''

    def __init__(self, instance_time, destruct_time, name, engine_name, map_size, end_point, max_epoch, max_move, random_percent = 0.8) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("EpochStart", 1)
        self.insert_state("Move", 1)
        self.insert_state("MoveCheck", 1)
        self.insert_state("Bumped", 1)
        self.insert_state("Wait", Infinite)
    
        self.insert_input_port("GAME2NPC")
        self.insert_output_port("NPC2GAME")
    
        self.map_size = map_size

        # 에포크 카운트 자체는 필요할듯
        self.max_epoch = max_epoch
        self.epoch = 0

        # 1 에포크 당 최대 움직임 수와 현재 움직임 카운트는 어차피 GameModel이 확인함

        self.start_location = self.reset_location()
        self.location = deepcopy(self.start_location)
        self.move_log = [] # 움직인 로그 저장용
        self.score_delta = [] # 점수 변화율
        self.location_log = [] # 나중에 이동로그 압축하려고
        self.old_location = [] # 이전 위치를 저장 (나중에 충돌났을때 이전 위치로 돌리고 멈추게 하려고)
        self.end_point = end_point
        # 멈춘다는 선택을 직접적으로는 못하게 할것
        # 나중에 부딛쳤다는 내용 뜨면 그때 할거임
        self.next_decision_arr = [0, 1, 2, 3]
        # 지금까지중에 최종 점수가 높게 나왔던 move log임
        self.best_move_arr = []
        self.best_score_delta = []
        # move log의 길이
        self.current_decision = None
        self.escaped = 0
        self.max_move = max_move 

        # 잘 탈출한 선례를 몇 퍼센트의 확률로 따를 것인가
        self.random_percent = random_percent 
        
    def get_location(self) :
        return self.location

    def reset_location(self) :
        '''
        에이전트의 위치를 변경하고 그 값을 반환함
        생성했을 때만 사용함
        '''
        self.start_location = [randint(0, self.map_size - 1), randint(0, self.map_size - 1)]
        self.location = deepcopy(self.start_location)
        return self.location
    
    # def get_best_arr(self) :



    # 이 함수 안쓸거임
    # def get_best_arr(self) -> None:
    #     '''
    #     가장 좋았던 epoch의 move_log를 best_arr로 지정함.   
    #     조건 1. 탈출했을 것
    #     조건 2. 점수가 높을 것
    #     조건 3. 점수가 같다면 회수가 더 낮은것 고를 것
    #     '''
    #     best_idx = 0
    #     escaped_index_list = list(filter(lambda x: self.escaped_log[x] == 1, range(len(self.escaped_log))))
    #     if len(escaped_index_list) != 0 :
    #         best_idx = escaped_index_list[0]
        
    #     if len(escaped_index_list) != 0 :
    #         for i in escaped_index_list :
    #             if self.score_log[i][-1] > self.best_score :
    #                 # i번째 결과 점수가 best_idx 번째 결과 점수보다 높으면
    #                 best_idx = i
    #             elif self.score_log[i][-1] == self.best_score :
    #                 # 결과 점수가 같으면 이동회수가 더 짧은걸로 고름
    #                 if len(self.move_log[i]) < len(self.move_log[best_idx]) :
    #                     best_idx = i
    #     elif len(escaped_index_list) == 0 :
    #         for i in range(len(self.score_log)) :
    #             if self.score_log[i][-1] > self.best_score :
    #                 best_idx = i
    #             elif self.score_log[i][-1] == self.best_score :
    #                 if len(self.move_log[i]) < len(self.move_log[best_idx]) :
    #                     best_idx = i
        
    #     self.best_move_arr = self.move_log[best_idx]
    #     self.best_score_arr = self.score_log[best_idx]
    #     self.best_escaped = self.escaped_log[best_idx]
    #     self.best_score = self.best_score_arr[-1]
                
    #     # temp_best_idx = 0
    #     # for i in range(len(self.move_log) - 1) :
    #     #     if self.score_log[i][-1] > self.score_log[temp_best_idx][-1] :
    #     #         temp_best_idx = i
    #     #     elif self.score_log[i][-1] == self.score_log[temp_best_idx][-1] :
    #     #         if len(self.move_log[i]) < len(self.move_log[temp_best_idx]) :
    #     #             temp_best_idx = i
    #     # self.best_move_arr = self.move_log[temp_best_idx]
    #     # self.best_score_arr = self.score_log[temp_best_idx]
    #     # self.best_escaped = self.escaped_log[temp_best_idx]
    #     # self.best_score = self.best_score_arr[-1]
    


    def move_location(self) :
        print("===============================")
        print(f"Agent {self.get_name()}")
        print(f"Next Decision Array : {self.next_decision_arr}")
        print(f"current decision : {self.current_decision}")
        print(f"Current Location : {self.location}")
        print(f"Move Log : {self.move_log}")
        print(f"Location Log : {self.location_log}")
        
        self.old_location = self.location
        if self.current_decision == MovingDirection.u.value :
            self.location = [self.old_location[0]-1, self.old_location[1]]
        elif self.current_decision == MovingDirection.d.value :
            self.location = [self.old_location[0]+1, self.old_location[1]]
        elif self.current_decision == MovingDirection.l.value :
            self.location = [self.old_location[0], self.old_location[1]-1]
        elif self.current_decision == MovingDirection.r.value :
            self.location = [self.old_location[0], self.old_location[1]+1]
        elif self.current_decision == MovingDirection.s.value :
            self.location = self.old_location

        # self.location_log.append(self.location)
        # self.move_log.append(self.current_decision)
        # self.score_delta.append(-1)
        
    def remove_opposite_moving(self) :
        if self.current_decision == MovingDirection.s.value :
            pass
        elif self.current_decision == MovingDirection.u.value :
            if MovingDirection.d.value in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(MovingDirection.d.value)]
        elif self.current_decision == MovingDirection.d.value :
            if MovingDirection.u.value in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(MovingDirection.u.value)]
        elif self.current_decision == MovingDirection.l.value :
            if MovingDirection.r.value in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(MovingDirection.r.value)]
        elif self.current_decision == MovingDirection.r.value :
            if MovingDirection.l.value in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(MovingDirection.l.value)]
                
    def out_of_range_check(self) :
        # 만약에 이동했는데 위치가 이상함
        msg = None
        if self.location[0] < 0 or self.location[0] > self.map_size - 1 or self.location[1] < 0 or self.location[1] > self.map_size - 1 :
            if len(self.score_delta) == 0 :
                self.score_delta.append(-20)
            else :
                self.score_delta[-1] -= 20

            self.location = self.old_location
            
            if self.current_decision in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(self.current_decision)]
            # 다음 결정에서는 다른 선택을 하도록, 방금 전에 한 선택을 뺌
            msg = SysMessage(self.get_name(), "NPC2GAME")
            msg.insert("out_of_range")
            
        # 이동했을때 위치가 이상하지 않음
        else :
            self.next_decision_arr = [0,1,2,3] 
            self.remove_opposite_moving()
            # 이번 선택의 반대편을 제외한 모든 선택 중 고를 수 있도록 함

        self.location_log.append(self.location)
        self.move_log.append(self.current_decision)
        self.score_delta.append(-1)

        if msg is not None :return msg
        else : return None
        # print(f"current epoch : {self.epoch}")
        # print(f"move log : {self.move_log[self.epoch]}")
        # print(f"current score : {self.score}")
        # print(f"current decision : {self.current_decision}")

    def make_choice(self,index, decision_len) -> int :
        '''
        만약에 이번이 첫 epoch가 아니면, 지금까지 있던 epoch 중에서  
        이번 차례에 가장 좋았던 선택 vs 랜덤 선택을 확률적으로 시킴
        근데 만약에 best 선택으로 인해 점수 변화가 -10 이상 났으면 안함
        best 선택으로 점수변화가 +100 이상 났으면 그거 고름
        '''
        if decision_len == 0 :
            self.next_decision_arr = [0,1,2,3]
            decision_len = 4

        random_decision = randint(0, decision_len - 1)  

        if self.epoch != 0 and index < len(self.best_move_arr):
            if self.best_score_delta[index] < -10 :
                if self.best_move_arr[index] in self.next_decision_arr :
                    del self.next_decision_arr[self.next_decision_arr.index(self.best_move_arr[index])]
                    decision_len -= 1
                    if decision_len == 0 :
                        self.next_decision_arr = [0,1,2,3]
                        return 4
                    else :
                        random_decision = randint(0, decision_len - 1)
                return self.next_decision_arr[random_decision]
            
            elif self.best_score_delta[index] > 100 :
                return self.best_move_arr[index]

              
            best_decision = self.best_move_arr[index]
            random_percent = random()
            # 주어진 확률로 더 좋은 선택을 함
            if random_percent <= self.random_percent :
                return best_decision
            else :
                return self.next_decision_arr[random_decision]
        else :
            return self.next_decision_arr[random_decision]

    def is_one_location_diff(self, location_1, location_2) :
        # location_1과 location_2가 한칸만 차이나는지 확인할거임
        diff = [loc1 - loc2 for loc1, loc2 in zip(location_1, location_2)]
        # 한 칸 차이나는 경우 = [0, 1] , [0, -1], [1, 0], [-1, 0] -> 합이 1이거나 -1임
        condition = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        if diff in condition:
            return True
        else :
            return False


    def compress_move_log(self) :
        
        while(self.max_move > 4) :
            flags = [1, 1, 1]
            idx = 3
            while(True) :
                if len(self.location_log) < 4 or idx > len(self.location_log) - 1:
                    break
                # 빙글 돌았을 경우
                if self.is_one_location_diff(self.location_log[idx - 3], self.location_log[idx - 2]) and self.is_one_location_diff(self.location_log[idx - 2], self.location_log[idx - 1]) and self.is_one_location_diff(self.location_log[idx - 1], self.location_log[idx]) and self.location_log[idx] == self.location_log[idx - 3] :
                    del self.move_log[idx - 2: idx + 1]
                    del self.score_delta[idx - 2 : idx + 1]
                    del self.location_log[idx - 2 : idx + 1]
                    # print(f"빙글 압축 후 : {self.location_log}, {len(self.location_log)}")
                    idx -= 1
                    if idx < 3 : idx = 3
                    flags[0] = 0
                    continue
                else :
                    idx += 1
            idx = 3
            while(True) :
                if len(self.location_log) < 4 or idx > len(self.location_log) - 1:
                    break
                # 돌다 만 경우
                if self.is_one_location_diff(self.location_log[idx], self.location_log[idx-3]) :
                    del self.move_log[idx - 2]
                    del self.move_log[idx - 1]
                    del self.score_delta[idx - 2 : idx]
                    del self.location_log[idx - 2 : idx]
                    # print(f"반 빙글 압축 후 : {self.location_log}, {len(self.location_log)}")
                    idx -= 1
                    if idx < 3 : idx = 3
                    flags[1] = 0
                    continue
                else :
                    idx += 1
            idx = 2
            while(True) :
                if len(self.location_log) < 3 or idx > len(self.location_log) - 1 :
                    break
                # 왔다갔다한 경우
                if self.is_one_location_diff(self.location_log[idx - 2], self.location_log[idx - 1]) and self.location_log[idx - 2] == self.location_log[idx] :
                    del self.move_log[idx - 1 : idx + 1]
                    del self.score_delta[idx - 1 : idx + 1]
                    del self.location_log[idx - 1: idx + 1]
                    # print(f"왔다갔다 압축 후 : {self.location_log}, {len(self.location_log)}")
                    idx -= 1
                    if idx < 2 : idx = 2
                    flags[2] = 0
                    continue
                else :
                    idx += 1
            if flags == [1, 1, 1] :
                break

    def epoch_end_process(self) -> SysMessage :
        # self.get_best_arr()
        print(f"Location Log 압축 전 : {self.location_log}, {len(self.location_log)}")
        print(f"Move Log 압축 전 : {self.move_log}, {len(self.move_log)}")
        print(f"Score Delta 압축 전 : {self.score_delta}, {len(self.score_delta)}")
        self.compress_move_log()
        print(f"Location Log 압축 후 : {self.location_log}, {len(self.location_log)}")
        print(f"Move Log 압축 후 : {self.move_log}, {len(self.move_log)}")
        print(f"Score Delta 압축 후 : {self.score_delta}, {len(self.score_delta)}")
    
        msg = SysMessage(self.get_name(), "NPC2GAME")
        msg.insert("epoch_end")
        msg.insert(self.get_name())
        msg.insert([self.move_log, self.score_delta])
        return msg


    def ext_trans(self, port, msg) :
        if port == "GAME2NPC" :
            if msg.retrieve()[0] == "EpochStart" :
                self.move_log = [] # 움직인 로그 저장용
                self.score_delta = [] # 점수 변화율
                self.location_log = [] # 나중에 이동로그 압축하려고
                self.old_location = [] # 이전 위치를 저장 (나중에 충돌났을때 이전 위치로 돌리고 멈추게 하려고)
        
                self.escaped = 0
                self.location = deepcopy(self.start_location)      
                
                self.epoch = msg.retrieve()[1]
                if len(msg.retrieve()[2][int(self.get_name())]) != 0 :
                    self.best_move_arr = msg.retrieve()[2][int(self.get_name())][0]
                    self.best_score_delta = msg.retrieve()[2][int(self.get_name())][1]
                self._cur_state = "EpochStart"

            elif msg.retrieve()[0] == "Move" :
                if self.get_name() not in str(msg.retrieve()[1]) :
                    self._cur_state = "Move"
                else :
                    self._cur_state = "Wait"

            elif msg.retrieve()[0] == "Bumped" :
                self.colli_msg = msg
                self._cur_state = "Bumped"
                                
                

    def output(self) :
        if self.get_cur_state() == "EpochStart" :
            pass
            
        elif self.get_cur_state() == "Move" :
            if self.escaped == 1 :
                pass
            else :
                # 문까지 갔나 확인하기
                if self.location == self.end_point :
                    self.score_delta[-1] += 1000
                    self.escaped = 1
                    return self.epoch_end_process()

                if len(self.move_log) == self.max_move :
                    return self.epoch_end_process()
                selection_len = len(self.next_decision_arr)
                # 어디로 갈지 선택하기
                if len(self.move_log) == 0 :
                    self.current_decision = self.make_choice(0, selection_len)
                else :
                    self.current_decision = self.make_choice(len(self.move_log) - 1, selection_len)
                # 이동하기
                self.move_location()                
                # 그리드 세계 밖으로 나갔나 확인하기
                out_of_range_msg = self.out_of_range_check()
                if out_of_range_msg is not None :
                    return out_of_range_msg
                    
                
                
                    
        elif self.get_cur_state() == "MoveCheck" :
            # 이동 횟수 다했나 확인
            if len(self.move_log) >= self.max_move :
                    return self.epoch_end_process()
            
        elif self.get_cur_state() == "Bumped" :
            colli_arr = self.colli_msg.retrieve()[1]
            if len(colli_arr) != 0 :
                for group in colli_arr :
                    for name in group :
                        if str(name) == self.get_name() :
                            colli_location = deepcopy(self.location)
                            # 얘가 부딛친 애면 이전 위치로 이동
                            if len(self.location_log) <= 1 :
                                self.location = deepcopy(self.old_location)
                            else : self.location = self.location_log[-2]
                            if len(self.score_delta) == 0 :
                                self.score_delta.append(-50)
                            else : 
                                self.score_delta[-1] -= 50
                            if self.current_decision in self.next_decision_arr :
                                del self.next_decision_arr[self.next_decision_arr.index(self.current_decision)]                                
                            

                            # 굳이 지울필요 있나..?
                            for i in range(len(self.location_log) - 1, -1, -1) :
                                if self.location_log[i] == colli_location :
                                    del self.location_log[i]
                                    del self.move_log[i]
                                    break
                            

                            random_percent = random()
                            if random_percent <= 0.8 :
                                self.next_decision_arr = [4]
                                # 80% 확률로 멈춤
                            # self.next_decision_arr = list(set(self.next_decision_arr))
                


    def int_trans(self) :
        if self.get_cur_state() == "EpochStart" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Move" :
            self._cur_state = "MoveCheck"
        elif self.get_cur_state() == "MoveCheck" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Wait" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Bumped" :
            self._cur_state = "Wait"
        if self.escaped == 1 :
            self._cur_state = "Wait"

            