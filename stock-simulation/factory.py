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
            LOG.info(_agent.__repr__())

    @property
    def length(self):
        return len(self.agents)

class IndexMixin(object):
    def __getitem__(self, key):
        return self.agents[key]

    def __len__(self):
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

    def dumps(self):
        for _agent in self.agents:
            LOG.info(_agent.__repr__())

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

    def _check_tracked_min_ascending(self):
        i = self.agents[0].tracked_min
        for _agent in self.agents:
            if i > _agent.tracked_min:
                return False
            else:
                i = _agent.tracked_min
        return True

    def _check_tracked_max_ascending(self):
        i = self.agents[0].tracked_max
        for _agent in self.agents:
            if i > _agent.tracked_max:
                return False
            else:
                i = _agent.tracked_max
        return True


def roots_of_n(delta, alpha):
    assert abs(alpha) > 1e-5
    return numpy.roots([1, 1, -2.0*delta/alpha])


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
        self._balance = delta
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

        assert self._check_lower_bound_ascending()
        assert self._check_upper_bound_ascending()


class RealAgentD(AgentFactory):
    def __init__(self, beta, number, state):
        assert number > 0 and isinstance(number, int), "The number of agents must be positive integer."
        super(RealAgentD, self).__init__(agent.AgentD, 2*number)
        for nn in range(0, 2*number, 2):
            self.agents[nn].tracked_min = beta
            self.agents[nn].tracked_max = beta
            self.agents[nn].state = state


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
                n = int(round(numpy.max(roots_of_n(delta, alpha))))
                LOG.info("length: {}, balance: {}, alpha: {}, alpha0: {}".format(2*n, delta, alpha, alpha0))

                if n > 0:
                    real_agent = RealAgentN(alpha0, alpha, n, delta)
                    # sanity checking
                    assert real_agent.length == 2*n
                    self.agents.append(real_agent)
                else:
                    LOG.warn("n is negative, ignore it.")

    @property
    def total_stocks(self):
        _total_stocks = 0
        for real_agent in self.agents:
            _total_stocks += real_agent.total_stocks
        return _total_stocks


class RealAgentDFactory(ItertorMixin, IndexMixin):

    def __init__(self, lower_bound_of_beta=0,
                 upper_bound_of_beta=20,
                 step_of_beta=0.5,
                 total_stocks_of_N_agents=484,
                 k=2,
                 theta=2):
        _sum = 0
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            _sum += _gamma(beta, k, theta)

        B = total_stocks_of_N_agents/_sum

        self.agents = []
        for beta in frange(lower_bound_of_beta,
                           upper_bound_of_beta,
                           step_of_beta):
            num_real_agents = int(round(B*_gamma(beta, k, theta)))
            if num_real_agents > 0:
                real_agent1 = RealAgentD(beta, num_real_agents, constants.STATE_WANT_TO_SELL)
                real_agent2 = RealAgentD(beta, num_real_agents, constants.STATE_WANT_TO_BUY)
                self.agents.append(real_agent1)
                self.agents.append(real_agent2)


    @property
    def total_stocks(self):
        _total_stocks = 0
        for real_agent in self.agents:
            _total_stocks += real_agent.total_stocks
        return _total_stocks


if __name__ == "__main__":
    # random.seed(123)
    N_real_agents = RealAgentNFactory()
    print(N_real_agents.length)
    print(N_real_agents.total_stocks)

    D_real_agents = RealAgentDFactory(total_stocks_of_N_agents=N_real_agents.total_stocks)
    print(D_real_agents.length)
    print(D_real_agents.total_stocks)
