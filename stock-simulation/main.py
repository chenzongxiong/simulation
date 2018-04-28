import sys
import time
import random

import log as logging
import agent
import factory
import constants
from market import get_market, reset_market


LOG = logging.getLogger(__name__)


class Simulation(object):

    def __init__(self,
                 number_of_transactions=10,
                 number_of_agentN=100,
                 number_of_agentD=100,
                 mu=0,
                 sigma=2):
        # seed = 1: counldnot produce sound result`
        reset_market()
        self.agentNs = factory.AgentFactory(agent.AgentN, number_of_agentN,
                                            agent_name="Agent-N")
        self.agentDs = factory.AgentFactory(agent.AgentD, number_of_agentD,
                                            agent_name="Agent-D")
        self._number_of_transactions = number_of_transactions
        self._number_of_agentN = number_of_agentN
        self._number_of_agentD = number_of_agentD
        self._sigma = sigma
        self.market = get_market()
        LOG.info("****************************************")
        LOG.info("Intializing...")
        LOG.debug("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_assets))
        # for agentd in self.agentDs:
        #     LOG.info(agentd)
        # for agentn in self.agentNs:
        #     LOG.info(agentn)
        LOG.info("Total stocks in the market is: {}, maximum stocks allowed in market is: {}.".format(
            self.agentNs.total_assets + self.agentDs.total_assets,
            self._number_of_agentN+self._number_of_agentD))

        LOG.info("****************************************")

    def _simulate(self, noise, price, delta=0.01, max_iteration=10000):
        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_assets))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_assets))
        LOG.info("Noise is {}".format(noise))
        # number of external agents
        action = self._action(noise)

        if action == "buy" and self.agentNs.total_assets == 0:
            LOG.warn("No one wants to sell stocks/bitcoins in market.")
            sys.exit(1)
        if action == "sell" and \
           self.agentNs.total_assets == self.agentNs.length:
            LOG.warn("No one wants to buy stocks/bitcoins in market.")
            sys.exit(1)

        state = constants.STATE_WANT_TO_BUY \
            if action == "buy" else constants.STATE_WANT_TO_SELL

        agentEs = factory.AgentFactory(agent.AgentE, abs(noise),
                                       agent_name="Agent-E",
                                       state=state)
        for agente in agentEs:
            getattr(agente, action)(price)

        LOG.info("Number of buyer in market: {}".format(self.market.number_of_buyers))
        LOG.info("Number of seller in market: {}".format(self.market.number_of_sellers))
        # TODO: Here should be another check
        delta = self._direction(action) * delta
        iteration = 0
        # price += delta
        curr_diff, price = self._jump_to_next_unstable_price(price, action)

        while True:
            price += delta
            prev_diff = curr_diff
            curr_diff = self._ballot(price)

            if self.market.exchange(price):
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
                LOG.info("Iteration #{}, reach stability price: {}".format(
                    iteration, price))
                break
            if self._check_stable_price(prev_diff, curr_diff):
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
                LOG.info("Iteration #{}, reach stability price: {}".format(
                    iteration, price))
                break

            iteration += 1
            if iteration >= max_iteration:
                LOG.error("Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(max_iteration, price))
                sys.exit(1)
            if iteration % 1000 == 0:
                LOG.info("Iteration #{} --> price: {}.".format(iteration, price))
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_assets))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_assets))
        LOG.info("Total assets in market is {}".format(self._total_assets))
        return price

    def simulate(self, action=None, delta=0.00001, max_iteration=1000000):
        start = time.time()
        LOG.info("Start to simulate...")
        noise = self._generate_noise()
        price = 10
        self.market.prices.append(price)
        for i in range(self._number_of_transactions):
            _price = price
            _noise = noise
            _action = self._action(_noise)
            LOG.info("Round #{} ACTION: {}, PRICE: {}, DELTA: {}".format(
                i, _action, _price, delta))
            self._simulate(_noise, _price, delta, max_iteration)
            price = self.market.prices[-1]
            noise = self._generate_noise()

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))
        LOG.info("****************DONE********************")
        LOG.info("****************************************")

    def _check_stable_price(self, t1, t2):
        return True if t1 * t2 <= 0 else False

    def _generate_noise(self):
        """Generate external agents from gaussian distribution. This function ensures
        the number of external agnets must be integral and non-zero
        """
        _noise = 0
        while _noise == 0:
            _noise = round(random.normalvariate(0, self._sigma))
        return int(_noise)

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
        return self.agentDs.total_assets + self.agentNs.total_assets

    def _direction(self, action):
        """If action is `buy` the price should go up, the direction of trend is
        positive. And action `sell` the price should go down, the direction of
        trend is negative."""
        return 1 if action == "buy" else -1

    def _ballot(self, price):
        """All agents in market ballot for given price. The `diff` between
        the number of seller and the number of buyer is what we are interested.
        Since it indicates how many stocks/bitcoins are bought/sold from/to
        the markets."""

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
        LOG.debug("#{} agents want to buy stocks".format(
            self.market.number_of_buyers))
        LOG.debug("#{} agents want to sell stocks".format(
            self.market.number_of_sellers))
        diff = self.market.number_of_buyers - self.market.number_of_sellers

        return diff

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


if __name__ == "__main__":
    number_of_transactions = 5
    LOG.debug("****************************************")
    LOG.debug("**Start to simlualte *buy* #{} transaction".format(number_of_transactions))
    LOG.debug("****************************************")
    random.seed(123)
    sim = Simulation(number_of_transactions,
                     number_of_agentN=50,
                     number_of_agentD=50)
    sim.simulate("buy", 0.0001, 1000000)
    LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
                                                       sim.market.prices))

    # LOG.debug("****************************************")
    # LOG.debug("**Start to simlualte *sell* #{} transaction".format(number_of_transactions))
    # LOG.debug("****************************************")
    # random.seed(1)
    # sim = Simulation(number_of_transactions)
    # sim.simulate("sell", 0.00001, 100000)
    # LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
    #                                                    sim.market.prices))
