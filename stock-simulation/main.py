import sys
import argparse
import time
import random
import signal
from matplotlib import pyplot as plt

import log as logging
import agent
import factory
import constants
from market import get_market, reset_market


LOG = logging.getLogger(__name__)

sim = None


class Simulation(object):

    def __init__(self,
                 number_of_transactions=10,
                 number_of_agentN=100,
                 number_of_agentD=100,
                 mu=0,
                 sigma=2):
        reset_market()
        self.agentNs = factory.AgentFactory(agent.AgentN, number_of_agentN,
                                            agent_name="Agent-N")
        self.agentDs = factory.AgentFactory(agent.AgentD, number_of_agentD,
                                            agent_name="Agent-D")
        self._number_of_transactions = number_of_transactions
        self._number_of_agentN = number_of_agentN
        self._number_of_agentD = number_of_agentD
        self._mu = mu
        self._sigma = sigma
        self._Kn_list = []
        self.market = get_market()
        LOG.info("****************************************")
        LOG.info("Intializing...")
        LOG.debug("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_assets))
        LOG.info("Total stocks in the market is: {}, maximum stocks allowed in market is: {}.".format(
            self.agentNs.total_assets + self.agentDs.total_assets,
            self._number_of_agentN+self._number_of_agentD))

        LOG.info("****************************************")

    def _simulate(self, noise, price, delta=0.01, max_iteration=10000):
        LOG.debug("Factory {} has {} stocks".format(self.agentNs.name,
                                                    self.agentNs.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentDs.name,
                                                    self.agentDs.total_assets))
        LOG.info("Noise is {}".format(noise))
        # number of external agents
        action = self._action(noise)

        if action == "buy" and self.agentNs.total_assets == 0:
            LOG.warn("No one wants to sell stocks/bitcoins in market.")
            return None
        if action == "sell" and \
           self.agentNs.total_assets == self.agentNs.length:
            LOG.warn("No one wants to buy stocks/bitcoins in market.")
            return None

        state = constants.STATE_WANT_TO_BUY \
            if action == "buy" else constants.STATE_WANT_TO_SELL

        agentEs = factory.AgentFactory(agent.AgentE, abs(noise),
                                       agent_name="Agent-E",
                                       state=state)
        for agente in agentEs:
            getattr(agente, action)(price)

        LOG.debug("Number of buyer in market: {}".format(self.market.number_of_buyers))
        LOG.debug("Number of seller in market: {}".format(self.market.number_of_sellers))
        delta = self._direction(action) * delta
        iteration = 0
        curr_diff, price = self._jump_to_next_unstable_price(price, action)
        _Kn = []
        while True:
            iteration += 1
            if iteration >= max_iteration:
                LOG.error("Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(max_iteration, price))
                return None

            if iteration % 1000 == 0:
                LOG.info("Iteration #{}: price {}.".format(iteration, price))
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
                LOG.info("#{} agents want to buy stocks".format(
                    self.market.number_of_buyers))
                LOG.info("#{} agents want to sell stocks".format(
                    self.market.number_of_sellers))

            price += delta
            prev_diff = curr_diff
            curr_diff = self._ballot(price)

            _Kn.append(self.agentNs.total_assets + self.agentDs.total_assets + curr_diff)

            if self.market.exchange(price) or \
               self._check_stable_price(prev_diff, curr_diff):
                LOG.debug("Exchange stocks/bitcoins successfully.")
                LOG.info("Iteration #{}, reach stability price: {}".format(
                    iteration, price))
                break

        LOG.debug("Factory {} has {} stocks".format(self.agentNs.name,
                                                    self.agentNs.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentDs.name,
                                                    self.agentDs.total_assets))
        LOG.info("Total assets in market is {}".format(self._total_assets))

        self._Kn_list.append((_Kn, action))
        return price

    def simulate(self, delta=0.001, max_iteration=50000):
        start = time.time()
        LOG.info("****************************************")
        LOG.info("Start to simulate...")
        LOG.info("****************************************")
        noise = self._generate_noise()
        _action = self._action(noise)
        price = 0 if _action == "buy" else 1
        self.market.prices.append(price)
        i = 0
        while i < self._number_of_transactions:
            _price = price
            _noise = noise
            _action = self._action(_noise)
            LOG.info("Round #{} ACTION: {}, PRICE: {}, DELTA: {}".format(
                i, _action, _price, delta))
            price = self._simulate(_noise, _price, delta, max_iteration)

            noise = self._generate_noise()
            if price is None:
                # Flip action
                while self._action(noise) == _action:
                    noise = self._generate_noise()
                price = self.market.prices[-1]
            else:
                i += 1

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))
        LOG.info("****************DONE********************")
        LOG.info("****************************************")

    def _check_stable_price(self, t1, t2):
        return True if t1 * t2 <= 0 else False

    def _generate_noise(self):
        """Generate external agents from gaussian distribution. This function ensures
        the number of external agnets must be integral and non-zero"""
        if not getattr(self, "_generator", None):
            self.noise_generator(random.normalvariate, self._mu, self._sigma)

        _noise = 0

        while _noise == 0:
            _noise = round(self._generator(*self._generator_args, **self._generator_kwargs))
        return int(_noise)

    def noise_generator(self, generator, *args, **kwargs):
        self._generator = generator
        self._generator_args = args
        self._generator_kwargs = kwargs

    def _action(self, noise):
        """Return the action of external agents take. If noise is less than 0,
        the stocks/bitcoins in market will decrease. In other word, external
        agents take action `buy`."""
        if noise < 0:
            return "buy"
        elif noise > 0:
            return "sell"
        else:
            return None

    @property
    def _total_assets(self):
        """Total assets(stocks/bitcoins) in market."""
        return self.agentDs.total_assets + self.agentNs.total_assets

    def _direction(self, action):
        """If action is `buy` the price should go up, the direction of trend is
        positive. And action `sell` the price should go down, the direction of
        trend is negative.
        --------
        Parameters:
        action: only could be `buy` or `sell`
        Returns: 1 if action is `buy`, 0 if action is `sell`
        """
        return 1 if action == "buy" else -1

    def _ballot(self, price):
        """All agents in market ballot for given price. The `diff` between
        the number of seller and the number of buyer is what we are interested.
        Since it indicates how many stocks/bitcoins are bought/sold from/to
        the markets.
        --------
        Parameter:
        price: the price of stocks/bitcoins
        Returns: difference of #buyers and #sellers, it's integral.
        """

        for agentn in self.agentNs:
            try:
                if agentn.state == constants.STATE_WANT_TO_BUY:
                    agentn.buy(price)
                elif agentn.state == constants.STATE_WANT_TO_SELL:
                    agentn.sell(price)
            except AssertionError:
                pass

        for agentd in self.agentDs:
            try:
                if agentd.state == constants.STATE_WANT_TO_BUY:
                    agentd.buy(price)
                elif agentd.state == constants.STATE_WANT_TO_SELL:
                    agentd.sell(price)
            except AssertionError:
                pass
        diff = self.market.number_of_buyers - self.market.number_of_sellers

        return int(round(diff))

    def _jump_to_next_unstable_price(self, price, action, delta=0.001):
        diff = 0
        direction = self._direction(action)
        delta = direction * delta
        i = 0
        while diff == 0:
            diff = self._ballot(price)
            price += delta
            i += 1
            if i % 1000 == 0:
                LOG.info("{} iterations passed.".format(i))
                LOG.info("Diff: {}, Price: {}".format(diff, price))

        return diff, price

    def plot_price(self):
        timestamp = range(len(self.market.prices))
        plt.plot(timestamp, self.market.prices)
        plt.xlabel("timestamp")
        plt.ylabel("price")

    def _plot_kn(self, _Kn, action):
        x = range(len(_Kn))
        color = "green" if action == "buy" else "red"
        plt.plot(x, _Kn, color=color, label=action)
        plt.legend()
        plt.show()

    def plot_Kn(self):
        start = 0
        for _Kn, action in self._Kn_list:
            x = range(start, start+len(_Kn), 1)
            color = "green" if action == "buy" else "red"
            plt.plot(x, _Kn, color=color)
            start = len(_Kn) + start - 1

        plt.xlabel("timestamp")
        plt.ylabel("Kn")

    def plot(self):
        plt.subplot(2, 1, 1)
        self.plot_Kn()
        plt.subplot(2, 1, 2)
        self.plot_price()

    def show_plot(self):
        plt.show()


def handler(signum, frame):
    LOG.info("Catch signal")
    global sim
    if sim is not None:
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
                        default=100)
    parser.add_argument("--number-of-agentD", dest="number_of_agentD",
                        required=False, type=int,
                        default=25)
    parser.add_argument("--mu", dest="mu",
                        required=False, type=float,
                        default=0)
    parser.add_argument("--sigma", dest="sigma",
                        required=False, type=float,
                        default=2)

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
    global sim
    sim = Simulation(number_of_transactions,
                     number_of_agentN=number_of_agentN,
                     number_of_agentD=number_of_agentD,
                     mu=mu,
                     sigma=sigma)
    sim.simulate(0.001, 30000)
    LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
                                                       sim.market.prices))
    sim.plot()
    sim.show_plot()
