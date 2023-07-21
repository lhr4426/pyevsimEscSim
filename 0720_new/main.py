from pyevsim import Infinite, SystemSimulator
import GameModel

if __name__ == "__main__" :
    ss = SystemSimulator()
    # 테스트용으로 현실시간기준으로 함
    engine = ss.register_engine("main_engine", "VIRTUAL_TIME", 1)
    engine.insert_input_port("start")

    game = GameModel.GameModel(instance_time = 0, destruct_time = Infinite, 
                               name='game', engine_name='main_engine', map_size = 10, 
                               agent_count = 3, max_epoch = 10, 
                               max_move = 50, random_percent = 0.5)
    
    engine.register_entity(game)

    engine.coupling_relation(None, "start", game, "start")
    engine.insert_external_event("start", None)

    engine.simulate()