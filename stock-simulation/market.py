import time
import log as logging
import constants
import agent

LOG = logging.getLogger(__name__)


class Market(object):

    def __init__(self):

        self._prices = []
        self._agents = {}
        self._buying_agents = 0
        self._selling_agents = 0

    def publish(self, instance, func_name, *args):
        """An agent can publish its action to a market by calling this function
        --------
        Parameters:
        instance: instance of an agent
        func_name: function name of an agent wants to invoke
        *args: arguments of function invoked by instance
        """
        # XXX: Not thread-safe
        if "buy" in func_name:
            self._buying_agents += 1
        elif "sell" in func_name:
            self._selling_agents += 1

        _metadata = {"func_name": func_name,
                     "args": args}
        self._agents[instance.name] = (instance, _metadata)

    def exchangable(self):
        if self._buying_agents != self._selling_agents:
            return False
        else:
            return True

    def restore(self):
        # TODO: remove the following part and return the result directly.
        # need to refactor code
        LOG.debug("Transaction failed.")
        LOG.debug("Before restoring, number of buyer is: {} and number of seller is: {}".format(self.number_of_buyers, self.number_of_sellers))
        keys_to_delete = []
        for _agent_name, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            if not isinstance(_agent, agent.AgentE):
                keys_to_delete.append(_agent_name)
        for key in keys_to_delete:
            del self._agents[key]
        LOG.debug("After restoring, number of buyer is: {} and number of seller is: {}".format(self.number_of_buyers, self.number_of_sellers))
        # sanity checking
        self._buying_agents = 0
        self._selling_agents = 0
        for _, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            assert isinstance(_agent, agent.AgentE)
            if _agent.state == constants.STATE_WANT_TO_BUY:
                self._buying_agents += 1
            else:
                self._selling_agents += 1

    def exchange(self, price):
        """A market is responsible to help agents to exchanged their stocks
        and notifies agents as long as the transactions complete.
        --------
        Parameters:
        price: price of stock/bitcoin in current transaction

        Returns:
        True means current transaction successes.
        Otherwise, current transaction fails."""
        self._prices.append(price)
        for _agent_name, _agent_with_meta in self._agents.items():
            _agent, _meta = _agent_with_meta[0], _agent_with_meta[1]
            func_name = _meta['func_name']
            args = _meta['args']
            getattr(_agent, func_name)(*args)

        LOG.info("Exchange stocks at price %s for all agents successfully." % price)
        # This transcation is successful, reset intermediate information for next transaction
        self.reset()

    @property
    def prices(self):
        return self._prices

    def reset(self):
        self._agents = {}
        self._buying_agents = 0
        self._selling_agents = 0

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
