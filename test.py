'''
중간에 시뮬레이션 시간 모드를 바꿀 수 있나 확인해볼 예정
'''


from pyevsim import BehaviorModelExecutor, SystemSimulator, Infinite, SysMessage

class Tester(BehaviorModelExecutor) :

    def __init__(self, instance_time, destruct_time, name, engine_name) :
        BehaviorModelExecutor.__init__(self, instance_time, destruct_time, name, engine_name)
        self.init_state("Init")
        self.insert_state("Init", Infinite)
        self.insert_state("Print", 1)

        self.insert_input_port("Start")

        self.engine = SystemSimulator.get_engine(self.engine_name)
        self.index = 0

    def ext_trans(self, port, msg):
        if port == "Start" :
            self._cur_state = "Print"
    
    def output(self):
        if self.index == 10 :
            self.engine.sim_mode = "REAL_TIME"
        print(f"{self.index}")
        self.index += 1
        
        
    def int_trans(self):
        if self.get_cur_state() == "Print" :
            self._cur_state = "Print"
    
        

if __name__ == "__main__" :
    ss = SystemSimulator()
    engine = ss.register_engine("main", "VIRTUAL_TIME", 1)
    engine.insert_input_port("Start")

    testModel = Tester(0, Infinite, "tester", "main")
    engine.register_entity(testModel)

    engine.coupling_relation(None, "Start", testModel, "Start")
    engine.insert_external_event("Start", None)
    engine.simulate()