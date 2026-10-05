from pprint import pprint

from src.bounded_agent import (
    Action,
    AuthorityLevel,
    BoundedAgent,
    ToolRegistry,
)


def send_message(recipient: str, message: str) -> dict:
    return {
        "recipient": recipient,
        "message": message,
        "delivered": True,
    }


tools = ToolRegistry()
tools.register("send_message", send_message)


def run_case(title: str, agent: BoundedAgent, action: Action, approved: bool = False) -> None:
    print(f"\n{'=' * 70}")
    print(title)
    print("=" * 70)

    result = agent.execute(action, approved=approved)

    print(f"Status: {result.status}")
    print(f"Reason: {result.reason}")

    if result.output is not None:
        print("Output:")
        pprint(result.output)

    print("Evidence:")
    for record in result.evidence:
        print(f"  {record['event']}: {record['detail']}")


bounded_action = Action(
    name="Send routine operational notification",
    tool="send_message",
    payload={
        "recipient": "operations@example.com",
        "message": "Synthetic bounded-action demonstration.",
    },
    required_level=AuthorityLevel.A1_BOUNDED,
)

approval_action = Action(
    name="Send externally approved notification",
    tool="send_message",
    payload={
        "recipient": "external@example.com",
        "message": "Synthetic approval-gated demonstration.",
    },
    required_level=AuthorityLevel.A2_APPROVAL,
)

prohibited_action = Action(
    name="Attempt prohibited external action",
    tool="send_message",
    payload={
        "recipient": "restricted@example.com",
        "message": "This action must never execute.",
    },
    required_level=AuthorityLevel.A3_PROHIBITED,
)


run_case(
    "CASE 1: Bounded action executes automatically",
    BoundedAgent(AuthorityLevel.A1_BOUNDED, tools),
    bounded_action,
)

run_case(
    "CASE 2: Approval-gated action is stopped without approval",
    BoundedAgent(AuthorityLevel.A2_APPROVAL, tools),
    approval_action,
)

run_case(
    "CASE 3: Same action executes after explicit approval",
    BoundedAgent(AuthorityLevel.A2_APPROVAL, tools),
    approval_action,
    approved=True,
)

run_case(
    "CASE 4: Prohibited action remains blocked",
    BoundedAgent(AuthorityLevel.A3_PROHIBITED, tools),
    prohibited_action,
    approved=True,
)
