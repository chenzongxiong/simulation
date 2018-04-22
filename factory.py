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
            self.agents.append(klass(name=uuid.uuid4().hex+" - "+agent_name,
                                     **kwargs))

    def total_stocks(self):
        return sum([_agent.state == constants.STATE_WANT_TO_SELL for _agent in self.agents])


if __name__ == "__main__":
    agentn_factory = AgentFactory(agent.AgentN, 10, state=constants.STATE_WANT_TO_SELL)
    assert agentn_factory.total_stocks() == 10
    agentn_factory = AgentFactory(agent.AgentN, 10, state=constants.STATE_WANT_TO_BUY)
    assert agentn_factory.total_stocks() == 0
    agentn_factory = AgentFactory(agent.AgentN, 10)
    LOG.debug("Total stocks of N-type agents is: {}".format(agentn_factory.total_stocks()))

    agentd_factory = AgentFactory(agent.AgentD, 10, state=constants.STATE_WANT_TO_SELL)
    assert agentd_factory.total_stocks() == 10
    agentd_factory = AgentFactory(agent.AgentD, 10, state=constants.STATE_WANT_TO_BUY)
    assert agentd_factory.total_stocks() == 0
    agentd_factory = AgentFactory(agent.AgentD, 10)
    LOG.debug("Total stocks of D-type agents is: {}".format(agentd_factory.total_stocks()))
