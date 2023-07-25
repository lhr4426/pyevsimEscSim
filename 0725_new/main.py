from pyevsim import Infinite, SystemSimulator
import GameModel
import ResultViewer

if __name__ == "__main__" :
    ss = SystemSimulator()
    # 테스트용으로 현실시간기준으로 함
    engine = ss.register_engine("main_engine", "VIRTUAL_TIME", 1)
    engine.insert_input_port("start")

    map_size = 10
    agent_count = 2
    max_epoch = 50
    max_move = 50
    random_percent = 0.75

    game = GameModel.GameModel(instance_time = 0, destruct_time = Infinite, 
                               name='game', engine_name='main_engine', map_size = map_size, 
                               agent_count = agent_count, max_epoch = max_epoch, 
                               max_move = max_move, random_percent = random_percent)
    
    engine.register_entity(game)

    engine.coupling_relation(None, "start", game, "start")

    viewer = ResultViewer.ResultViewer(0, Infinite, name='viewer', 
                                       engine_name='main_engine', map_size=map_size,
                                       agent_count=agent_count)

    engine.register_entity(viewer)
    engine.coupling_relation(game, "GAME2VIEWER", viewer, "GAME2VIEWER")

    engine.insert_external_event("start", None)

    engine.simulate()