import uuid

import agent
import constants
import log as logging

LOG = logging.getLogger(__name__)


class AgentFactory(object):

    def __init__(self,
                 klass,
                 number=1,
                 agent_name="agent",
                 **kwargs):

        kwargs.pop("name", None)
        self.agents = []
        for i in range(number):
            self.agents.append(klass(name=agent_name+"-"+uuid.uuid4().hex,
                                     **kwargs))
        self.name = agent_name
        self.number = number

    @property
    def total_assets(self):
        return sum([_agent.state == constants.STATE_WANT_TO_SELL for _agent in self.agents])

    def __iter__(self):
        self._i = iter(self.agents)
        return self

    def __next__(self):
        _agents = self._i.next()
        return _agents

    def next(self):
        return self.__next__()

    def dumps(self):
        for _agent in self.agents:
            LOG.info(_agent.__repr__())


if __name__ == "__main__":
    agentn_factory = AgentFactory(agent.AgentN, 10)
    LOG.debug("Total stocks of N-type agents is: {}".format(agentn_factory.total_assets))
    agentd_factory = AgentFactory(agent.AgentD, 10)
    LOG.debug("Total stocks of D-type agents is: {}".format(agentd_factory.total_assets))
