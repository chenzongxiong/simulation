import pickle
import log as logging


LOG = logging.getLogger(__name__)


class Market(object):

    def __init__(self):

        self._buying_agents = []
        self._selling_agents = []
        self._prices = []

    def publish(self, instance, func_name, *args, **kwargs):
        """An agent can publish its action to a market by calling this function
        --------
        Parameters:
        instance: instance of an agent
        func_name: function name of an agent wants to invoke
        *args: arguments of function invoked by instance
        """
        assert func_name in ("buy", "sell"), \
            "Only support to publish `buy` and `sell` actions"

        _serialized = pickle.dumps({"agent": instance,
                                    "func_name": func_name,
                                    "args": args})
        if func_name == "buy":
            self._buying_agents.append(_serialized)
        elif func_name == "sell":
            self._selling_agents.append(_serialized)

    def exchange(self, price):
        """A market is responsible to help agents to exchanged their stocks
        and notifies agents as long as the transactions complete.
        --------
        Parameters:

        """
        assert len(self._buying_agents) == len(self._selling_agents)

        if len(self._buying_agents) > 0:
            """NOTE: Here is roughly checking the price. In fact, during a
            transaction, all buyer and seller should compromise on the same
            price. Or this transaction will fail."""
            assert pickle.loads(self._buying_agents[0])['args'][0] == \
                pickle.loads(self._selling_agents[0])['args'][0]

            assert pickle.loads(self._buying_agents[0])['args'][0] == price
        else:
            LOG.debug("At price %s, no agents want to exchagne stocks." % price)

        LOG.info("Exchange stocks at price %s for all agents successfully." % price)
        self._prices.append(price)
        # This transcation is successful, reset intermediate information for next transaction
        self.reset()

    @property
    def prices(self):
        return self._prices

    def reset(self):
        self._buying_agents = []
        self._selling_agents = []


class StockMarket(Market):
    pass


market = None


def get_market(name=None):
    global market
    if market is None:
        market = Market()

    return market
