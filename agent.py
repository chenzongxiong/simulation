import json
import random

import log as logging
import constants
from market import get_market


LOG = logging.getLogger(__name__)

STATE_WANT_TO_BUY = constants.STATE_WANT_TO_BUY
STATE_WANT_TO_SELL = constants.STATE_WANT_TO_SELL


class BaseAgent(object):

    def __init__(self,
                 state,
                 name="Agent-Base",
                 price=None,
                 market=None):
        self._state = random.choice([STATE_WANT_TO_BUY, STATE_WANT_TO_SELL]) \
            if state is None else state
        self.name = name
        self.price = 0 if self._state == STATE_WANT_TO_SELL and \
            price is None else price

        self.profits = []
        self._market = get_market() if market is None else market

    def buy(self, price):
        """Buy stock/bitcoin from market.
        Parameters:
        --------
        price: the price of stock/bitcoin at timestamp t
        """
        assert self.buying_signal(price), \
            "{} cannot buy a stock/bitcoin at price {}. {}".format(self.name, price,
                                                                    self.__repr__())
        LOG.debug("{} wants to buy a stock/bitcoin at price {}. {}".format(
            self.name, price, self.__repr__()))

        # Emit a signal/message to a pool and wait for others who want to buy.
        self._market.publish(self, "postprocess_buy", price)
        return self

    def sell(self, price):
        """Send stock/bitcoin to market.
        --------
        Parameters:
        price: the value of stock in timestamp t
        """
        assert self.selling_signal(price), \
            "{} cannot sell its stock/bitcoin.{}".format(self.name, self.__repr__())
        assert self.price is not None, \
            "{} must buy a stock/bitcoin before selling."

        # Emit a signal/message to a pool and wait for others who want to sell
        LOG.debug("{} wants to sell a stock/bitcoin at price {}. {}".format(
            self.name, price, self.__repr__()))

        self._market.publish(self, "postprocess_sell", price)
        return self

    def postprocess_buy(self, price):
        # Update stock/bitcoin's price
        self.price = price
        # Switch current state from `STATE_WANT_TO_BUY` to `STATE_WANT_TO_SELL`
        self._state = STATE_WANT_TO_SELL

    def postprocess_sell(self, price):
        self.profits.append(price - self.price)
        LOG.debug("{} sells a stock/bitcoin at price {}, and gets profit {}."
                  .format(self.name, price, self.profits[-1]))
        # Reset `price` since we have sold it
        self.price = None
        # Switch current state from `STATE_WANT_TO_SELL` to `STATE_WANT_TO_BUY`
        self._state = STATE_WANT_TO_BUY

    def buying_signal(self, price):
        raise NotImplementedError

    def selling_signal(self, price):
        raise NotImplementedError

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
                 state=None,
                 lower_bound=None,
                 upper_bound=None,
                 name="N-Agent",
                 lower_random_func=random.uniform,
                 upper_random_func=random.gammavariate,
                 **kwargs):

        price = kwargs.pop("price", None)
        super(AgentN, self).__init__(state=state, name=name, price=price)

        if not kwargs:
            assert lower_random_func == random.uniform
            assert upper_random_func == random.gammavariate
            kwargs['lower_random_func_args'] = (0., 1.)
            kwargs['upper_random_func_args'] = (4., 1.)

        self._lower_bound = lower_bound if lower_bound else \
            lower_random_func(*kwargs['lower_random_func_args'])

        self._upper_bound = upper_bound if upper_bound else \
            self._lower_bound + upper_random_func(*kwargs['upper_random_func_args'])

        # Ensure the price is less/equal `lower_bound`
        if price is None and self.state == STATE_WANT_TO_SELL:
            self.price = self._lower_bound

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
                 state=None,
                 buying_threshold=None,
                 selling_threshold=None,
                 name="D-Agent",
                 random_func=random.gammavariate,
                 **kwargs):

        super(AgentD, self).__init__(state=state, name=name,
                                     price=kwargs.pop("price", None))
        if not kwargs:
            assert random_func == random.gammavariate
            kwargs["random_func_args"] = (1.0, 1.0)

        self._buying_threshold = random_func(*kwargs["random_func_args"]) \
            if buying_threshold is None else buying_threshold
        self._selling_threshold = random_func(*kwargs["random_func_args"]) \
            if selling_threshold is None else selling_threshold

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
        return super(AgentD, self).buy(price)

    def postprocess_buy(self, price):
        super(AgentD, self).postprocess_buy(price)
        self._tracked_max = price
        self._tracked_min = None

    def sell(self, price):
        self.tracking(price)
        return super(AgentD, self).sell(price)

    def postprocess_sell(self, price):
        super(AgentD, self).postprocess_sell(price)
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


class AgentE(BaseAgent):

    def __init__(self,
                 state=None,
                 name="Agent-E"):
        super(AgentE, self).__init__(state=state, name=name)

    def buying_signal(self, price=None):
        return self._state == STATE_WANT_TO_BUY

    def selling_signal(self, price=None):
        return self._state == STATE_WANT_TO_SELL


def polling(agent, prices):
    timestamp = 0
    while timestamp < len(prices):
        # Polling buy
        if agent.state == STATE_WANT_TO_BUY:
            while timestamp < len(prices):
                price = prices[timestamp]
                timestamp += 1
                try:
                    agent.buy(price).postprocess_buy(price)
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
                    agent.sell(price).postprocess_sell(price)
                    LOG.info("{} sells a stock/bitcoin at price {} successfully.".format(agent.name, price))
                    break
                except AssertionError:
                    LOG.info("{} could not sell a stock/bitcoin at price {}. {}".format(agent.name, price, agent.__repr__()))


if __name__ == "__main__":
    pass
