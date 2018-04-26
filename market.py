import log as logging
import constants
import agent

LOG = logging.getLogger(__name__)


class Market(object):

    def __init__(self):

        self._prices = []
        self._agents = {}

    def publish(self, instance, func_name, *args, **kwargs):
        """An agent can publish its action to a market by calling this function
        --------
        Parameters:
        instance: instance of an agent
        func_name: function name of an agent wants to invoke
        *args: arguments of function invoked by instance
        """
        _metadata = {"func_name": func_name,
                     "args": args}
        self._agents[instance.name] = (instance, _metadata)

    def exchange(self, price):
        """A market is responsible to help agents to exchanged their stocks
        and notifies agents as long as the transactions complete.
        --------
        Parameters:
        price: price of stock/bitcoin in current transaction

        Returns:
        True means current transaction successes.
        Otherwise, current transaction fails."""

        _buying_agents = 0
        _selling_agents = 0
        for _, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            if _agent.state == constants.STATE_WANT_TO_BUY:
                _buying_agents += 1
            elif _agent.state == constants.STATE_WANT_TO_SELL:
                _selling_agents += 1
            else:
                raise

        if _buying_agents != _selling_agents:
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
            for _, _agent_with_meta in self._agents.items():
                _agent = _agent_with_meta[0]
                assert isinstance(_agent, agent.AgentE)
            return False

        LOG.info("Exchange stocks at price %s for all agents successfully." % price)
        self._prices.append(price)
        for _agent_name, _agent_with_meta in self._agents.items():
            _agent, _meta = _agent_with_meta[0], _agent_with_meta[1]
            func_name = _meta['func_name']
            args = _meta['args']
            getattr(_agent, func_name)(*args)

        # This transcation is successful, reset intermediate information for next transaction
        self.reset()
        return True

    @property
    def prices(self):
        return self._prices

    def reset(self):
        self._agents = {}

    @property
    def number_of_buyers(self):
        _buying_agents = 0
        for _, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            if _agent.state == constants.STATE_WANT_TO_BUY:
                _buying_agents += 1
        return _buying_agents

    @property
    def number_of_sellers(self):
        _selling_agents = 0
        for _, _agent_with_meta in self._agents.items():
            _agent = _agent_with_meta[0]
            if _agent.state == constants.STATE_WANT_TO_SELL:
                _selling_agents += 1
        return _selling_agents


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
