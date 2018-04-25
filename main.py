import log as logging
import agent
import factory
import constants
from market import get_market


LOG = logging.getLogger(__name__)


def simulation_buying():
    agentn_factory = factory.AgentFactory(agent.AgentN, 20,
                                          agent_name="Agent-N")
    agentd_factory = factory.AgentFactory(agent.AgentN, 20,
                                          agent_name="Agent-D")

    LOG.debug("Intializing...")
    LOG.debug("Factory {} has {} stocks".format(agentn_factory.name, agentn_factory.total_stocks()))
    LOG.debug("Factory {} has {} stocks".format(agentd_factory.name, agentd_factory.total_stocks()))
    LOG.debug("Total stocks in the market is: {}".format(agentn_factory.total_stocks() + agentd_factory.total_stocks()))
    LOG.debug("--------------------------------------------")

    market = get_market()
    price = 0
    delta = 0.001

    # while True:
    agente_factory = factory.AgentFactory(agent.AgentE, 5,
                                          agent_name="Agent-E")

    LOG.debug("Factory {} has {} stocks".format(agente_factory.name, agente_factory.total_stocks()))
    LOG.debug("{} agents of factory {} want to buy stocks".format(agente_factory.name,
                                                                  len(agente_factory.agents) - agente_factory.total_stocks()))
    for agente in agente_factory:
        try:
            agente.buy(price)
        except AssertionError:
            pass

    LOG.debug("{} agents want to buy stocks".format(len(market._buying_agents)))
    LOG.debug("{} agents want to sell stocks".format(len(market._selling_agents)))
    while True:
        for agentn in agentn_factory:
            try:
                if agentn.state == constants.STATE_WANT_TO_BUY:
                    agentn.buy(price)
                elif agentn.state == constants.STATE_WANT_TO_SELL:
                    agentn.buy(price)
            except AssertionError:
                pass

        for agentd in agentd_factory:
            try:
                if agentd.state == constants.STATE_WANT_TO_BUY:
                    agentd.buy(price)
                elif agentd.state == constants.STATE_WANT_TO_SELL:
                    agentd.sell(price)
            except AssertionError:
                pass

        LOG.debug("{} agents want to buy stocks".format(len(market._buying_agents)))
        LOG.debug("{} agents want to sell stocks".format(len(market._selling_agents)))

        if market.exchange(price):
            break

        price += delta

if __name__ == "__main__":
    simulation_buying()
