import sys
import argparse
import random
import signal

import log as logging
from simulation import Simulation2

LOG = logging.getLogger(__name__)

sim = None


def handler(signum, frame):
    LOG.info("Catch signal")
    global sim
    if sim is not None:
        LOG.info("After #{} simulations, we got {}".format(sim._curr_num_transactions,
                                                           sim.market.prices))
        sim.plot()
        sim.show_plot()

    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGSEGV, handler)

    parser = argparse.ArgumentParser()

    parser.add_argument("--number-of-transactions", dest="number_of_transactions",
                        required=False, type=int,
                        default=100)
    parser.add_argument("--number-of-agentN", dest="number_of_agentN",
                        required=False, type=int,
                        default=300)
    parser.add_argument("--number-of-agentD", dest="number_of_agentD",
                        required=False, type=int,
                        default=75)
    parser.add_argument("--mu", dest="mu",
                        required=False, type=float,
                        default=0)
    parser.add_argument("--sigma", dest="sigma",
                        required=False, type=float,
                        default=0.5)

    argv = parser.parse_args(sys.argv[1:])

    number_of_transactions = argv.number_of_transactions
    number_of_agentN = argv.number_of_agentN
    number_of_agentD = argv.number_of_agentD
    mu = argv.mu
    sigma = argv.sigma

    LOG.info("****************************************")
    LOG.info("Start to simlualte #{} transaction".format(number_of_transactions))
    LOG.info("Number of Agent N: {}".format(number_of_agentN))
    LOG.info("Number of Agent D: {}".format(number_of_agentD))
    LOG.info("Mean of gaussian distribution: {}".format(mu))
    LOG.info("Standard deriviation of gaussian distribution: {}".format(sigma))
    LOG.info("****************************************")
    sim = Simulation2(number_of_transactions, sigma=sigma)
    sim.simulate(0.01, 10000)
    LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
                                                       sim.market.prices))
    sim.plot()
    sim.show_plot()
