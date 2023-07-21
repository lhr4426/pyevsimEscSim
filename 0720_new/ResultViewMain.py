from pyevsim import Infinite, SystemSimulator
import ResultViewer

if __name__ == "__main__" :
    ss = SystemSimulator()
    # 테스트용으로 현실시간기준으로 함
    engine = ss.register_engine("main_engine", "REAL_TIME", 1)
    engine.insert_input_port("start")

    rv = ResultViewer.ResultViewer(instance_time = 0, destruct_time = Infinite, 
                               name='game', engine_name='main_engine', map_size = 10, 
                               file_path="Result.json",agent_count = 3)
    
    engine.register_entity(rv)

    engine.coupling_relation(None, "start", rv, "start")
    engine.insert_external_event("start", None)

    engine.simulate()