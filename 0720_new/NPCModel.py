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
        self.move_log = [[]] # 움직인 로그 저장용
        self.score_log = [[]] # 한 움직임에 대한 점수 변화 결과 저장
        self.escaped_log = [] # 해당 에포크에서 나갔나 안나갔나 저장
        self.score = 500 # 스코어 500에서 시작
        self.old_location = [] # 이전 위치를 저장 (나중에 충돌났을때 이전 위치로 돌리고 멈추게 하려고)
        self.end_point = end_point
        # 멈춘다는 선택을 직접적으로는 못하게 할것
        # 나중에 부딛쳤다는 내용 뜨면 그때 할거임
        self.next_decision_arr = [0, 1, 2, 3]
        # 지금까지중에 최종 점수가 높게 나왔던 move log임
        self.best_move_arr = []
        self.best_score_arr = []
        self.best_escaped = 0
        self.best_score = 999
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
        self.start_location = self.location = [randint(0, self.map_size - 1), randint(0, self.map_size - 1)]
        return self.location
    
    def get_best_arr(self) -> None:
        '''
        가장 좋았던 epoch의 move_log를 best_arr로 지정함.   
        조건 1. 점수가 높을 것
        조건 2. 점수가 같다면 회수가 더 낮은것 고를 것
        '''
        temp_best_idx = 0
        for i in range(len(self.move_log) - 1) :
            if self.score_log[i][-1] > self.score_log[temp_best_idx][-1] :
                temp_best_idx = i
            elif self.score_log[i][-1] == self.score_log[temp_best_idx][-1] :
                if len(self.move_log[i]) < len(self.move_log[temp_best_idx]) :
                    temp_best_idx = i
        self.best_move_arr = self.move_log[temp_best_idx]
        self.best_score_arr = self.score_log[temp_best_idx]
        self.best_escaped = self.escaped_log[temp_best_idx]
        self.best_score = self.best_score_arr[-1]
    


    def move_location(self) :
        print(f"current decision : {self.current_decision}")
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

        self.move_log[self.epoch].append(self.current_decision)
        
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
        if self.location[0] < 0 or self.location[0] > self.map_size - 1 or self.location[1] < 0 or self.location[1] > self.map_size - 1 :
            self.location = self.old_location
            self.score -= 50
            if self.current_decision in self.next_decision_arr :
                del self.next_decision_arr[self.next_decision_arr.index(self.current_decision)]
            # 다음 결정에서는 다른 선택을 하도록, 방금 전에 한 선택을 뺌

        # 이동했을때 위치가 이상하지 않음
        else :
            self.score -= 1
            self.next_decision_arr = [0,1,2,3] 
            self.remove_opposite_moving()
            # 이번 선택의 반대편을 제외한 모든 선택 중 고를 수 있도록 함
        self.score_log[self.epoch].append(self.score)
        
        print(f"current epoch : {self.epoch}")
        print(f"score log : {self.score_log[self.epoch]}")
        print(f"move log : {self.move_log[self.epoch]}")
        # print(f"current score : {self.score}")
        # print(f"current decision : {self.current_decision}")

    def make_choice(self,index, decision_len) -> int :
        '''
        만약에 이번이 첫 epoch가 아니면, 지금까지 있던 epoch 중에서  
        이번 차례에 가장 좋았던 선택 vs 랜덤 선택을 확률적으로 시킴
        '''
        random_decision = randint(0, decision_len - 1)
        if self.epoch != 0 and index < len(self.best_move_arr):
            best_decision = self.best_move_arr[index]
            random_percent = random()
            # 주어진 확률로 더 좋은 선택을 함
            if random_percent <= self.random_percent :
                return best_decision
            else :
                return self.next_decision_arr[random_decision]
        else :
            return self.next_decision_arr[random_decision]
            
    def epoch_end_process(self) -> SysMessage:
        self.escaped_log.append(self.escaped)
        self.get_best_arr()

        msg = SysMessage(self.get_name(), "NPC2GAME")
        msg.insert("epoch_end")
        msg.insert(self.get_name())
        return msg

        

    def ext_trans(self, port, msg) :
        if port == "GAME2NPC" :
            if msg.retrieve()[0] == "EpochStart" :
                if self.move_log[-1] != [] :
                    self.move_log.append([])
                    self.score_log.append([])

                self.epoch = msg.retrieve()[1]
                self.escaped = 0
                self.score = 500
                self.location = self.start_location
                self._cur_state = "EpochStart"

            elif msg.retrieve()[0] == "Move" :
                if self.get_name() not in str(msg.retrieve()[1]) :
                    self._cur_state = "Move"
                else :
                    self._cur_state = "Wait"

            elif msg.retrieve()[0] == "Bumped" :
                colli_arr = msg.retrieve()[1]
                if len(colli_arr) != 0 :
                    for group in colli_arr :
                        for name in group :
                            if str(name) == self.get_name() :
                                # 얘가 부딛친 애면 이전 위치로 이동하고 점수 50점 뺌
                                self.location = self.old_location
                                if len(self.score_log[-1]) != 0 :
                                    self.score_log[-1][-1] -= 50
                                self.score -= 50
                                if self.current_decision in self.next_decision_arr :
                                    del self.next_decision_arr[self.next_decision_arr.index(self.current_decision)]
                                self.next_decision_arr.append(4)
                                # 방금 한 선택을 지워버리고 멈춘다는 선택지를 넣음
                

    def output(self) :
        if self.get_cur_state() == "EpochStart" :
            pass
        
        elif self.get_cur_state() == "Move" :
            print(f"Next Decision Array : {self.next_decision_arr}")
            if self.escaped == 1 :
                pass
            else :
                if len(self.move_log[self.epoch]) == self.max_move :
                    return self.epoch_end_process()
                selection_len = len(self.next_decision_arr)
                # 어디로 갈지 선택하기
                if len(self.move_log[self.epoch]) == 0 :
                    self.current_decision = self.make_choice(0, selection_len)
                else :
                    self.current_decision = self.make_choice(len(self.move_log[self.epoch]) - 1, selection_len)
                # 이동하기
                self.move_location()                
                # 그리드 세계 밖으로 나갔나 확인하기
                self.out_of_range_check()
                # 문까지 갔나 확인하기
                if self.location == self.end_point :
                    self.score_log[self.epoch][len(self.score_log[self.epoch]) - 1] += 100
                    self.escaped = 1
                    return self.epoch_end_process()
                    
        elif self.get_cur_state() == "MoveCheck" :
            # 이동 횟수 다했나 확인
            if len(self.move_log[self.epoch]) >= self.max_move :
                    return self.epoch_end_process()
            
            
    def int_trans(self) :
        if self.get_cur_state() == "EpochStart" :
            self._cur_state = "Wait"
        if self.get_cur_state() == "Move" and self.escaped == 0:
            self._cur_state = "MoveCheck"
        elif self.get_cur_state() == "Move" and self.escaped == 1:
            self._cur_state = "Wait"
        elif self.get_cur_state() == "MoveCheck" :
            self._cur_state = "Wait"
        elif self.get_cur_state() == "Wait" :
            self._cur_state = "Wait"

            