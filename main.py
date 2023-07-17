from pyevsim import Infinite, SystemSimulator
import GameModel

if __name__ == "__main__" :
    ss = SystemSimulator()
    engine = ss.register_engine("main_engine", "VIRTUAL_TIME", 1)
    engine.insert_input_port("start")

    game = GameModel.GameModel(0, Infinite, 'game', 'main_engine', 10)
    engine.register_entity(game)

    engine.coupling_relation(None, "start", game, "start")
    engine.insert_external_event("start", None)

    engine.simulate()