import sys
import time
import random
from matplotlib import pyplot as plt

import log as logging
import agent
import factory
import constants
from market import get_market, reset_market


LOG = logging.getLogger(__name__)


class Simulation2(object):
    def __init__(self,
                 number_of_transactions=100,
                 mu=0,
                 sigma=0.5,

                 lower_bound_of_delta=0,
                 upper_bound_of_delta=20,
                 C_delta=20,
                 k_delta=7.5,
                 theta_delta=1.0,
                 C0_delta=2,
                 C_alpha=1,
                 k_alpha=2,
                 theta_alpha=2,

                 lower_bound_of_beta=0,
                 upper_bound_of_beta=20,
                 step_of_beta=0.5,
                 k_beta=2,
                 theta_beta=2):

        reset_market()
        self.market = get_market()
        self.agentNs = factory.RealAgentNFactory(
            lower_bound_of_delta=lower_bound_of_delta,
            upper_bound_of_delta=upper_bound_of_delta,
            C_delta=C_delta,
            k_delta=k_delta,
            C0_delta=C0_delta,
            C_alpha=C_alpha,
            k_alpha=k_alpha,
            theta_alpha=theta_alpha)

        total_stocks_of_N_agents = self.agentNs.total_stocks
        print(total_stocks_of_N_agents)
        self.agentDs = factory.RealAgentDFactory(
            lower_bound_of_beta=lower_bound_of_beta,
            upper_bound_of_beta=upper_bound_of_beta,
            step_of_beta=step_of_beta,
            total_stocks_of_N_agents=total_stocks_of_N_agents,
            k_beta=k_beta, theta_beta=theta_beta)

        self._number_of_transactions = number_of_transactions
        self._mu = mu
        self._sigma = sigma
        self._Kn_list = []
        LOG.info("****************************************")
        LOG.info("Intializing...")
        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_stocks))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_stocks))
        LOG.info("Factory {} has {} virtual agents".format(self.agentNs.name, self.agentNs.total_virtual_agents))
        LOG.info("Factory {} has {} virtual agents".format(self.agentDs.name, self.agentDs.total_virtual_agents))
        LOG.info("****************************************")
        time.sleep(1)

    def simulate(self, delta=0.01, max_iteration=10000):
        start = time.time()
        noise = self._generate_noise()
        _action = self._action(noise)
        price = 0
        self.market.prices.append(price)

        i = 0
        self._curr_num_transactions = 0
        while i < self._number_of_transactions:
            _price = price
            _noise = noise
            _action = self._action(_noise)
            LOG.info("Round #{} ACTION: {}, PRICE: {}, DELTA: {}".format(
                i, _action, _price, delta))
            _start = time.time()
            price= self._simulate(_noise, _price, delta, max_iteration)
            _end = time.time()
            LOG.info("Round #{} Time costs: {}".format(
                i, _end-_start))

            noise = self._generate_noise()
            if price is None:
                while self._action(noise) == _action:
                    noise = self._generate_noise()
                price = self.market.prices[-1]
            else:
                i += 1
                self._curr_num_transactions = i

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))

    def _simulate(self, noise, price, delta=0.01, max_iteration=10000):
        LOG.info("Noise is {}".format(noise))
        # number of external agents
        action = self._action(noise)

        if action == "buy" and self.agentNs.total_stocks == 0:
            LOG.warn("No one wants to sell stocks/bitcoins in market.")
            return None
        if action == "sell" and \
           self.agentNs.total_stocks == self.agentNs.length:
            LOG.warn("No one wants to buy stocks/bitcoins in market.")
            return None

        state = constants.STATE_WANT_TO_BUY \
            if action == "buy" else constants.STATE_WANT_TO_SELL

        agentEs = factory.AgentFactory(agent.AgentE, abs(noise),
                                       agent_name="Agent-E",
                                       state=state)
        for agente in agentEs:
            getattr(agente, action)(price)

        delta = self._direction(action)*delta
        iteration = 0
        _Kn = []
        # curr_diff, price = self._jump_to_next_unstable_price(price, action)
        curr_diff = self._ballot(price)
        _Kn.append(self.total_stocks + curr_diff)
        #import ipdb; ipdb.set_trace()
        while True:
            iteration += 1
            if iteration >= max_iteration:
                LOG.error("Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(max_iteration, price))
                return None

            price += delta
            prev_diff = curr_diff
            # TODO: 10 ms
            _start = time.time()
            curr_diff = self._ballot(price)
            _end = time.time()
            # LOG.info("Time elapses {} in *ballot*".format(_end-_start))
            # import ipdb; ipdb.set_trace()
            # _Kn.append(self.agentNs.total_stocks + self.agentDs.total_stocks + curr_diff)
            _Kn.append(self.total_stocks + curr_diff)

            if iteration % 1000 == 0:
                LOG.info("Iteration #{}: price {}.".format(iteration, price))
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
                LOG.info("#{} agents want to buy stocks".format(
                    self.market.number_of_buyers))
                LOG.info("#{} agents want to sell stocks".format(
                    self.market.number_of_sellers))

            flag1 = self.market.exchangable()
            # TODO: 2 ~ 4 us
            flag2 = self._check_stable_price(prev_diff, curr_diff)
            if flag1 or flag2:
                # TODO: 20 ~ 40 us
                self.market.exchange(price)
                LOG.info("Iteration #{}: reach stability price: {}. current difference is: {}, previous difference is: {}]".format(iteration, price, curr_diff, prev_diff))
                break
            else:
                # TODO: 20 ~ 40 us
                self.market.restore()

        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_stocks))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_stocks))

        LOG.info("Total assets in market is {}".format(self.total_stocks))
        self._Kn_list.append((_Kn, action))
        return price

    def _check_stable_price(self, t1, t2):
        return t1*t2 <= 0 and t1 != 0

    def _generate_noise(self):
        """Generate external agents from gaussian distribution. This function ensures
        the number of external agnets must be integral and non-zero"""
        if not getattr(self, "_generator", None):
            self.noise_generator(random.normalvariate, self._mu, self._sigma)

        _noise = 0

        while _noise == 0:
            _noise = int(round(self._generator(*self._generator_args, **self._generator_kwargs)))
        return _noise

    def noise_generator(self, generator, *args, **kwargs):
        self._generator = generator
        self._generator_args = args
        self._generator_kwargs = kwargs

    def _action(self, noise):
        """Return the action of external agents take. If noise is less than 0,
        the stocks/bitcoins in market will decrease. In other word, external
        agents take action `buy`."""
        if noise < 0:
            return "buy"
        elif noise > 0:
            return "sell"
        else:
            return None

    @property
    def total_stocks(self):
        """Total assets(stocks/bitcoins) in market."""
        return self.agentDs.total_stocks + self.agentNs.total_stocks

    def _direction(self, action):
        """If action is `buy` the price should go up, the direction of trend is
        positive. And action `sell` the price should go down, the direction of
        trend is negative.
        --------
        Parameters:
        action: only could be `buy` or `sell`
        Returns: 1 if action is `buy`, 0 if action is `sell`
        """
        return 1 if action == "buy" else -1

    def _ballot(self, price):
        # TODO: consider *balance*
        # remove try-catch to improve performance
        # TODO: 0.02 s
        counter = 0
        _start = time.time()
        for real_agentn in self.agentNs:
            for agentn in real_agentn:
                agentn.sell(price)
                agentn.buy(price)
                counter += 1

        _end = time.time()
        # LOG.info("Time {} elapses in *real agent d*".format(_end-_start))

        _start = time.time()

        # TODO: 0.004 s
        for real_agentd in self.agentDs:
            for agentd in real_agentd:
                agentd.sell(price)
                agentd.buy(price)
                counter += 1
        _end = time.time()
        # LOG.info("Time {} elapses in *real agent n*".format(_end-_start))
        # LOG.info("{} agnets participant in this ballot.".format(counter))

        diff = self.market.number_of_buyers - self.market.number_of_sellers
        #diff = self.market.number_of_sellers - self.market.number_of_buyers
        return diff

    def _jump_to_next_unstable_price(self, price, action, delta=0.001):
        diff = 0
        direction = self._direction(action)
        delta = direction * delta
        i = 0
        while diff == 0:
            diff = self._ballot(price)
            price += delta
            i += 1
            if i % 1000 == 0:
                LOG.info("{} iterations passed.".format(i))
                LOG.info("Diff: {}, Price: {}".format(diff, price))

        return diff, price

    def plot_price(self):
        timestamp = range(len(self.market.prices))
        plt.plot(timestamp, self.market.prices)
        plt.xlabel("timestamp")
        plt.ylabel("price")

    def _plot_kn(self, _Kn, action):
        x = range(len(_Kn))
        color = "green" if action == "buy" else "red"
        plt.plot(x, _Kn, color=color, label=action)
        plt.legend()
        plt.show()

    def plot_Fn(self):
        start = 0
        for _Kn, action in self._Kn_list:
            x = range(start, start+len(_Kn), 1)
            color = "green" if action == "buy" else "red"
            plt.plot(x, _Kn, color=color)
            start = len(_Kn) + start - 1

        plt.xlabel("step")
        plt.ylabel("Fn")

    def plot_Kn(self):
        plt.xlabel("step")
        plt.ylabel("Kn")
    def plot(self):
        plt.subplot(3, 1, 1)
        self.plot_Kn()
        plt.subplot(3, 1, 2)
        self.plot_Fn()
        plt.subplot(3, 1, 3)
        self.plot_price()

    def show_plot(self):
        plt.show()
