import unittest
import uuid

import constants
import log as logging
import agent
import factory
import market


LOG = logging.getLogger(__name__)

STATE_WANT_TO_BUY = constants.STATE_WANT_TO_BUY
STATE_WANT_TO_SELL = constants.STATE_WANT_TO_SELL


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        market.reset_market()


class AgentNTestCase(BaseTestCase):

    def test_buying_signal(self):
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertTrue(agent_n.buying_signal(2))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertTrue(agent_n.buying_signal(3))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.buying_signal(4))

        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(2))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(3))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(4))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(10))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.buying_signal(11))

    def test_selling_signal(self):
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertTrue(agent_n.selling_signal(11))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertTrue(agent_n.selling_signal(10))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.selling_signal(4))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.selling_signal(3))
        agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
        self.assertFalse(agent_n.selling_signal(2))

        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.selling_signal(2))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.selling_signal(3))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.selling_signal(4))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.selling_signal(10))
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        self.assertFalse(agent_n.selling_signal(11))

    def test_buy(self):
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(2)
        agent_n.postprocess_buy(2)
        self.assertEqual(agent_n.state, STATE_WANT_TO_SELL)
        self.assertEqual(agent_n.price, 2)

        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(3)
        agent_n.postprocess_buy(3)
        self.assertEqual(agent_n.state, STATE_WANT_TO_SELL)
        self.assertEqual(agent_n.price, 3)

        try:
            agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
            agent_n.buy(5)
            agent_n.postprocess_buy(5)
        except AssertionError:
            pass

        try:
            agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
            agent_n.buy(3)
            agent_n.postprocess_buy(3)
        except AssertionError:
            pass

    def test_sell(self):
        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(2)
        agent_n.postprocess_buy(2)
        agent_n.sell(11)
        agent_n.postprocess_sell(11)
        self.assertEqual(agent_n.state, STATE_WANT_TO_BUY)
        self.assertIsNone(agent_n.price)

        agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        agent_n.buy(2)
        agent_n.postprocess_buy(2)
        agent_n.sell(10)
        agent_n.postprocess_sell(11)
        self.assertEqual(agent_n.state, STATE_WANT_TO_BUY)
        self.assertIsNone(agent_n.price)

        try:
            agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
            agent_n.sell(11)
            agent_n.postprocess_sell(11)
        except AssertionError:
            pass

        try:
            agent_n = agent.AgentN(STATE_WANT_TO_SELL, 3, 10)
            agent_n.sell(10)
            agent_n.postprocess_sell(10)
        except AssertionError:
            pass


class AgentDTestCase(BaseTestCase):

    def test_buying_signal(self):
        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(2)
        self.assertTrue(agent_d.buying_signal(7))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(2)
        self.assertFalse(agent_d.buying_signal(4))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.tracking(1)
        self.assertTrue(agent_d.buying_signal(5))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.tracking(4)
        self.assertTrue(agent_d.buying_signal(7))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.tracking(1)
        self.assertFalse(agent_d.buying_signal(3))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.tracking(4)
        self.assertFalse(agent_d.buying_signal(5))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(2)
        self.assertFalse(agent_d.buying_signal(7))

    def test_selling_signal(self):
        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        self.assertTrue(agent_d.selling_signal(4))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        self.assertFalse(agent_d.selling_signal(5))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        agent_d.tracking(9)
        self.assertTrue(agent_d.selling_signal(5))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        agent_d.tracking(9)
        self.assertFalse(agent_d.selling_signal(8))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        agent_d.tracking(4)
        self.assertTrue(agent_d.selling_signal(3))

        agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
        agent_d.tracking(7)
        agent_d.tracking(4)
        self.assertFalse(agent_d.selling_signal(5))

        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(7)
        self.assertFalse(agent_d.selling_signal(2))

    def test_buy(self):
        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.tracking(2)
        agent_d.tracking(5)
        agent_d.buy(6)
        agent_d.postprocess_buy(6)
        self.assertEqual(agent_d.state, STATE_WANT_TO_SELL)
        self.assertEqual(agent_d.price, 6)
        self.assertIsNone(agent_d._tracked_min)

        try:
            agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
            agent_d.tracking(3)
            agent_d.tracking(2)
            agent_d.tracking(5)
            agent_d.buy(4)
            agent_d.postprocess_buy(4)
        except AssertionError:
            pass

        try:
            agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
            agent_d.tracking(3)
            agent_d.tracking(2)
            agent_d.tracking(5)
            agent_d.buy(4)
            agent_d.postprocess_buy(4)
        except AssertionError:
            pass

    def test_sell(self):
        agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        agent_d.tracking(3)
        agent_d.buy(7)
        agent_d.postprocess_buy(7)
        agent_d.tracking(8)
        agent_d.tracking(9)
        agent_d.sell(6)
        agent_d.postprocess_sell(6)
        self.assertEqual(agent_d.state, STATE_WANT_TO_BUY)
        self.assertIsNone(agent_d.price)
        self.assertIsNone(agent_d._tracked_max)

        try:
            agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
            agent_d.tracking(9)
            agent_d.sell(6)
            agent_d.postprocess_sell(6)
        except AssertionError:
            pass

        try:
            agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
            agent_d.tracking(3)
            agent_d.buy(7)
            agent_d.postprocess_buy(7)
            agent_d.tracking(8)
            agent_d.tracking(9)
            agent_d.sell(8)
            agent_d.postprocess_sell(8)
        except AssertionError:
            pass


class AgentETestCase(BaseTestCase):

    def test_buying_signal(self):
        agent_e = agent.AgentE(STATE_WANT_TO_BUY)
        self.assertTrue(agent_e.buying_signal())

        agent_e = agent.AgentE(STATE_WANT_TO_SELL)
        self.assertFalse(agent_e.buying_signal())

    def test_selling_signal(self):
        agent_e = agent.AgentE(STATE_WANT_TO_SELL)
        self.assertTrue(agent_e.selling_signal())

        agent_e = agent.AgentE(STATE_WANT_TO_BUY)
        self.assertFalse(agent_e.selling_signal())

    def test_buy(self):
        agent_e = agent.AgentE(STATE_WANT_TO_BUY)
        agent_e.buy(4).postprocess_buy(4)
        self.assertEqual(agent_e.price, 4)
        self.assertEqual(agent_e.state, STATE_WANT_TO_SELL)

        try:
            agent_e = agent.AgentE(STATE_WANT_TO_SELL)
            agent_e.buy(4).postprocess_buy(4)
        except AssertionError:
            pass

    def test_sell(self):
        agent_e = agent.AgentE(STATE_WANT_TO_SELL)
        agent_e.sell(4).postprocess_sell(4)
        self.assertIsNone(agent_e.price)
        self.assertEqual(agent_e.state, STATE_WANT_TO_BUY)

        try:
            agent_e = agent.AgentE(STATE_WANT_TO_BUY)
            agent_e.sell(4).postprocess_sell(4)
            self.assertIsNone(agent_e.price)
            self.assertEqual(agent_e.state, STATE_WANT_TO_BUY)
        except AssertionError:
            pass


class AgentFactoryTestCase(BaseTestCase):

    def test_total_stocks(self):
        agentn_factory = factory.AgentFactory(agent.AgentN, 10, state=constants.STATE_WANT_TO_SELL)
        self.assertEqual(agentn_factory.total_assets, 10)
        agentn_factory = factory.AgentFactory(agent.AgentN, 10, state=constants.STATE_WANT_TO_BUY)
        self.assertEqual(agentn_factory.total_assets, 0)

        agentd_factory = factory.AgentFactory(agent.AgentD, 10, state=constants.STATE_WANT_TO_SELL)
        self.assertEqual(agentd_factory.total_assets, 10)
        agentd_factory = factory.AgentFactory(agent.AgentD, 10, state=constants.STATE_WANT_TO_BUY)
        self.assertEqual(agentd_factory.total_assets, 0)

        agente_factory = factory.AgentFactory(agent.AgentE, 10, state=constants.STATE_WANT_TO_SELL)
        self.assertEqual(agente_factory.total_assets, 10)
        agente_factory = factory.AgentFactory(agent.AgentE, 10, state=constants.STATE_WANT_TO_BUY)
        self.assertEqual(agente_factory.total_assets, 0)


class MarketTestCase(BaseTestCase):
    def setUp(self):
        self.market = market.get_market()

    def test_publish(self):
        self.assertEqual(self.market.number_of_buyers, 0)
        agent_e = agent.AgentE(STATE_WANT_TO_BUY,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_e.buy(1)
        self.assertEqual(self.market.number_of_buyers, 1)
        self.assertEqual(self.market.number_of_sellers, 0)

        agent_e = agent.AgentE(STATE_WANT_TO_SELL,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_e.sell(1)
        self.assertEqual(self.market.number_of_buyers, 1)
        self.assertEqual(self.market.number_of_sellers, 1)

        # agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
        # agent_d.tracking(3)
        # agent_d.tracking(2)
        # agent_d.tracking(5)
        # agent_d.buy(6)
        # self.assertEqual(len(self.market._buying_agents), 2)
        # self.assertEqual(len(self.market._selling_agents), 1)

        # agent_d.tracking(8)
        # agent_d.tracking(9)
        # agent_d.sell(6)
        # self.assertEqual(len(self.market._buying_agents), 2)
        # self.assertEqual(len(self.market._selling_agents), 2)

        # agent_n = agent.AgentN(STATE_WANT_TO_BUY, 3, 10)
        # agent_n.buy(2)
        # self.assertEqual(len(self.market._buying_agents), 3)
        # self.assertEqual(len(self.market._selling_agents), 2)
        # agent_n.sell(11)
        # self.assertEqual(len(self.market._buying_agents), 3)
        # self.assertEqual(len(self.market._selling_agents), 3)

    def test_exchange_and_price(self):
        self.assertEqual(self.market.prices, [])
        agent_1 = agent.AgentE(STATE_WANT_TO_BUY,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_1.buy(1)
        agent_2 = agent.AgentE(STATE_WANT_TO_SELL,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_2.sell(1)
        self.market.exchange(1)
        self.assertEqual(self.market.prices, [1])

        agent_1 = agent.AgentE(STATE_WANT_TO_BUY,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_1.buy(1)
        agent_2 = agent.AgentE(STATE_WANT_TO_SELL,
                               name="AgentE-"+uuid.uuid4().hex)
        agent_2.sell(1)
        try:
            # This transaction is invalid,
            self.market.exchange(2)
        except AssertionError:
            pass


def test_agent_behaviour():
    prices = [8, 7, 4, 6, 5, 4, 7, 9, 5, 14, 21, 19, 20]

    agent_n = agent.AgentN(STATE_WANT_TO_BUY, 5, 20)
    agent.polling(agent_n, prices)
    assert agent_n.profits[-1] == 17
    LOG.debug("==============================================================")
    agent_n = agent.AgentN(STATE_WANT_TO_SELL, 5, 20)
    agent_n.price = 0
    agent.polling(agent_n, prices)
    assert agent_n.profits[-1] == 21

    LOG.debug("==============================================================")
    agent_d = agent.AgentD(STATE_WANT_TO_BUY, 4, 3)
    agent.polling(agent_d, prices)
    assert agent_d.profits == [-4]
    LOG.debug("==============================================================")
    agent_d = agent.AgentD(STATE_WANT_TO_SELL, 4, 3)
    agent_d.price = 0
    agent.polling(agent_d, prices)
    assert agent_d.profits == [4, -4]


if __name__ == "__main__":
    test_agent_behaviour()
    unittest.main()
