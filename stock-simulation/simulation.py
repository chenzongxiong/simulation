import os
import time
import random
import numpy as np
import matplotlib
# matplotlib.use('Agg')

from matplotlib import pyplot as plt

import log as logging
import agent
import factory
import constants
import colors
from market import get_market, reset_market


LOG = logging.getLogger(__name__)

def plot_agent_distribution(details, title='', xlabel='', ylabel=''):
    import ipdb; ipdb.set_trace()
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

        C_delta = 160
        k_delta = 8
        theta_delta = 1.0


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
        self._participated_agents_list = []
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
        import pandas as pd
        df1 = pd.DataFrame.from_dict(self.agentNs.distribution, orient='index')
        df1.to_csv("./agentn-distribution.csv")
        df2 = pd.DataFrame.from_dict(self.agentNs.distribution2, orient='index')
        df2.to_csv("./agentn-distribution2.csv")

        df3 = pd.DataFrame.from_dict(self.agentDs.distribution, orient='index')
        df3.to_csv("./agentd-distribution.csv")
        df4 = pd.DataFrame.from_dict(self.agentDs.distribution2, orient='index')
        df4.to_csv("./agentd-distribution2.csv")

        df5 = pd.DataFrame.from_dict(self.agentNs.details, orient='index')
        df5.to_csv("./agentn-detail.csv")
        df6 = pd.DataFrame.from_dict(self.agentDs.details, orient='index')
        df6.to_csv("./agentd-detail.csv")

        # import ipdb; ipdb.set_trace()
        # import sys; sys.exit(1)

    def simulate(self, delta=0.01, max_iteration=5000):
        self._internal_transactions = []

        price, noise = 0, self._generate_noise()
        self._curr_num_transactions = 0

        self.market.prices.append(price)
        self._Kn_list = []
        self._ideal_noise_list, self._real_noise_list = [0], [0]

        self._data_series = [(self.total_stocks, noise, price, self._ideal_noise_list[-1], self._real_noise_list[-1], self._action(noise))]

        start = time.time()
        for i in range(self._number_of_transactions + 1):
            self._curr_num_transactions = i
            _price, _noise = price, noise
            LOG.info(colors.yellow("Round #{} ACTION: {}, PRICE: {:.3f}, DELTA: {}, total_stocks: {}, noise/total_stocks is: {:.3f} %".format(i, self._action(_noise), _price, delta, self.total_stocks, abs(_noise/self.total_stocks) * 100)))

            _start = time.time()
            self.agentDs.backup()
            price = self._simulate(_noise, _price, delta, max_iteration)
            _end = time.time()
            LOG.info("Round #{} Time costs: {}".format(i, _end-_start))

            noise = self._generate_noise()
            if price is None:
                # no suitable price found
                while self._action(noise) == self._action(_noise):
                    noise = self._generate_noise()
                price = self.market.prices[-1]

            self._ideal_noise_list.append(_noise + self._ideal_noise_list[-1])
            self._data_series.append((self.total_stocks, noise, price, self._ideal_noise_list[-1], self._real_noise_list[-1], self._action(noise)))

        end = time.time()
        LOG.info("Time elapses: {}".format(end-start))

    def _simulate_helper(self, noise, price, fake=False, delta=0.01, max_iteration=5000):
        noise = noise if fake is False else -noise
        LOG.info("Noise is {}".format(noise))
        state = constants.STATE_WANT_TO_BUY if self._action(noise) == "buy" else constants.STATE_WANT_TO_SELL
        action = self._action(noise)
        direction = self._direction(action)
        # number of external agents
        agentEs = factory.AgentFactory(agent.AgentE, abs(noise), agent_name="Agent-E", state=state)
        for agente in agentEs:
            getattr(agente, action)(price)

        delta = self._direction(action)*delta
        LOG.info("Before jump to next unstable price: total assets in market is: {}".format(self.total_stocks))
        prev_diff, curr_diff = None, self._ballot(price, direction, True)
        LOG.info("first round ballot, curr_diff is: {}".format(curr_diff))

        _stock_list, _price_list = [self.total_stocks + curr_diff], [price]
        failed = True
        for iteration in range(max_iteration):
            price += delta
            prev_diff, curr_diff = curr_diff, self._ballot(price, direction, False)
            _price_list.append(price)
            _stock_list.append(self.total_stocks + curr_diff)
            flag1, flag2 = self.market.exchangable(), self._check_stable_price(prev_diff, curr_diff)
            if flag1 or flag2:
                LOG.info("Before exchanging at stable price: total assets in market is: {}".format(self.total_stocks))
                prev_stocks, curr_ideal_stocks, curr_reality_stocks = self.total_stocks, self.total_stocks + noise, self.total_stocks + noise + curr_diff
                if fake is False:
                    self._real_noise_list.append(self._real_noise_list[-1] + curr_diff + noise)
                    # participanted_agents = [self.market._buying_agentNs, self.market._selling_agentNs,
                    #                         self.market._buying_agentDs, self.market._selling_agentDs,
                    #                         *(lambda x: (x, 0) if x > 0 else (0, x))(noise + curr_diff)]
                    participanted_agents = [self.market._buying_agentNs, self.market._selling_agentNs,
                                            self.market._buying_agentDs, self.market._selling_agentDs]
                    if noise + curr_diff > 0:
                        participanted_agents += [noise+curr_diff, 0]
                    else:
                        participanted_agents += [0, noise+curr_diff]

                    self._participated_agents_list.append(participanted_agents)
                    self.market.exchange(price)
                    failed = False
                else:
                    self.agentDs.restore()
                    self.market.reset()
                    failed = True

                LOG.info("After exchanging at stable price: total assets in market is: {}".format(self.total_stocks))
                LOG.info("Iteration #{}: reach stability price: {:.3f}. current difference is: {}, previous difference is: {}".format(iteration, price, curr_diff, prev_diff))
                break

            self.market.restore()
            if iteration % 1000 == 0:
                LOG.info("Iteration #{}: price {}. Previous difference is: {}, Current difference is: {}".format(iteration, price, prev_diff, curr_diff))
                LOG.info("#{} agents want to buy stocks, #{} agents want to sell stocks".format(self.market.number_of_buyers, self.market.number_of_sellers))

        if fake is True or failed is True:
            LOG.error(colors.red("Faked: {}, Max iteration #{} reaches, price {} fail to find a solution for this transaction.".format(fake, max_iteration, price)))
            self.agentDs.restore()
            self.market.reset()
            # enforce price to be None, since it's fake or failed
            price = None
        else:
            self._Kn_list.append((_stock_list, action))
            if len(self._Kn_list) >= 2:
                # NOTE: enforce line continuous, don't remove
                self._Kn_list[-2][0].append(_stock_list[0])

        LOG.info("Factory N has {} stocks, Factory D has {} stocks, Total assets in market is {}.".format(self.agentNs.total_stocks, self.agentDs.total_stocks, self.total_stocks))
        return price, _price_list, _stock_list, prev_stocks, curr_ideal_stocks, curr_reality_stocks, failed

    def _simulate(self, noise, price, delta=0.01, max_iteration=5000):
        delta = 0.001

        fake_price, fake_price_list, fake_stock_list, fake_prev_stocks, fake_curr_ideal_stocks, fake_curr_reality_stocks, fake_failed = self._simulate_helper(noise, price, fake=True, delta=delta, max_iteration=max_iteration)
        price, price_list, stock_list, prev_stocks, curr_ideal_stocks, curr_reality_stocks, failed = self._simulate_helper(noise, price, fake=False, delta=delta, max_iteration=max_iteration)

        fake_stock_list = [i - noise for i in fake_stock_list]
        stock_list = [i + noise for i in stock_list]
        stacked_price_list = np.array([fake_price_list, price_list])
        stacked_stock_list = np.array([fake_stock_list, stock_list])
        stacked_prev_stocks = np.array([fake_prev_stocks, prev_stocks])
        stacked_curr_ideal_stocks = np.array([fake_curr_ideal_stocks, curr_ideal_stocks])
        stacked_curr_reality_stocks = np.array([fake_curr_reality_stocks, curr_reality_stocks])

        self.plot_price_stocks(stacked_price_list,
                               stacked_stock_list,
                               stacked_prev_stocks,
                               stacked_curr_ideal_stocks,
                               stacked_curr_reality_stocks,
                               failed)
        return price

    def _check_stable_price(self, t1, t2):
        return t1*t2 <= 0 and t1 != 0

    def _generate_noise(self, from_pre_generated=False):
        """Generate external agents from gaussian distribution. This function ensures
        the number of external agnets must be integral and non-zero"""
        # from_pre_generated = True
        if from_pre_generated is True:
            if not getattr(self, "_load_from_file", None):
                # fname = '../../feng/new-dataset/models/diff_weights/method-sin/activation-None/state-0/markov_chain/mu-0/sigma-110/units-20/nb_plays-20/points-1000/input_dim-1/predictions-mu-0-sigma-110-points-1000/activation#-elu/state#-0/units#-100/nb_plays#-100/ensemble-11/loss-mle/predictions-batch_size-1500-debug-4.csv'
                fname = '/Users/zxchen/predictions-batch_size-1500.csv'
                data = np.loadtxt(fname, skiprows=0, delimiter=",", dtype=np.float32)
                self._noise_outputs = data[:, 1]
                self._noise_step = 1
                self._noise_index = 0
                self._pre_noise = int(round(self._noise_outputs[0]))

                self._load_from_file = True

            _noise = 0
            while _noise == 0:
                _noise = int(round(self._noise_outputs[self._noise_index])) - self._pre_noise
                self._noise_index += self._noise_step
            self._pre_noise = _noise
            return _noise

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
        ax.set_xlabel("step")
        ax.set_ylabel("price")

    def plot_Kn(self, ax):
        for start, (_Kn, action) in zip(range(len(self._Kn_list)), self._Kn_list):
            x = np.linspace(start, start+1, len(_Kn))
            color = "green" if action == "buy" else "red"
            ax.plot(x, _Kn, color=color, linewidth=1)

        ax.set_xlabel("step")
        ax.set_ylabel("Kn")

    def plot_noise(self, ax):
        x = range(len(self._ideal_noise_list))
        ax.plot(x, self._ideal_noise_list, color='blue')
        ax.plot(x, self._real_noise_list, color='red')
        ax.set_xlabel("step")
        ax.set_ylabel("Noise Ideal/Reality")

    def plot_participanted_agents(self, ax, agent_type):
        _x = np.arange(len(self._participated_agents_list))
        _y = np.array(self._participated_agents_list)
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
        self.plot_noise(ax1)
        self.plot_Kn(ax2)
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
        np.savetxt(fname, _data, fmt="%s", delimiter=',', header="#stocks, #noise, #price, #walk, #kn, #action")

        participated_agents_fname = "../training-dataset/mu-{}-sigma-{}-points-{}-participanted-agents.csv".format(self._mu,
                                                                                                                   self._sigma,
                                                                                                                   self._number_of_transactions)
        participated_agents_data = np.array(self._participated_agents_list)
        np.savetxt(participated_agents_fname, participated_agents_data, fmt="%s", delimiter=',', header="agentN1,agentN2,agentD1,agentD2,agentE1,agentE2")


    def plot_price_stocks(self, prices, stocks, B1, B2, B3, failed=False):
        '''
        prices: the prices attemped find a root
        stocks: stocks changes corresponding to the changes of prices
        B1: the start line
        B2: the ideal line should reach
        B3: the real line reached
        index: the number of the transaction (or transaction id)
        mu, sigma: meta data
        failed: a flag to show whether the transaction is failure or success
        '''
        fig = plt.figure()
        fake_price_list, price_list = np.array(prices[0]), np.array(prices[1])
        fake_stock_list, stock_list = np.array(stocks[0]) - self._baseline_total_stocks, np.array(stocks[1]) - self._baseline_total_stocks
        B1, B2, B3 = B1 - self._baseline_total_stocks, B2 - self._baseline_total_stocks, B3 - self._baseline_total_stocks
        fake_B1, _B1 = B1[0], B1[1]
        fake_B2, _B2 = B2[0], B2[1]
        fake_B3, _B3 = B3[0], B3[1]

        fname1 = '../training-dataset/mu-{}-sigma-{}-points-{}/{}-brief.csv'.format(self._mu, self._sigma, self._number_of_transactions, self._curr_num_transactions)
        fname2 = '../training-dataset/mu-{}-sigma-{}-points-{}/{}-true-detail.csv'.format(self._mu, self._sigma, self._number_of_transactions, self._curr_num_transactions)
        fname3 = '../training-dataset/mu-{}-sigma-{}-points-{}/{}-fake-detail.csv'.format(self._mu, self._sigma, self._number_of_transactions, self._curr_num_transactions)
        os.makedirs(os.path.dirname(fname1), exist_ok=True)
        # # NOTE: header="#fake_start_line, #fake_ideal_line_should_reach, #fake_line_reached, #start_line, #ideal_line_should_reach, #line_reached
        _data1 = np.hstack([fake_B1, fake_B2, fake_B3, _B1, _B2, _B3])
        np.savetxt(fname1, _data1, fmt="%s", delimiter=',')
        # NOTE: header="#price_list, #stock_list""
        _data2 = np.vstack([price_list, stock_list]).T
        np.savetxt(fname2, _data2, fmt="%s", delimiter=',')
        # NOTE: header="#fake_price_list, #fake_stock_list"
        _data3 = np.vstack([fake_price_list, fake_stock_list]).T
        np.savetxt(fname3, _data3, fmt="%s", delimiter=',')

        if np.all(fake_price_list[1:] - fake_price_list[:-1] >= 0):
            fake_color = 'black'
            fake_txt = "INCREASE"
        else:
            fake_color = 'blue'
            fake_txt = 'DECREASE'

        if np.all(price_list[1:] - price_list[:-1] >= 0):
            color = 'black'
            txt = "INCREASE"
        else:
            color = 'blue'
            txt = 'DECREASE'

        fake_l = 10 if len(fake_price_list) == 1 else len(fake_price_list)
        l = 10 if len(price_list) == 1 else len(price_list)

        fake_B1, fake_B2, fake_B3 = np.array([fake_B1]*fake_l), np.array([fake_B2]*fake_l), np.array([fake_B3]*fake_l)
        _B1, _B2, _B3 = np.array([_B1]*l), np.array([_B2]*l), np.array([_B3]*l)

        plt.plot(fake_price_list, fake_B1, 'r', fake_price_list, fake_B2, 'c--', fake_price_list, fake_B3, 'k--')
        plt.plot(price_list, _B1, 'r', price_list, _B2, 'c', price_list, _B3, 'k-')
        plt.plot(fake_price_list, fake_stock_list, color=fake_color, marker='^', markersize=2, linestyle='--')
        plt.plot(price_list, stock_list, color=color, marker='o', markersize=2)
        plt.text(fake_price_list.mean(), fake_stock_list.mean(), fake_txt)
        plt.text(price_list.mean(), stock_list.mean(), txt)
        plt.xlabel("Prices")
        plt.ylabel("#Stocks")

        # plt.show()
        if failed is True:
            fname = './frames-mu-{}-sigma-{}/{}-failed.png'.format(self._mu, self._sigma, self._curr_num_transactions)
        else:
            fname = './frames-mu-{}-sigma-{}/{}.png'.format(self._mu, self._sigma, self._curr_num_transactions)
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        fig.savefig(fname, dpi=400)

    def simulate2(self):
        '''
        Generate noise(Pn+Pd) from price.
        '''

        # fname = '/Users/zxchen/predictions-batch_size-1500-first-up-1500-points.csv'
        fname = '../predictions-batch_size-1500-debug-6.csv'
        data = np.loadtxt(fname, skiprows=0, delimiter=",", dtype=np.float32)
        self._prices = data[:, 0]
        self._Pnd = [self.agentDs.total_stocks + self.agentNs.total_stocks]
        self._Pn = [self.agentNs.total_stocks]
        self._Pd = [self.agentDs.total_stocks]

        self.market.prices.append(self._prices[0])
        loop = self._prices.shape[0]
        # loop = 10

        direction = None

        for i in range(1, loop):
            self._ballot(self._prices[i], direction)
            self.market.exchange(self._prices[i])

            self._Pnd.append(self.agentDs.total_stocks + self.agentNs.total_stocks)
            self._Pn.append(self.agentNs.total_stocks)
            self._Pd.append(self.agentDs.total_stocks)


        # import ipdb; ipdb.set_trace()
        self._Pnd = np.array(self._Pnd)
        self._Pn = np.array(self._Pn)
        self._Pd = np.array(self._Pd)
        self._prices = self._prices[:loop]
        self._noise = data[:loop, 1]
        res = np.vstack([self._prices, self._Pn, self._Pd, self._Pnd, self._noise]).T
        fname = "{}-base.csv".format(fname[:-4])
        np.savetxt(fname, res, fmt="%.3f", delimiter=",")

        self.fig, (ax1, ax2, ax3, ax4) = plt.subplots(4)

        x = range(len(self._Pnd))
        ax1.plot(x, self._Pnd, color='blue')
        ax1.set_xlabel("step")
        ax1.set_ylabel("Pnd")

        ax2.set_xlabel("step")
        ax2.plot(x, data[:, 1][:len(x)], color='red')
        ax2.set_ylabel("NN")

        ax3.plot(x, self._Pn, color='blue')
        ax3.set_xlabel("step")
        ax3.set_ylabel("Pn")

        ax4.plot(x, self._Pd, color='blue')
        ax4.set_xlabel("step")
        ax4.set_ylabel("Pd")
        plt.show()
        fname = "{}-base.png".format(fname[:-4])
        self.fig.savefig(fname, dpi=400)
