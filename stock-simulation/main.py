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
                 number_of_agentn=100,
                 number_of_agentd=100,
                 number_of_agente=3):
        # seed = 1: counldnot produce sound result`
        reset_market()
        self.agentn_factory = factory.AgentFactory(agent.AgentN, number_of_agentn,
                                                   agent_name="Agent-N")
        self.agentd_factory = factory.AgentFactory(agent.AgentD, number_of_agentd,
                                                   agent_name="Agent-D")
        self._number_of_transactions = number_of_transactions
        self._number_of_agente = number_of_agente
        self._number_of_agentn = number_of_agentn
        self._number_of_agentd = number_of_agentd
        self.market = get_market()
        LOG.info("****************************************")
        LOG.info("Intializing...")
        LOG.debug("Factory {} has {} stocks".format(self.agentn_factory.name, self.agentn_factory.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentd_factory.name, self.agentd_factory.total_assets))
        for agentd in self.agentd_factory:
            LOG.info(agentd)
        for agentn in self.agentn_factory:
            LOG.info(agentn)
        LOG.info("Total stocks in the market is: {}, maximum stocks allowed in market is: {}.".format(
            self.agentn_factory.total_assets + self.agentd_factory.total_assets,
            self._number_of_agentn+self._number_of_agentd))

        LOG.info("****************************************")

    def _simulate(self, action, price, delta=0.01, max_iteration=10000):
        assert action in ("buy", "sell")

        if action == "buy" and (self.agentn_factory.total_assets + self.agentd_factory.total_assets == 0):
            LOG.info("No more stocks can be bought from market.")
            sys.exit(1)
        if action == "sell" and \
           (self.agentn_factory.total_assets + self.agentd_factory.total_assets ==
            self._number_of_agentn+self._number_of_agentd):
            LOG.info("No more stocks can be sold to market.")
            sys.exit(1)

        LOG.debug("Factory {} has {} stocks".format(self.agentn_factory.name, self.agentn_factory.total_assets))
        LOG.debug("Factory {} has {} stocks".format(self.agentd_factory.name, self.agentd_factory.total_assets))
        LOG.info("Total stocks in the market is: {}".format(self.agentn_factory.total_assets + self.agentd_factory.total_assets)

        price = price
        delta = delta if action == "buy" else -delta
        agente_factory = factory.AgentFactory(agent.AgentE, self._number_of_agente,
                                              agent_name="Agent-E")
        LOG.debug("Factory {} has {} stocks".format(agente_factory.name, agente_factory.total_assets)
        # LOG.info("{} agents of factory {} want to buy stocks".format(agente_factory.name,
        #                                                              len(agente_factory.agents) - agente_factory.total_assets)
        # LOG.info("{} agents of factory {} want to sell stocks".format(agente_factory.name,
        #                                                               agente_factory.total_assets)

        # if action == "buy" and \
        #    (self.agentn_factory.total_assets < len(agente_factory.agents) - agente_factory.total_assets:
        #     LOG.warn("This transaction must be failed.")
        #     return
        while True:
            LOG.info("{} agents of factory {} want to buy stocks".format(agente_factory.name,
                                                                         len(agente_factory.agents) - agente_factory.total_assets()))
            LOG.info("{} agents of factory {} want to sell stocks".format(agente_factory.name,
                                                                          agente_factory.total_assets)
            if action == "buy" and \
               agente_factory.total_assets() == len(agente_factory.agents):
                agente_factory = factory.AgentFactory(agent.AgentE, self._number_of_agente,
                                                      agent_name="Agent-E")

            elif action == "sell" and \
                 agente_factory.total_assets() == 0:
                agente_factory = factory.AgentFactory(agent.AgentE, self._number_of_agente,
                                                      agent_name="Agent-E")
            else:
                break

        LOG.info("Generate a valid agente-factory.")
        for agente in agente_factory:
            try:
                getattr(agente, action)(price)
            except AssertionError:
                pass

        LOG.debug("#{} agents want to buy stocks".format(self.market.number_of_buyers))
        LOG.debug("#{} agents want to sell stocks".format(self.market.number_of_sellers))
        iteration = 0
        while True:
            # TODO: check the valid of agente-factory, make sure the number of buyer and
            # seller is valid
            price += delta
            if price < 0:
                LOG.error("Price is negative, *INVALID*!!!")
                for agentd in self.agentd_factory:
                    LOG.info(agentd)
                for agentn in self.agentn_factory:
                    LOG.info(agentn)
                sys.exit(1)

            LOG.debug("Current Price is: {}".format(price))
            for agentn in self.agentn_factory:
                try:
                    if agentn.state == constants.STATE_WANT_TO_BUY:
                        agentn.buy(price)
                        LOG.debug("{} want to buy this stock/bitcion at price.".format(agentn, price))
                    elif agentn.state == constants.STATE_WANT_TO_SELL:
                        agentn.sell(price)
                        LOG.debug("{} want to sell this stock/bitcion at price.".format(agentn, price))
                except AssertionError:
                    pass

            for agentd in self.agentd_factory:
                try:
                    if agentd.state == constants.STATE_WANT_TO_BUY:
                        agentd.buy(price)
                        LOG.debug("{} want to buy this stock/bitcion at price.".format(agentd, price))
                    elif agentd.state == constants.STATE_WANT_TO_SELL:
                        agentd.sell(price)
                        LOG.debug("{} want to sell this stock/bitcion at price.".format(agentd, price))
                except AssertionError:
                    pass

            LOG.debug("#{} agents want to buy stocks".format(self.market.number_of_buyers))
            LOG.debug("#{} agents want to sell stocks".format(self.market.number_of_sellers))

            if self.market.exchange(price):
                LOG.info("Iteration #{}, reaching stability, next price is {}".format(iteration,
                                                                                      price))
                break

            iteration += 1
            if iteration >= max_iteration:
                LOG.error("Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(max_iteration, price))
                for agentd in self.agentd_factory:
                    LOG.info(agentd)
                for agentn in self.agentn_factory:
                    LOG.info(agentn)
                sys.exit(1)
            if iteration % 1000 == 0:
                LOG.info("Iteration #{} --> price: {}.".format(iteration, price))

    def _simulate1(self, action, price, delta=0.01, max_iteration=10000):
        # agente = random.normal()
        #
        pass

    def simulate(self, action=None, delta=0.00001, max_iteration=1000000):
        start = time.time()
        LOG.info("Start to simulate...")
        first_action = random.choice(["buy", "sell"]) if action is None else action
        if first_action == "sell":
            price = 1
        elif first_action == "buy":
            price = 0

        self.market.prices.append(price)
        _action = first_action
        for i in range(self._number_of_transactions):
            LOG.info("Round #{} ACTION: {}, PRICE: {}, DELTA: {}".format(i, _action, price, delta))
            _price = price
            if _action == "buy":
                self._simulate(_action, _price, delta, max_iteration)
            elif _action == "sell":
                self._simulate(_action, _price, delta, max_iteration)
            price = self.market.prices[-1]
            _action = random.choice(["buy", "sell"]) if action is None else action

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))
        LOG.info("****************DONE********************")
        LOG.info("****************************************")

    def _check_stable_price(self, t1, t2):
        return True if t1 * t2 <= 0 else False


if __name__ == "__main__":
    number_of_transactions = 5
    LOG.debug("****************************************")
    LOG.debug("**Start to simlualte *buy* #{} transaction".format(number_of_transactions))
    LOG.debug("****************************************")
    random.seed(123)
    sim = Simulation(number_of_transactions,
                     number_of_agentn=100,
                     number_of_agentd=100,
                     number_of_agente=3)
    # sim.simulate("buy", 0.001, 10000)
    sim.simulate("buy", 0.0001, 1000000)
    LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
                                                       sim.market.prices))

    LOG.debug("****************************************")
    LOG.debug("**Start to simlualte *sell* #{} transaction".format(number_of_transactions))
    LOG.debug("****************************************")
    random.seed(1)
    sim = Simulation(number_of_transactions)
    sim.simulate("sell", 0.00001, 100000)
    LOG.info("After #{} simulations, we got {}".format(number_of_transactions,
                                                       sim.market.prices))
