import unittest

from src.bounded_agent import (
    Action,
    AuthorityLevel,
    BoundedAgent,
    ToolRegistry,
)


def synthetic_tool(value: str) -> dict:
    return {"value": value, "executed": True}


class TestBoundedAgent(unittest.TestCase):

    def setUp(self):
        self.tools = ToolRegistry()
        self.tools.register("synthetic_tool", synthetic_tool)

    def test_bounded_action_executes(self):
        agent = BoundedAgent(AuthorityLevel.A1_BOUNDED, self.tools)

        action = Action(
            name="bounded action",
            tool="synthetic_tool",
            payload={"value": "test"},
            required_level=AuthorityLevel.A1_BOUNDED,
        )

        result = agent.execute(action)

        self.assertEqual(result.status, "COMPLETED")
        self.assertTrue(result.output["executed"])

    def test_approval_action_stops_without_approval(self):
        agent = BoundedAgent(AuthorityLevel.A2_APPROVAL, self.tools)

        action = Action(
            name="approval action",
            tool="synthetic_tool",
            payload={"value": "test"},
            required_level=AuthorityLevel.A2_APPROVAL,
        )

        result = agent.execute(action)

        self.assertEqual(result.status, "ESCALATED")
        self.assertEqual(result.reason, "Human approval required.")

    def test_approval_action_executes_when_approved(self):
        agent = BoundedAgent(AuthorityLevel.A2_APPROVAL, self.tools)

        action = Action(
            name="approved action",
            tool="synthetic_tool",
            payload={"value": "test"},
            required_level=AuthorityLevel.A2_APPROVAL,
        )

        result = agent.execute(action, approved=True)

        self.assertEqual(result.status, "COMPLETED")

    def test_prohibited_action_never_executes(self):
        agent = BoundedAgent(AuthorityLevel.A3_PROHIBITED, self.tools)

        action = Action(
            name="prohibited action",
            tool="synthetic_tool",
            payload={"value": "test"},
            required_level=AuthorityLevel.A3_PROHIBITED,
        )

        result = agent.execute(action, approved=True)

        self.assertEqual(result.status, "ESCALATED")
        self.assertEqual(result.reason, "Action is prohibited by policy.")


if __name__ == "__main__":
    unittest.main()
