import os
import time
import random
import numpy as np
from matplotlib import pyplot as plt

import log as logging
import agent
import factory
import constants
import colors
from market import get_market, reset_market


LOG = logging.getLogger(__name__)

def plot_agent_distribution(details, title='', xlabel='', ylabel=''):
    fig, ax = plt.subplots()
    labels = []
    heights = []
    for k, v in details.items():
        labels.append(k)
        heights.append(v)

    indexs = np.arange(len(labels))
    # bar_width = 0.35
    bar_width = 1
    ax.set_title(title)
    # ax.bar(indexs, heights, bar_width, color={'b', 'r'})
    ax.bar(indexs, heights, bar_width, color={'b', 'r'})
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks(indexs)
    ax.set_xticklabels(labels, rotation=90)
    ax.legend()
    fig.tight_layout()
    fig.set_figheight(500)
    fig.set_figwidth(1000)
    plt.show()
    fig.savefig("./{}.png".format(title), dpi=400)


def plot_price_stocks(prices, Kns, B1, B2, B3, index=None, mu=0, sigma=-1, failed=False):
    fig = plt.figure()
    prices = np.array(prices)
    # prices = prices[1:]
    Kns = np.array(Kns)
    # Kns = Kns[1:] - Kns[:-1]
    if np.all(prices[1:] - prices[:-1] >= 0):
        color = 'black'
        txt = "Increase"
    else:
        color = 'blue'
        txt = 'Decrease'

    l = len(prices)
    if l == 1:
        l = 10
    B1 = np.array([B1]*l)
    B2 = np.array([B2]*l)
    B3 = np.array([B3]*l)

    plt.plot(prices, B1, color='red', linewidth=1)
    plt.plot(prices, B2, color='cyan', linewidth=2)
    plt.plot(prices, B3, color='black', linewidth=4)

    plt.plot(prices, Kns, color=color, marker='o', markersize=8)
    # import ipdb; ipdb.set_trace()
    # plt.arrow(prices.mean(), Kns.mean(), prices.mean() / 1000, 0, shape='left')
    # plt.arrow(prices.mean(), Kns.mean(), prices.mean() / 10, 0, shape='right')
    plt.text(prices.mean(), Kns.mean(), txt)
    plt.xlabel("Prices")
    plt.ylabel("#Stocks")
    if failed is True:
        fname = './frames-mu-{}-sigma-{}/{}-failed.png'.format(mu, sigma, index)
    else:
        fname = './frames-mu-{}-sigma-{}/{}.png'.format(mu, sigma, index)

    os.makedirs(os.path.dirname(fname), exist_ok=True)
    fig.savefig(fname, dpi=400)


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

        random.seed(123)
        np.random.RandomState(seed=123)

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

        self.agentDs = factory.RealAgentDFactory(
            lower_bound_of_beta=lower_bound_of_beta,
            upper_bound_of_beta=upper_bound_of_beta,
            step_of_beta=step_of_beta,
            total_stocks_of_N_agents=total_stocks_of_N_agents,
            k_beta=k_beta, theta_beta=theta_beta)

        self._number_of_transactions = number_of_transactions
        self._mu = mu
        self._sigma = sigma
        self._participated_agents = []
        self._baseline_total_stocks = self.agentDs.total_stocks + self.agentNs.total_stocks
        LOG.info("****************************************")
        LOG.info("Intializing...")
        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_stocks))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_stocks))
        LOG.info("Factory {} has {} virtual agents".format(self.agentNs.name, self.agentNs.total_virtual_agents))
        LOG.info("Factory {} has {} virtual agents".format(self.agentDs.name, self.agentDs.total_virtual_agents))
        LOG.info("Number of N real agents: {}".format(self.agentNs.length))
        LOG.info("Number of D real agents: {}".format(self.agentDs.length))
        LOG.info("Total stocks belong to AgentD {}".format(self.agentDs.total_stocks))
        LOG.info("Total stocks belong to AgentN {}".format(self.agentNs.total_stocks))
        LOG.info("Total stocks in market: {}".format(self.agentNs.total_stocks + self.agentDs.total_stocks))
        LOG.debug("min width of N agents: {}".format(self.agentNs.min_width))
        LOG.debug("max width of N agents: {}".format(self.agentNs.max_width))

        LOG.debug("min width of N real agents: {}".format(self.agentNs.min_width_real_agent))
        LOG.debug("max width of N real agents: {}".format(self.agentNs.max_width_real_agent))
        LOG.debug("lowest bound of N real agents: {}".format(self.agentNs._lowest_bound))
        LOG.debug("uppest bound of N real agents: {}".format(self.agentNs._uppest_bound))

        LOG.debug("min threshold of D agents: {}".format(self.agentDs.min_threshold))
        LOG.debug("max threshold of D agents: {}".format(self.agentDs.max_threshold))
        LOG.info("****************************************")
        input("Press Enter to continue...")
        # plot_agent_distribution(self.agentNs.distribution, title="virtual-agentn-distribution", xlabel="balance", ylabel='#virtual agents')
        # plot_agent_distribution(self.agentNs.distribution2, title="real-agentn-distribution", xlabel="balance", ylabel='#real agents')
        # plot_agent_distribution(self.agentNs.details, title="AgentN-Details", xlabel="width", ylabel='#virtual agents')
        # plot_agent_distribution(self.agentDs.distribution, title="virtual-agentd-distribution", xlabel='buy/sell threashold', ylabel='#virtual agents')
        # plot_agent_distribution(self.agentDs.distribution2, title="real-agentd-distribution", xlabel='buy/sell threashold', ylabel='#virtual agents')


    def simulate(self, delta=0.01, max_iteration=5000):
        # np.random.seed(123)
        max_iteration = 200
        # delta = 0.005
        delta = 0.07
        start = time.time()
        noise = self._generate_noise()
        price = 0
        self.market.prices.append(price)
        self._Kn_list = []
        self._data_series = []
        self._random_walk = [0]
        self._kn_list = [0]
        i = 0
        self._curr_num_transactions = 0

        self.agentDs.backup()

        while i < self._number_of_transactions + 1:
            _price = price
            _noise = noise
            _action = self._action(_noise)
            _total_stocks = self.total_stocks
            LOG.info(colors.yellow("Round #{} ACTION: {}, PRICE: {:.3f}, DELTA: {}, total_stocks: {}, noise/total_stocks is: {:.3f} %".format(
                i, _action, _price, delta, _total_stocks, abs(_noise/_total_stocks) * 100)))

            _start = time.time()
            price = self._simulate(_noise, _price, delta, max_iteration)
            _end = time.time()
            LOG.info("Round #{} Time costs: {}".format(
                i, _end-_start))

            noise = self._generate_noise()
            if price is None:
                # no suitable price found
                while self._action(noise) == _action:
                    noise = self._generate_noise()
                price = self.market.prices[-1]
            else:
                i += 1
                self._curr_num_transactions = i
                self._data_series.append([_total_stocks, _noise, _price, self._random_walk[-1], self._kn_list[-2], _action])
                self._random_walk.append(_noise + self._random_walk[-1])

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))

    def _simulate(self, noise, price, delta=0.01, max_iteration=5000):
        # __price = price
        max_iteration = 5000
        delta = 0.001
        # delta = 0.02
        LOG.info("Noise is {}".format(noise))
        # number of external agents
        action = self._action(noise)

        if action == "buy" and self.agentNs.total_stocks == 0:
            LOG.warn("No one wants to sell stocks/bitcoins in market.")
            return None
        if action == "sell" and \
           self.agentNs.total_stocks == self.agentNs.length * self.agentNs[0].length:
            LOG.warn("No one wants to buy stocks/bitcoins in market.")
            return None

        state = constants.STATE_WANT_TO_BUY \
            if action == "buy" else constants.STATE_WANT_TO_SELL

        agentEs = factory.AgentFactory(agent.AgentE, abs(noise),
                                       agent_name="Agent-E",
                                       state=state)
        for agente in agentEs:
            getattr(agente, action)(price)

        direction = self._direction(action)
        delta = direction*delta
        iteration = 0
        # _Kn = [self.total_stocks - noise]
        # _price_list = [price]
        _Kn = []
        _price_list = []
        LOG.info("Before jump to next unstable price: total assets in market is: {}".format(self.total_stocks))
        # _Kn.append(self.total_stocks)
        # curr_diff, price = self._jump_to_next_unstable_price(price, action)
        # LOG.info("After jump to next unstable price: total assets in market is: {}, curr_diff is: {}".format(self.total_stocks, curr_diff))

        curr_diff = self._ballot(price, direction, True)
        LOG.info("first round ballot, curr_diff is: {}".format(curr_diff))

        _Kn.append(self.total_stocks + curr_diff)
        _price_list.append(price)
        while True:
            iteration += 1
            if iteration >= max_iteration:
                LOG.error(colors.red("Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(max_iteration, price)))
                plot_price_stocks(_price_list, [i + noise for i in _Kn], self.total_stocks,
                                  self.total_stocks + noise,
                                  self.total_stocks + noise + curr_diff,
                                  self._curr_num_transactions,
                                  self._mu,
                                  self._sigma,
                                  True)
                # import ipdb; ipdb.set_trace()
                self.agentDs.restore()
                self.market.reset()
                return None

            prev_diff = curr_diff
            price += delta
            # TODO: 10 ms
            _start = time.time()
            curr_diff = self._ballot(price, direction, False)

            _Kn.append(self.total_stocks + curr_diff)
            _price_list.append(price)

            _end = time.time()
            # LOG.info("Time elapses {} in *ballot*".format(_end-_start))

            if iteration % 1000 == 0:
                LOG.info("Iteration #{}: price {}.".format(iteration, price))
                LOG.info("Previous difference is: {}, Current difference is: {}".format(prev_diff, curr_diff))
                LOG.info("#{} agents want to buy stocks".format(
                    self.market.number_of_buyers))
                LOG.info("#{} agents want to sell stocks".format(
                    self.market.number_of_sellers))
                # import ipdb; ipdb.set_trace()

            flag1 = self.market.exchangable()
            # TODO: 2 ~ 4 us
            flag2 = self._check_stable_price(prev_diff, curr_diff)
            if flag1 or flag2:
                # TODO: 20 ~ 40 us
                LOG.info("Before exchanging at stable price: total assets in market is: {}".format(self.total_stocks))
                # _price_list.append(price)
                # _Kn.append(self.total_stocks + curr_diff)

                self._kn_list.append(self._kn_list[-1] + curr_diff + noise)
                plot_price_stocks(_price_list, [i + noise for i in _Kn], self.total_stocks, self.total_stocks + noise, self.total_stocks + noise + curr_diff,
                                  self._curr_num_transactions,
                                  self._mu,
                                  self._sigma,
                                  False)

                self._participated_agents.append([self.market._buying_agentNs, self.market._selling_agentNs, self.market._buying_agentDs, self.market._selling_agentDs])
                if noise + curr_diff > 0:
                    self._participated_agents[-1] += [noise+curr_diff, 0]
                else:
                    self._participated_agents[-1] += [0, abs(noise+curr_diff)]

                self.market.exchange(price)
                LOG.info("After exchanging at stable price: total assets in market is: {}".format(self.total_stocks))
                LOG.info("Iteration #{}: reach stability price: {:.3f}. current difference is: {}, previous difference is: {}".format(iteration, price, curr_diff, prev_diff))
                # import ipdb; ipdb.set_trace()
                break
            else:
                # TODO: 20 ~ 40 us
                self.market.restore()

        LOG.info("Factory {} has {} stocks".format(self.agentNs.name, self.agentNs.total_stocks))
        LOG.info("Factory {} has {} stocks".format(self.agentDs.name, self.agentDs.total_stocks))

        LOG.info("Total assets in market is {}".format(self.total_stocks))
        self._Kn_list.append((_Kn, action))
        if len(self._Kn_list) >= 2:
            # NOTE: enforce line continuous, don't remove
            self._Kn_list[-2][0].append(_Kn[0])
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

    def _ballot(self, price, direction, first=True):
        # TODO: 0.02 s
        """
        direction: indicate that whether price should grow or decay
                   1 means price would grow, -1 mean price would decay
        """
        counter = 0
        _start = time.time()

        for real_agentd in self.agentDs:
            for agentd in real_agentd:
                # if direction == 1 and not agentd.buying_signal(price):
                #     break
                # if direction == -1 and not agentd.selling_signal(price):
                #     break

                # if agentd.buying_signal(price):
                #     LOG.info(agentd.__repr__() + " buy stock. [D agent]")
                # if agentd.selling_signal(price):
                #     LOG.info(agentd.__repr__() + " sell stock. [D agent]")
                agentd.buy(price)
                agentd.sell(price)

        for real_agentn in self.agentNs:
            for agentn in real_agentn:
                # TODO: opitimize performance
                # if direction == 1 and not agentn.selling_signal(price):
                #     break
                # if direction == -1 and not agentn.buying_signal(price):
                #     break

                agentn.buy(price)
                agentn.sell(price)


        # if direction == 1:      # external agents buy, agents N sell
        #     for real_agentn in self.agentNs:
        #         for agentn in real_agentn:
        #             if agentn.upper_bound > price:
        #                 break
        #             else:
        #                 agentn.sell(price)

        # elif direction == -1:   # external agents sell, agents N buy
        #     for real_agentn in self.agentNs:
        #         for agentn in real_agentn:
        #             if agentn.lower_bound > price:
        #                 break
        #             else:
        #                 agentn.buy(price)

        # _end = time.time()
        # # LOG.info("Time {} elapses in *real agent d*".format(_end-_start))

        # _start = time.time()

        # if first is True:
        #     for real_agentd in self.agentDs:
        #         for agentd in real_agentd:
        #             agentd.tracking(price)


        # # TODO: 0.004 s
        # if direction == 1:      # external agents buy, agents D buy
        #     for real_agentd in self.agentDs:
        #         for agentd in real_agentd:
        #             if not agentd.buying_signal(price):
        #                 break
        #             agentd.buy(price)

        # elif direction == -1:   # external agents sell, agents D sell
        #     for real_agentd in self.agentDs:
        #         for agentd in real_agentd:
        #             if not agentd.selling_signal(price):
        #                 break
        #             agentd.sell(price)

        _end = time.time()
        # LOG.info("Time {} elapses in *real agent n*".format(_end-_start))
        # LOG.info("{} agnets participant in this ballot.".format(counter))

        diff = self.market.number_of_buyers - self.market.number_of_sellers
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

    def plot_price(self, ax):
        timestamp = range(len(self.market.prices))
        ax.plot(timestamp, self.market.prices)
        ax.set_xlabel("timestamp")
        ax.set_ylabel("price")

    def plot_Fn(self, ax):
        start = 0

        for _Kn, action in self._Kn_list:
            x = np.linspace(start, start+1, len(_Kn))
            color = "green" if action == "buy" else "red"
            linewidth = 1 if action == 'buy' else 2
            ax.plot(x, _Kn, color=color, linewidth=linewidth)
            start += 1

        ax.set_xlabel("step")
        ax.set_ylabel("Fn")

    def plot_Kn(self, ax):
        x = range(len(self._random_walk))
        ax.plot(x, self._random_walk, color='blue')
        ax.plot(x, self._kn_list, color='red')
        ax.set_xlabel("step")
        ax.set_ylabel("Kn/Bn")

    def plot_noise(self, ax):
        noise = np.array(self._data_series)[:, 1].astype(float).reshape(-1)
        x = range(noise.shape[0])
        ax.plot(x, noise)
        ax.set_xlabel("step")
        ax.set_ylabel("Noise")

    def plot_participanted_agents(self, ax, agent_type):
        _x = np.arange(len(self._participated_agents))
        _y = np.array(self._participated_agents)
        bar_width = 0.8
        if agent_type == 'N':
            ax.bar(_x - bar_width/2, _y[:, 0], width=bar_width, color='blue')
            ax.bar(_x - bar_width/2, _y[:, 1], width=bar_width, color='blue', bottom=_y[:, 0])
            ax.set_ylabel("N")
        elif agent_type == 'D':
            ax.bar(_x + bar_width/2, _y[:, 2], width=bar_width, color='black')
            ax.bar(_x + bar_width/2, _y[:, 3], width=bar_width, color='black', bottom=_y[:, 2])
            ax.set_ylabel("D")
        elif agent_type == 'E':
            ax.bar(_x + bar_width/2, _y[:, 4], width=bar_width, color='black')
            ax.bar(_x + bar_width/2, _y[:, 5], width=bar_width, color='blue', bottom=_y[:, 4])
            ax.set_ylabel("E")

    def plot(self):
        self.fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6)
        self.plot_Kn(ax1)
        self.plot_Fn(ax2)
        self.plot_price(ax3)
        self.plot_participanted_agents(ax4, agent_type='N')
        self.plot_participanted_agents(ax5, agent_type='D')
        self.plot_participanted_agents(ax6, agent_type='E')

    def show_plot(self):
        self.fig.show()

    def save_plot(self, fname=None, dpi=300):
        fname = "../img/mu-{}-sigma-{}-points-{}.png".format(self._mu,
                                                             self._sigma,
                                                             self._number_of_transactions)
        self.fig.savefig(fname, dpi=dpi)

    def dump_dataset(self):
        # total stocks in market, stocks bought/sold by external agents, current price
        fname = "../training-dataset/mu-{}-sigma-{}-points-{}.csv".format(self._mu,
                                                                          self._sigma,
                                                                          self._number_of_transactions)
        _data = np.array(self._data_series)
        #np.savetxt(fname, _data, fmt="%i, %i, %1.3f, %s", delimiter=',', header="#stocks, #noise, #price, #action")
        np.savetxt(fname, _data, fmt="%s", delimiter=',', header="#stocks, #noise, #price, #walk, #kn, #action")
