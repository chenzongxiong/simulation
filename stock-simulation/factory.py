import uuid
import agent
from agent import STATE_WANT_TO_BUY, STATE_WANT_TO_SELL


class AgentFactory(object):

    def __init__(self,
                 klass,
                 number=1,
                 agent_name="agent",
                 **kwargs):

        kwargs.pop("name", None)
        self.agents = []
        for i in range(number):
            _agent = klass(name=uuid.uuid4().hex+" - "+agent_name,
                           **kwargs)

            self.agents.append(_agent)

    def total_stocks(self):
        counts = 0
        for _agent in self.agents:
            if _agent.state == STATE_WANT_TO_SELL:
                counts += 1

        return counts


if __name__ == "__main__":
    agentn_factory = AgentFactory(agent.AgentN, 10, state=STATE_WANT_TO_SELL)
    assert agentn_factory.total_stocks() == 10
    agentn_factory = AgentFactory(agent.AgentN, 10, state=STATE_WANT_TO_BUY)
    assert agentn_factory.total_stocks() == 0
    agentn_factory = AgentFactory(agent.AgentN, 10)
    print("Total stocks of N-type agents is: {}".format(agentn_factory.total_stocks()))

    agentd_factory = AgentFactory(agent.AgentD, 10, state=STATE_WANT_TO_SELL)
    assert agentd_factory.total_stocks() == 10
    agentd_factory = AgentFactory(agent.AgentD, 10, state=STATE_WANT_TO_BUY)
    assert agentd_factory.total_stocks() == 0
    agentd_factory = AgentFactory(agent.AgentD, 10)
    print("Total stocks of D-type agents is: {}".format(agentd_factory.total_stocks()))
