import json
import logging
import unittest

LOG = logging.getLogger(__name__).setLevel(logging.DEBUG)

STATE_WANT_TO_BUY = 0
STATE_WANT_TO_SELL = 1


class BaseAgent(object):
    def __init__(self, state, connection=None, name="base"):
        self._state = state
        self.name = name
        self.price = None
        # connect to market and perform actions.
        self.connection = connection

    def buy(self, price):
        """Buy stock/bitcoin from market.
        price: the price of stock/bitcoin at timestamp t
        """
        # if self.buying_signal(price):
        assert self.buying_signal(price), \
            "{} cannot buy its stock/bitcoin.\n{}".format(self.name, self.__repr__())

        # TODO: buy this stock
        LOG.debug("{} buys a stock/bitconin at price {}.".format(self.name, price))
        # sanity checking
        if self.price is None:
            self.price = price

        # Switch current state from `STATE_WANT_TO_BUY` to `STATE_WANT_TO_SELL`
        self._state = STATE_WANT_TO_SELL
        # TODO: Emit a signal/message to a pool and waiting for others who want to buy.

    def sell(self, price):
        """Send stock/bitcoin to market.
        price: the value of stock in timestamp t
        """
        assert self.selling_signal(price), \
            "{} cannot sell its stock/bitcoin.\n{}".format(self.name, self.__repr__())

        # TODO: sell this stock
        LOG.debug("{} sells a stock/bitcoin at price {}, and gets profit {}."
                  .format(self.name, price, price-self.price))
        # Reset `price` since we have sold it
        self.price = None
        # Switch current state from `STATE_WANT_TO_SELL` to `STATE_WANT_TO_BUY`
        self._state = STATE_WANT_TO_BUY
        # TODO: Emit a signal/message to a pool and waiting for others who want to sell

    def buying_signal(self, price):
        raise

    def selling_signal(self, price):
        raise

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
    def __init__(self, state,
                 lower_bound, upper_bound,
                 name="N-Agent"):
        # TODO: Set default value for `state`, `lower_bound` and `upper_bound`
        # from sound probability distributions
        super(BaseAgent, self).__init__(state, name)
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def buying_signal(self, price):
        return self._state == STATE_WANT_TO_BUY and \
            (price >= self._lower_bound)

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
    def __init__(self, state,
                 buyindg_threshold,
                 selling_threshold, name="D-Agent"):
        # `buyindg_threshold` and `selling_threshold` should be postive value
        super(BaseAgent, self).__init__(state, name)
        self._buying_threshold = buyindg_threshold
        self._selling_threshold = selling_threshold
        self._tracked_min = None
        self._tracked_max = None

    def tracking(self, price):
        if self._state == STATE_WANT_TO_BUY:
            # sanity checking
            if self._tracked_max is not None:
                raise

            if self._tracked_min is None:
                self._tracked_min = price
            else:
                self._tracked_min = price if price < self._tracked_min else self._tracke_min

        elif self._state == STATE_WANT_TO_SELL:
            # sanity checking
            if self._tracked_min is not None:
                raise

            if self._tracked_max is None:
                self._tracked_max = price
            else:
                self._tracked_max = price if price > self._tracked_max else self._tracke_max
        else:
            raise

    def buying_singal(self, price):
        return (self._state == STATE_WANT_TO_BUY) and \
            (self._tracked_min is not None) and \
            (price - self._tracked_min) >= self._buying_threshold

    def selling_signal(self, price):
        return (self._state == STATE_WAITING_TO_SELLING) and \
            (self._tracked_max is not None) and \
            (self._tracked_max - price) >= self._selling_threshold

    def buy(self, price):
        super(BaseAgent, self).buy(price)
        self._tracked_min = None

    def sell(self, price):
        super(BaseAgent, self).sell(price)
        self._tracked_max = None

    def __repr__(self):
        return json.dumps({"name": self.name,
                           "state": self._state,
                           "price": self.price,
                           "tracked_min": self._tracked_min,
                           "tracked_max": self._tracked_max,
                           "buyindg_threshold": self._buying_threshold,
                           "selling_threshold": self._selling_threshold})


class AgentNTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_buying_signal(self):
        agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertTrue(agent_n.buying_signal(2))
        self.assertTrue(agent_n.buying_signal(3))

        self.assertFalse(agent_n.buying_signal(4))
        self.assertFalse(agent_n.buying_signal(10))
        self.assertFalse(agent_n.buying_signal(11))

        agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(2))
        self.assertFalse(agent_n.buying_signal(3))
        self.assertFalse(agent_n.buying_signal(4))
        self.assertFalse(agent_n.buying_signal(10))
        self.assertFalse(agent_n.buying_signal(11))

    def test_selling_signal(self):
        agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertTrue(agent_n.sellingsignal(11))
        self.assertTrue(agent_n.sellingsignal(10))
        self.assertFalse(agent_n.selling_signal(4))
        self.assertFalse(agent_n.selling_signal(3))
        self.assertFalse(agent_n.selling_signal(2))

        agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.buying_signal(2))
        self.assertFalse(agent_n.buying_signal(3))
        self.assertFalse(agent_n.buying_signal(4))
        self.assertFalse(agent_n.buying_signal(10))
        self.assertFalse(agent_n.buying_signal(11))

    def test_buy(self):
        agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(2)
        self.assertEqual(agent_n.state, STATE_WANT_TO_SELL)
        self.assertEqual(agent_n.price, 2)

        agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(3)
        self.assertEqual(agent_n.state, STATE_WANT_TO_SELL)
        self.assertEqual(agent_n.price, 3)

        # TODO: The following code should raise exception, assert those exceptions
        # agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        # agent_n.buy(1)

        # agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        # agent_n.buy(3)

    def test_sell(self):
        agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        agent_n.sell(11)
        self.assertEqual(agent_n.state, STATE_WANT_TO_BUY)
        self.assertIsNone(agent_n.price)

        agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        agent_n.sell(10)
        self.assertEqual(agent_n.state, STATE_WANT_TO_BUY)
        self.assertIsNone(agent_n.price)
        # TODO: The following code should raise exceptions, assert those exceptions
        # agent_n = AgentN(STATE_WANT_TO_SELL, 3, 10)
        # agent_n.sell(5)

        # agent_n = AgentN(STATE_WANT_TO_BUY, 3, 10)
        # agent_n.sell(11)


if __name__ == "__main__":
    pass
