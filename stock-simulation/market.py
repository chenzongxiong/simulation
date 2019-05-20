import time
import log as logging
import constants
import agent
import colors

LOG = logging.getLogger(__name__)


class Market(object):

    def __init__(self):

        self._prices = []
        self._agents = {}
        self._buying_agents = 0
        self._selling_agents = 0
        self._buying_agentDs = 0
        self._selling_agentDs = 0
        self._buying_agentNs = 0
        self._selling_agentNs = 0

        self._delta_price = 0

    def publish(self, instance, func_name, *args):
        """An agent can publish its action to a market by calling this function
        --------
        Parameters:
        instance: instance of an agent
        func_name: function name of an agent wants to invoke
        *args: arguments of function invoked by instance
        """
        self._delta_price = args[0]
        # XXX: Not thread-safe
        if "buy" in func_name:
            self._buying_agents += 1
            if isinstance(instance, agent.AgentN):
                self._buying_agentNs += 1
            elif isinstance(instance, agent.AgentD):
                self._buying_agentDs += 1
        elif "sell" in func_name:
            self._selling_agents += 1
            if isinstance(instance, agent.AgentN):
                self._selling_agentNs += 1
            elif isinstance(instance, agent.AgentD):
                self._selling_agentDs += 1
        # import ipdb; ipdb.set_trace()
        _metadata = {"func_name": func_name,
                     "args": args}
        self._agents[instance.name] = (instance, _metadata)

    def exchangable(self):
        # NOTE: the condition to judge whether it's exchangable or not
        # are not the same as the situation in real world
        if self._buying_agents != self._selling_agents:
            return False
        else:
            return True

    def restore(self):
        # TODO: remove the following part and return the result directly.
        # need to refactor code
        # import ipdb; ipdb.set_trace()
        _price = self._delta_price

        LOG.debug(colors.red("Intra-Transaction failed at price: {:.3f}.".format(self._delta_price)))
        LOG.debug("Before restoring, number of buyers is: {} and number of sellers is: {}".format(self.number_of_buyers, self.number_of_sellers))
        LOG.debug("Before restoring, number of buyers (no agentEs) is: {} and number of sellers(no agentEs) is: {}".format(self._buying_agentDs + self._buying_agentNs,
                                                                                                                           self._selling_agentDs + self._selling_agentNs))
        if self._buying_agentDs > 0 or self._selling_agentDs > 0:
            LOG.debug(colors.green("Before restoring, sellers of AgentD is {}, buyers of AgentD is {} <<<<<<<>>>>>>> sellers of AgentN is {}, buyers of AgentN is {}, price: {:.3f}".format(
                self._selling_agentDs, self._buying_agentDs, self._selling_agentNs, self._buying_agentNs, _price)))
        else:
            LOG.debug(colors.purple("Before restoring, sellers of AgentD is {}, buyers of AgentD is {} <<<<<<<>>>>>>> sellers of AgentN is {}, buyers of AgentN is {}, price: {:.3f}".format(
                self._selling_agentDs, self._buying_agentDs, self._selling_agentNs, self._buying_agentNs, _price)))

        keys_to_delete = []
        for _agent_name, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            if not isinstance(_agent, agent.AgentE):
                keys_to_delete.append(_agent_name)
        for key in keys_to_delete:
            if self._agents[key][0].state == constants.STATE_WANT_TO_BUY:
                self._buying_agents -= 1
                if isinstance(self._agents[key][0], agent.AgentN):
                    self._buying_agentNs -= 1
                elif isinstance(self._agents[key][0], agent.AgentD):
                    self._buying_agentDs -= 1
                    self._agents[key][0].fallback()
            elif self._agents[key][0].state == constants.STATE_WANT_TO_SELL:
                self._selling_agents -= 1
                if isinstance(self._agents[key][0], agent.AgentN):
                    self._selling_agentNs -= 1
                elif isinstance(self._agents[key][0], agent.AgentD):
                    self._selling_agentDs -= 1
                    self._agents[key][0].fallback()
            del self._agents[key]
        LOG.debug("After restoring, number of buyer is: {} and number of seller is: {}".format(self.number_of_buyers, self.number_of_sellers))
        LOG.debug(colors.purple("After restoring, sellers of AgentD is {}, buyers of AgentD is {}, sellers of AgentN is {}, buyers of AgentN is {}".format(
            self._selling_agentDs, self._buying_agentDs, self._selling_agentNs, self._buying_agentNs)))

        # sanity checking
        # self._buying_agents = 0
        # self._selling_agents = 0
        # for _, _agent_with_meta in self._agents.items():
        #     _agent = _agent_with_meta[0]
        #     assert isinstance(_agent, agent.AgentE)
        #     if _agent.state == constants.STATE_WANT_TO_BUY:
        #         self._buying_agents += 1
        #     else:
        #         self._selling_agents += 1

    def exchange(self, price):
        """A market is responsible to help agents to exchanged their stocks
        and notifies agents as long as the transactions complete.
        --------
        Parameters:
        price: price of stock/bitcoin in current transaction."""

        self._prices.append(price)
        for _agent_name, _agent_with_meta in self._agents.items():
            _agent, _meta = _agent_with_meta[0], _agent_with_meta[1]
            func_name = _meta['func_name']
            args = _meta['args']
            getattr(_agent, func_name)(*args)

        LOG.info(colors.purple("sellers of AgentD is {}, buyers of AgentD is {}, sellers of AgentN is {}, buyers of AgentN is {}".format(
            self._selling_agentDs, self._buying_agentDs, self._selling_agentNs, self._buying_agentNs)))
        LOG.info(colors.cyan("Exchange stocks at price {:.3f}, prev-prices for {:.3f}, {} buying agents and {} selling agents successfully.".format(price,
                                                                                                                                                    self._prices[-2],
                                                                                                                                                    self._buying_agents,
                                                                                                                                                    self._selling_agents)))

        # This transcation is successful, reset intermediate information for next transaction
        self.reset()

    @property
    def prices(self):
        return self._prices

    def reset(self):
        self._agents = {}
        self._buying_agents = 0
        self._selling_agents = 0
        self._buying_agentDs = 0
        self._buying_agentNs = 0
        self._selling_agentDs = 0
        self._selling_agentNs = 0

    def cleanup(self, price):
        pass
    @property
    def number_of_buyers(self):
        return self._buying_agents

    @property
    def number_of_sellers(self):
        return self._selling_agents


market = None


def get_market(name=None):
    """During the simulation, ensure that there is only one market.
    This function isn't thread-safe. To set up agents cocurrently,
    it's important to make variable `market` singleton"""

    global market
    if market is None:
        market = Market()

    return market


def reset_market():
    global market
    market = None
