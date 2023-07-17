from pyevsim import Infinite, SystemSimulator
import GameModel

if __name__ == "__main__" :
    ss = SystemSimulator()
    # 테스트용으로 현실시간기준으로 함
    engine = ss.register_engine("main_engine", "REAL_TIME", 1)
    engine.insert_input_port("start")

    game = GameModel.GameModel(0, Infinite, 'game', 'main_engine', 10)
    engine.register_entity(game)

    engine.coupling_relation(None, "start", game, "start")
    engine.insert_external_event("start", None)

    engine.simulate()