import uuid
import numpy
import math

from numpy import random
import agent
import constants
import log as logging

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
    n = - (1.0 / alpha) * numpy.log(1 - delta * (1-numpy.exp(-alpha)) / numpy.exp(-alpha))
    if numpy.isnan(n):
        # n = 10
        n = 100
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
        super(RealAgentN, self).__init__(agent.AgentN, 2*number_of_layer)
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
        super(RealAgentD, self).__init__(agent.AgentD, number)
        for nn in range(0, number):
            self.agents[nn].buying_threshold = beta
            self.agents[nn].selling_threshold = beta
            self.agents[nn].state = state

        self._lowest_bound = beta
        self.buying_threshold = self.selling_threshold = beta
        # self._balance = beta
        self._balance = -1


class RealAgentNFactory(ItertorMixin, IndexMixin):
    def __init__(self,
                 lower_bound_of_delta=0,
                 upper_bound_of_delta=20,
                 C_delta=20,
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

        self.agents = []
        for delta in frange(lower_bound_of_delta,
                            upper_bound_of_delta,
                            step_of_delta):
            num_real_agents = int(round(C_delta*_gamma(delta,
                                                       k_delta,
                                                       theta_delta)))
            for i in range(num_real_agents):
                alpha = C_alpha * random.gamma(k_alpha, theta_alpha)
                alpha0 = random.uniform(-alpha, alpha)
                # n = int(round(numpy.max(roots_of_n(delta, alpha))))
                n = int(round(calculate_n(delta, alpha)))
                LOG.debug("length: {}, balance: {}, alpha: {}, alpha0: {}".format(2*n, delta, alpha, alpha0))

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
        # self._agents_sort_asc_lower = sorted(self.agents, key=attrgetter("_lowest_bound"))
        # self._agents_sort_asc_upper = sorted(self.agents, key=attrgetter("_uppest_bound"))

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


class RealAgentDFactory(ItertorMixin, IndexMixin):

    def __init__(self, lower_bound_of_beta=0,
                 upper_bound_of_beta=20,
                 step_of_beta=0.5,
                 total_stocks_of_N_agents=484,
                 k_beta=2,
                 theta_beta=2):
        self.name = "Real Agent D Factory"
        _sum = 0
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            _sum += _gamma(beta, k_beta, theta_beta)

        B = total_stocks_of_N_agents/_sum
        self.agents = []
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            num_real_agents = int(round(B*_gamma(beta, k_beta, theta_beta)))
            if num_real_agents > 0:
                real_agent1 = RealAgentD(beta, num_real_agents, constants.STATE_WANT_TO_SELL)
                real_agent2 = RealAgentD(beta, num_real_agents, constants.STATE_WANT_TO_BUY)
                self.agents.append(real_agent1)
                self.agents.append(real_agent2)


    @property
    def total_stocks(self):
        return sum([real_agent.total_stocks for real_agent in self.agents])

    @property
    def total_virtual_agents(self):
        return sum([len(real_agent) for real_agent in self.agents])


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
