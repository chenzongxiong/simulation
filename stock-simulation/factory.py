import uuid
import numpy
import math

from numpy import random
import numpy as np
import agent
import constants
import log as logging
import colors
import matplotlib.pyplot as plt

LOG = logging.getLogger(__name__)


class ItertorMixin(object):
    def __iter__(self):
        self._i = iter(self.agents)
        return self

    def __next__(self):
        try:
            _agents = self._i.next()
        except AttributeError:
            _agents = self._i.__next__()

        return _agents

    def next(self):
        return self.__next__()

    def dumps(self):
        for _agent in self.agents:
            LOG.debug(_agent.__repr__())


class IndexMixin(object):
    def __getitem__(self, key):
        return self.agents[key]

    def __len__(self):
        return len(self.agents)

    @property
    def length(self):
        return len(self.agents)


class AgentFactory(ItertorMixin, IndexMixin):

    def __init__(self,
                 klass,
                 number=1,
                 agent_name="agent",
                 balance=0.0,
                 **kwargs):

        kwargs.pop("name", None)
        self.agents = []

        for i in range(number):
            self.agents.append(klass(name=agent_name+"-"+uuid.uuid4().hex,
                                     **kwargs))
        self.name = agent_name
        self.number = number
        # if a factory has no balance, although `buying_signal` occurs,
        # it couldn't buy stock/bitcoin from market.
        self._balance = balance
        self._agent_arranged = False

    @property
    def total_stocks(self):
        return sum([_agent.state == constants.STATE_WANT_TO_SELL for _agent in self.agents])

    def _arrange_agents(self):
        self._agent_arranged = True

    def _check_lower_bound_ascending(self):
        i = self.agents[0].lower_bound
        for _agent in self.agents:
            if i > _agent.lower_bound:
                return False
            else:
                i = _agent.lower_bound
        return True

    def _check_upper_bound_ascending(self):
        i = self.agents[0].upper_bound

        for _agent in self.agents:
            if i > _agent.upper_bound:
                return False
            else:
                i = _agent.upper_bound
        return True

    def _check_buying_threshold_ascending(self):
        i = self.agents[0].buying_threshold
        for _agent in self.agents:
            if i > _agent.buying_threshold:
                return False
            else:
                i = _agent.buying_threshold
        return True

    def _check_selling_threshold_ascending(self):
        i = self.agents[0].selling_threshold
        for _agent in self.agents:
            if i > _agent.selling_threshold:
                return False
            else:
                i = _agent.selling_threshold
        return True


def roots_of_n(delta, alpha):
    assert abs(alpha) > 1e-5
    return numpy.roots([1, 1, -2.0*delta/alpha])


def calculate_n(delta, alpha):
    # x = 1 - delta * (1-numpy.exp(-alpha))
    n = - (1.0 / alpha) * numpy.log(1 - delta * (1-numpy.exp(-alpha)) / numpy.exp(-alpha))
    # import ipdb; ipdb.set_trace()
    if numpy.isnan(n):
        n = 80
        LOG.debug(colors.red("fail to calcuate N, set to {}".format(n)))

    # n = 20
    return n


def _gamma(x, k, theta):
    return x**k * math.exp(-x/theta) / math.gamma(k)


def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


class RealAgentN(AgentFactory):
    def __init__(self, alpha0, alpha, number_of_layer=0, delta=0.0):
        assert number_of_layer > 0 and isinstance(number_of_layer, int), \
          "number_of_layer must be positive integer"
        super(RealAgentN, self).__init__(agent.AgentN, 2*number_of_layer, agent_name="Agent-N")
        self._number_of_layer = number_of_layer

        for nn in range(0, 2*number_of_layer):
            lower_bound = alpha0 + (nn-number_of_layer)*alpha

            self.agents[nn].lower_bound = lower_bound
            self.agents[nn].upper_bound = lower_bound + alpha

            if lower_bound >= 0:
                self.agents[nn].state = constants.STATE_WANT_TO_SELL
            else:
                self.agents[nn].state = constants.STATE_WANT_TO_BUY

        # sanity check
        if alpha0 >= 0:
            assert self.total_stocks == number_of_layer
        else:
            assert self.total_stocks == number_of_layer-1

        # NOTE: make sure the agents are well arranged
        assert self._check_lower_bound_ascending()
        assert self._check_upper_bound_ascending()

        self._lowest_bound = self.agents[0].lower_bound
        self._uppest_bound = self.agents[2*number_of_layer-1].upper_bound
        self._balance = delta


class RealAgentD(AgentFactory):
    def __init__(self, beta, number, state):
        assert number > 0 and isinstance(number, int), "The number of agents must be positive integer."
        super(RealAgentD, self).__init__(agent.AgentD, number, agent_name="Agent-D")
        for nn in range(0, number):
            self.agents[nn].buying_threshold = beta
            self.agents[nn].selling_threshold = beta
            self.agents[nn].state = state

        self._lowest_bound = beta
        self.buying_threshold = self.selling_threshold = beta
        self._balance = beta


class RealAgentNFactory(ItertorMixin, IndexMixin):
    def __init__(self,
                 lower_bound_of_delta=0,
                 upper_bound_of_delta=20,
                 C_delta=1,
                 k_delta=7.5,
                 theta_delta=1.0,
                 C0_delta=2,
                 C_alpha=1,
                 k_alpha=2,
                 theta_alpha=2):

        random.seed(123)
        numpy.random.RandomState(seed=123)

        self.name = "Real Agent N Factory"
        step_of_delta = 1.0/C0_delta
        # step_of_delta = 0.1
        self._alpha_list = []
        self.agents = []
        self._num_of_agents_list = []
        self._delta_list = []
        C_alpha = 1
        k_alpha = 2
        theta_alpha = 2

        lower_bound_of_delta = 0
        upper_bound_of_delta = 40

        for delta in frange(lower_bound_of_delta,
                            upper_bound_of_delta,
                            step_of_delta):
            num_real_agents = int(round(C_delta*_gamma(delta,
                                                       k_delta,
                                                       theta_delta)))
            self._delta_list.append(delta)
            self._num_of_agents_list.append(num_real_agents)

            for i in range(num_real_agents):
                # alpha = C_alpha * random.gamma(k_alpha, theta_alpha) / 2000
                # alpha = C_alpha * random.gamma(k_alpha, theta_alpha) / 100
                alpha = C_alpha * random.gamma(k_alpha, theta_alpha) / 100

                self._alpha_list.append(alpha)
                alpha0 = random.uniform(-alpha, alpha)
                n = int(round(calculate_n(delta, alpha)))
                LOG.debug("length: {}, delta/balance: {}, alpha: {:.5f}, alpha0: {:.5f}".format(2*n, delta, alpha, alpha0))

                if n > 0:
                    real_agent = RealAgentN(alpha0, alpha, n, delta)
                    # sanity checking
                    assert real_agent.length == 2*n
                    self.agents.append(real_agent)
                else:
                    LOG.warn("n is negative, ignore it.")

        # arrange real agents N ascendingly
        from operator import itemgetter, attrgetter
        self.agents = sorted(self.agents, key=attrgetter("_lowest_bound"))
        self._agents_sort_asc_lower = sorted(self.agents, key=attrgetter("_lowest_bound"))
        self._agents_sort_asc_upper = sorted(self.agents, key=attrgetter("_uppest_bound"))

        self._alpha_list.sort()
        self._alpha_list = np.array(self._alpha_list)

        # self._num_of_agents_list = np.array(self._num_of_agents_list)
        # plt.plot(self._delta_list, self._num_of_agents_list)

        # plt.hist(self._alpha_list, bins=50)
        # plt.show()
        # import ipdb; ipdb.set_trace()
        # self._lowest_bound = self.agents[0]._lowest_bound
        # self._uppest_bound = self.agents[-1]._uppest_bound
        self._lowest_bound = self._agents_sort_asc_lower[0]._lowest_bound
        self._uppest_bound = self._agents_sort_asc_upper[-1]._uppest_bound

    def set_agents_sort_asc_lower(self):
        self.agents = self._agents_sort_asc_lower

    def set_agents_sort_asc_upper(self):
        self.agents = self._agents_sort_asc_upper

    @property
    def total_stocks(self):
        return sum([real_agent.total_stocks for real_agent in self.agents])

    @property
    def total_virtual_agents(self):
        return sum([len(real_agent) for real_agent in self.agents])

    @property
    def min_width(self):
        min_width_ = float('inf')
        for real_agent in self.agents:
            for agent in real_agent:
                if min_width_ > (agent.upper_bound - agent.lower_bound):
                    min_width_ = agent.upper_bound - agent.lower_bound
        return min_width_

    @property
    def max_width(self):
        max_width_ = -float('inf')
        for real_agent in self.agents:
            for agent in real_agent:
                if max_width_ < (agent.upper_bound - agent.lower_bound):
                    max_width_ = agent.upper_bound - agent.lower_bound

        return max_width_

    @property
    def min_width_real_agent(self):
        min_width_ = float('inf')
        for real_agent in self.agents:
            if min_width_ > real_agent._uppest_bound - real_agent._lowest_bound:
                min_width_ = real_agent._uppest_bound - real_agent._lowest_bound

        return min_width_

    @property
    def max_width_real_agent(self):
        max_width_ = -float('inf')
        for real_agent in self.agents:
            if max_width_ < real_agent._uppest_bound - real_agent._lowest_bound:
                max_width_ = real_agent._uppest_bound - real_agent._lowest_bound

        return max_width_


    @property
    def distribution(self):
        from operator import itemgetter, attrgetter
        agents = sorted(self.agents, key=attrgetter("_balance"))
        _distribution = {}
        for real_agent in agents:
            _distribution[real_agent._balance] = 0

        for real_agent in agents:
            _distribution[real_agent._balance] += len(real_agent.agents)

        return _distribution

    @property
    def distribution2(self):
        from operator import itemgetter, attrgetter
        agents = sorted(self.agents, key=attrgetter("_balance"))
        _distribution = {}
        for real_agent in agents:
            _distribution[real_agent._balance] = 0

        for real_agent in agents:
            _distribution[real_agent._balance] += 1

        return _distribution


    @property
    def details(self):
        # _details = {}
        # for real_agent in self.agents:
        #     for agent in real_agent:
        #         width = agent._upper_bound - agent._lower_bound
        #         k1 = 'buy-{:.5f}'.format(width)
        #         k2 = 'sell-{:.5f}'.format(width)
        #         if k1 not in _details:
        #             _details[k1] = 0
        #         if k2 not in _details:
        #             _details[k2] = 0
        #         if agent.state == constants.STATE_WANT_TO_BUY:
        #             _details[k1] += 1
        #         if agent.state == constants.STATE_WANT_TO_SELL:
        #             _details[k2] += 1

        # return _details

        _details = {}

        for real_agent in self.agents:
            width = (real_agent._uppest_bound - real_agent._lowest_bound) / (2 * len(real_agent))
            print("width: {}".format(width))
            k1 = 'buy-{:.5f}'.format(width)
            k2 = 'sell-{:.5f}'.format(width)
            if k1 not in _details:
                _details[k1] = 0
            if k2 not in _details:
                _details[k2] = 0

            for agent in real_agent:
                if agent.state == constants.STATE_WANT_TO_BUY:
                    _details[k1] += 1
                if agent.state == constants.STATE_WANT_TO_SELL:
                    _details[k2] += 1
        import ipdb; ipdb.set_trace()
        return _details


class RealAgentDFactory(ItertorMixin, IndexMixin):

    def __init__(self, lower_bound_of_beta=0.01,
                 upper_bound_of_beta=0.5,
                 step_of_beta=0.5,
                 total_stocks_of_N_agents=484,
                 k_beta=2,
                 theta_beta=2):
        self.name = "Real Agent D Factory"
        # step_of_beta = 0.13
        # step_of_beta = 0.13
        step_of_beta = 0.0015
        lower_bound_of_beta = 0.001
        # upper_bound_of_beta = 0.2
        upper_bound_of_beta = 0.2
        _sum = 0
        factor = 80
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            beta *= factor
            _sum += _gamma(beta, k_beta, theta_beta)

        import ipdb; ipdb.set_trace()
        B = total_stocks_of_N_agents/_sum
        B *= 0.2
        self.agents = []
        self._cdf = [0]
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            beta *= factor
            num_real_agents = int(round(B*_gamma(beta, k_beta, theta_beta)))
            if num_real_agents > 0:
                real_agent1 = RealAgentD(beta/factor, num_real_agents, constants.STATE_WANT_TO_SELL)
                real_agent2 = RealAgentD(beta/factor, num_real_agents, constants.STATE_WANT_TO_BUY)
                self.agents.append(real_agent1)
                self.agents.append(real_agent2)
                self._cdf.append(self._cdf[-1] + num_real_agents)

    @property
    def total_stocks(self):
        return sum([real_agent.total_stocks for real_agent in self.agents])

    @property
    def total_virtual_agents(self):
        return sum([len(real_agent) for real_agent in self.agents])

    @property
    def min_threshold(self):
        min_buying_threshold = float('inf')
        min_selling_threshold = float('inf')
        for real_agent in self.agents:
            for agent in real_agent:
                if min_buying_threshold > agent.buying_threshold:
                    min_buying_threshold = agent.buying_threshold
                if min_selling_threshold > agent.selling_threshold:
                    min_selling_threshold = agent.selling_threshold
        return (min_buying_threshold, min_selling_threshold)

    @property
    def max_threshold(self):
        max_buying_threshold = -float('inf')
        max_selling_threshold = -float('inf')
        for real_agent in self.agents:
            for agent in real_agent:
                if max_buying_threshold < agent.buying_threshold:
                    max_buying_threshold = agent.buying_threshold
                if max_selling_threshold < agent.selling_threshold:
                    max_selling_threshold = agent.selling_threshold

        return (max_buying_threshold, max_selling_threshold)

    @property
    def distribution(self):
        'number of/distribution of virtual agents'
        from operator import itemgetter, attrgetter
        agents = sorted(self.agents, key=attrgetter("_balance"))
        _distribution = {}
        for real_agent in agents:
            _distribution[real_agent._balance] = 0

        for real_agent in agents:
            _distribution[real_agent._balance] += len(real_agent.agents)

        return _distribution

    @property
    def distribution2(self):
        'number of/distribution of real agents'
        _distribution = {}
        return _distribution

    @property
    def details(self):
        _details = {}
        for real_agent in self.agents:
            for agent in real_agent:
                k1 = 'buy-{}'.format(agent.buying_threshold)
                k2 = 'sell-{}'.format(agent.selling_threshold)
                if k1 not in _details:
                    _details[k1] = 0
                if k2 not in _details:
                    _details[k2] = 0
                if agent.state == constants.STATE_WANT_TO_BUY:
                    _details[k1] += 1
                if agent.state == constants.STATE_WANT_TO_SELL:
                    _details[k2] += 1
        print(self._cdf)
        import ipdb; ipdb.set_trace()
        return _details


    def backup(self):
        self._backup_min_max = []
        for i, real_agent in enumerate(self.agents):
            self._backup_min_max.append([])
            for agent in real_agent:
                self._backup_min_max[i].append((agent._tracked_min, agent._tracked_max))

    def restore(self):
        for i in range(len(self._backup_min_max)):
            for j in range(len(self._backup_min_max[i])):
                tracked_min, tracked_max = self._backup_min_max[i][j]
                self.agents[i][j]._tracked_min = tracked_min
                self.agents[i][j]._tracked_max = tracked_max


if __name__ == "__main__":
    # random.seed(123)
    N_real_agents = RealAgentNFactory()
    print("Number of N real agents: {}".format(N_real_agents.length))
    print("Number of stocks belonged to N real agents: {}".format(N_real_agents.total_stocks))
    print("Number of virtual agents belonged to N real agents: {}".format(N_real_agents.total_virtual_agents))

    D_real_agents = RealAgentDFactory(total_stocks_of_N_agents=N_real_agents.total_stocks)
    print("Number of D real agents: {}".format(D_real_agents.length))
    print("Number of stocks belonged to D real agents: {}".format(D_real_agents.total_stocks))
    print("Number of virtual agents belonged to D real agents: {}".format(D_real_agents.total_virtual_agents))

    lowest_bounds = []
    N_real_agents.set_agents_sort_asc_lower()
    for real_agent in N_real_agents:
        lowest_bounds.append(real_agent._lowest_bound)
    print("N lowest_bounds: ", lowest_bounds)

    lowest_bounds = []
    for real_agent in D_real_agents:
        lowest_bounds.append(real_agent._lowest_bound)
    print("D lowest_bounds: ", lowest_bounds)


    uppest_bounds = []
    N_real_agents.set_agents_sort_asc_upper()
    for real_agent in N_real_agents:
        uppest_bounds.append(real_agent._uppest_bound)
    print("N uppest_bounds: ", uppest_bounds)
