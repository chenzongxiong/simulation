import json
import logging
import random

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.DEBUG)

STATE_WANT_TO_BUY = 0
STATE_WANT_TO_SELL = 1


class BaseAgent(object):

    def __init__(self,
                 state,
                 name="Agent-Base",
                 price=None):
        self._state = state
        self.name = name
        self.price = 0 if state == STATE_WANT_TO_SELL and \
            price is None else price

        # connect to market and perform actions.
        self.connection = None
        self.profits = []

    def buy(self, price):
        """Buy stock/bitcoin from market.
        price: the price of stock/bitcoin at timestamp t
        """
        assert self.buying_signal(price), \
            "{} cannot buy a stock/bitcoin at price {}.\n{}".format(self.name, price,
                                                                    self.__repr__())
        LOG.debug("{} buys a stock/bitconin at price {}.".format(self.name, price))
        if self.price is None:
            self.price = price

        # Switch current state from `STATE_WANT_TO_BUY` to `STATE_WANT_TO_SELL`
        self._state = STATE_WANT_TO_SELL
        # TODO: Emit a signal/message to a pool and wait for others who want to buy.
        # Block until get the data
        # self.connection.get()

    def sell(self, price):
        """Send stock/bitcoin to market.
        price: the value of stock in timestamp t
        """
        assert self.selling_signal(price), \
            "{} cannot sell its stock/bitcoin.\n{}".format(self.name, self.__repr__())
        assert self.price is not None, \
            "{} must buy a stock/bitcoin before selling."

        # TODO: sell this stock
        self.profits.append(price - self.price)

        LOG.debug("{} sells a stock/bitcoin at price {}, and gets profit {}."
                  .format(self.name, price, self.profits[-1]))
        # Reset `price` since we have sold it
        self.price = None
        # Switch current state from `STATE_WANT_TO_SELL` to `STATE_WANT_TO_BUY`
        self._state = STATE_WANT_TO_BUY
        # TODO: Emit a signal/message to a pool and wait for others who want to sell
        # self.connection.push()

    def buying_signal(self, price):
        raise NotImplementedError("buying_signal must be implemented in sub-class.")

    def selling_signal(self, price):
        raise NotImplementedError("selling_signal must be implemented in sub-class.")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def __repr__(self):
        return json.dumps({"name": self.name,
                           "state": self._state,
                           "price": self.price})


class AgentN(BaseAgent):

    def __init__(self,
                 state=random.choice([STATE_WANT_TO_BUY, STATE_WANT_TO_SELL]),
                 lower_bound=random.uniform(0, 1),
                 upper_bound=1+random.gammavariate(1.0, 1.0),
                 name="N-Agent"):
        super(AgentN, self).__init__(state=state, name=name)
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound
        assert self._lower_bound < self._upper_bound, \
            "`lower_bound` must be less than `upper_bound`"

    def buying_signal(self, price):
        return self._state == STATE_WANT_TO_BUY and \
            (self._lower_bound >= price)

    def selling_signal(self, price):
        return self._state == STATE_WANT_TO_SELL and \
            (price >= self._upper_bound)

    def __repr__(self):
        return json.dumps({"name": self.name,
                           "state": self._state,
                           "price": self.price,
                           "lower_bound": self._lower_bound,
                           "upper_bound": self._upper_bound})


class AgentD(BaseAgent):

    def __init__(self,
                 state=random.choice([STATE_WANT_TO_BUY, STATE_WANT_TO_SELL]),
                 buying_threshold=random.gammavariate(1.0, 1.0),
                 selling_threshold=random.gammavariate(1.0, 1.0),
                 name="D-Agent"):
        super(AgentD, self).__init__(state=state, name=name)
        self._buying_threshold = buying_threshold
        self._selling_threshold = selling_threshold
        self._tracked_min = None
        self._tracked_max = None

    def tracking(self, price):
        if self._state == STATE_WANT_TO_BUY:
            assert self._tracked_max is None, "You're in state `STATE_WANT_TO_BUY`, `tracked_max` must be None."
            if self._tracked_min is None:
                self._tracked_min = price
            else:
                self._tracked_min = price if price < self._tracked_min else self._tracked_min
        elif self._state == STATE_WANT_TO_SELL:
            assert self._tracked_min is None, "You're in state `STATE_WANT_TO_SELL`, `tracked_min` must be None."
            if self._tracked_max is None:
                self._tracked_max = price
            else:
                self._tracked_max = price if price > self._tracked_max else self._tracked_max
        else:
            raise

    def buying_signal(self, price):
        return (self._state == STATE_WANT_TO_BUY) and \
            (self._tracked_min is not None) and \
            (price - self._tracked_min) >= self._buying_threshold

    def selling_signal(self, price):
        return (self._state == STATE_WANT_TO_SELL) and \
            (self._tracked_max is not None) and \
            (self._tracked_max - price) >= self._selling_threshold

    def buy(self, price):
        self.tracking(price)
        super(AgentD, self).buy(price)
        self._tracked_max = price
        self._tracked_min = None

    def sell(self, price):
        self.tracking(price)
        super(AgentD, self).sell(price)
        self._tracked_min = price
        self._tracked_max = None

    def __repr__(self):
        return json.dumps({"name": self.name,
                           "state": self._state,
                           "price": self.price,
                           "tracked_min": self._tracked_min,
                           "tracked_max": self._tracked_max,
                           "buying_threshold": self._buying_threshold,
                           "selling_threshold": self._selling_threshold})


def polling(agent, prices):
    timestamp = 0
    while timestamp < len(prices):
        # Polling buy
        if agent.state == STATE_WANT_TO_BUY:
            while timestamp < len(prices):
                price = prices[timestamp]
                timestamp += 1
                try:
                    agent.buy(price)
                    LOG.info("{} buys a stock/bitcoin at price {} successfully.".format(agent.name, price))
                    break
                except AssertionError:
                    LOG.info("{} could not buy a stock/bitcoin at price {}. {}".format(agent.name, price, agent.__repr__()))

        # Polling sell
        elif agent.state == STATE_WANT_TO_SELL:
            while timestamp < len(prices):
                price = prices[timestamp]
                timestamp += 1
                try:
                    agent.sell(price)
                    LOG.info("{} sells a stock/bitcoin at price {} successfully.".format(agent.name, price))
                    break
                except AssertionError:
                    LOG.info("{} could not sell a stock/bitcoin at price {}. {}".format(agent.name, price, agent.__repr__()))


if __name__ == "__main__":
    pass
