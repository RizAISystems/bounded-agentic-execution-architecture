from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable


class AuthorityLevel(IntEnum):
    A0_OBSERVE = 0
    A1_BOUNDED = 1
    A2_APPROVAL = 2
    A3_PROHIBITED = 3


@dataclass
class Action:
    name: str
    tool: str
    payload: dict[str, Any]
    required_level: AuthorityLevel


@dataclass
class ExecutionResult:
    status: str
    action: str
    reason: str
    output: Any = None
    evidence: list[dict[str, Any]] = field(default_factory=list)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = fn

    def execute(self, name: str, payload: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**payload)


class PolicyEngine:
    @staticmethod
    def evaluate(
        action: Action,
        operating_level: AuthorityLevel,
        approved: bool,
    ) -> tuple[bool, str]:

        if action.required_level == AuthorityLevel.A3_PROHIBITED:
            return False, "Action is prohibited by policy."

        if action.required_level == AuthorityLevel.A2_APPROVAL and not approved:
            return False, "Human approval required."

        if action.required_level > operating_level:
            return False, "Current operating authority is insufficient."

        return True, "Authority check passed."


class Validator:
    @staticmethod
    def pre_execute(action: Action) -> tuple[bool, str]:
        if not action.tool:
            return False, "No execution tool specified."

        if not isinstance(action.payload, dict):
            return False, "Payload must be a dictionary."

        return True, "Pre-execution validation passed."

    @staticmethod
    def post_execute(output: Any) -> tuple[bool, str]:
        if output is None:
            return False, "Tool returned no verifiable result."

        return True, "Post-execution validation passed."


class EvidenceLog:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def add(self, event: str, detail: str) -> None:
        self.records.append(
            {
                "event": event,
                "detail": detail,
            }
        )


class BoundedAgent:
    def __init__(
        self,
        operating_level: AuthorityLevel,
        tools: ToolRegistry,
    ) -> None:
        self.operating_level = operating_level
        self.tools = tools

    def execute(
        self,
        action: Action,
        approved: bool = False,
    ) -> ExecutionResult:

        evidence = EvidenceLog()

        evidence.add("ACTION_PROPOSED", action.name)

        allowed, reason = PolicyEngine.evaluate(
            action=action,
            operating_level=self.operating_level,
            approved=approved,
        )

        evidence.add("AUTHORITY_CHECK", reason)

        if not allowed:
            return ExecutionResult(
                status="ESCALATED",
                action=action.name,
                reason=reason,
                evidence=evidence.records,
            )

        valid, reason = Validator.pre_execute(action)
        evidence.add("PRE_VALIDATION", reason)

        if not valid:
            return ExecutionResult(
                status="REJECTED",
                action=action.name,
                reason=reason,
                evidence=evidence.records,
            )

        try:
            output = self.tools.execute(action.tool, action.payload)
            evidence.add("TOOL_EXECUTION", f"{action.tool} executed")
        except Exception as exc:
            evidence.add("EXECUTION_FAILURE", str(exc))

            return ExecutionResult(
                status="FAILED",
                action=action.name,
                reason=str(exc),
                evidence=evidence.records,
            )

        valid, reason = Validator.post_execute(output)
        evidence.add("POST_VALIDATION", reason)

        if not valid:
            return ExecutionResult(
                status="FAILED_VALIDATION",
                action=action.name,
                reason=reason,
                output=output,
                evidence=evidence.records,
            )

        evidence.add("STATE_TRANSITION", "Execution completed successfully")

        return ExecutionResult(
            status="COMPLETED",
            action=action.name,
            reason="Bounded execution completed successfully.",
            output=output,
            evidence=evidence.records,
        )
