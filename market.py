import pickle


class Market(object):
    def __init__(self):
        pass


class StockMarket(Market):

    def __init__(self):
        self.selling_agents = {}
        self.buying_agents = {}
        self.transactions = []

        self.timestamp - 1
        self.prices = []

    def poll_selling(self, serialized_data):
        deserialized_data = pickle.loads(serialized_data)
        name, _agent = deserialized_data[0], deserialized_data[1]
        assert name not in self.selling_agents.keys()

        self.selling_agents[name] = _agent
        # TODO: poll selling, spawn a new thread and let agent polls selling
        # self.selling_agents.pop(name)
        self._poll_selling(_agent)

    def poll_buying(self, serialized_data):
        deserialized_data = pickle.loads(serialized_data)
        name, _agent = deserialized_data[0], deserialized_data[1]
        assert name not in self.buying_agents.keys()

        self.buying_agents[name] = _agent
        # TODO: poll buying, spawn a new thread and let agent polls buying
        # self.buying_agents.pop(name)

    def _poll_selling(self, _agent, price):
        while True:
            # price = self.prices[self.timestamp]
            try:
                _agent.sell(price)
                LOG.info("{} sells a stock/bitcoin at price {} successfully.".format(agent.name, price))
                break
            except AssertionError:
                LOG.info("{} could not sell a stock/bitcoin at price {}. {}".format(_agent.name, price, _agent.__repr__()))
            # TODO: sleeping until `timestamp` updates

    def _poll_buying(self, _agent, price):
        while True:
            # price = self.prices[self.timestamp]
            try:
                _agent.buy(price)
                LOG.info("{} buys a stock/bitcoin at price {} successfully.".format(_agent.name, price))
                break
            except AssertionError:
                LOG.info("{} could not buy a stock/bitcoin at price {}. {}".format(_agent.name, price, _agent.__repr__()))
            # TODO: sleeping until `timestamp` updates
