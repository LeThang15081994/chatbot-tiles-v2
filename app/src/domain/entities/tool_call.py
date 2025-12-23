"""
Tool Call Entity
Represents a tool/function call in the RAG system
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from enum import Enum


class ToolStatus(str, Enum):
    """Tool execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ToolCall:
    """
    Tool call entity

    Represents a function/tool call made by the LLM.
    Part of agent-like behavior in RAG.
    """

    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = field(default_factory=lambda: str(uuid4()))
    status: ToolStatus = ToolStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    result: Optional['ToolResult'] = None
    error: Optional[str] = None

    def mark_executing(self) -> None:
        """Mark tool as executing"""
        self.status = ToolStatus.EXECUTING
        self.executed_at = datetime.now()

    def mark_success(self, result: 'ToolResult') -> None:
        """
        Mark tool execution as successful

        Args:
            result: Tool execution result
        """
        self.status = ToolStatus.SUCCESS
        self.result = result
        if not self.executed_at:
            self.executed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """
        Mark tool execution as failed

        Args:
            error: Error message
        """
        self.status = ToolStatus.FAILED
        self.error = error
        if not self.executed_at:
            self.executed_at = datetime.now()

    def is_search_tool(self) -> bool:
        """Check if this is a search tool"""
        return "search" in self.tool_name.lower()

    def get_execution_time_ms(self) -> Optional[int]:
        """
        Get execution time in milliseconds

        Returns:
            Execution time or None if not executed
        """
        if not self.executed_at:
            return None
        delta = self.executed_at - self.created_at
        return int(delta.total_seconds() * 1000)

    def __repr__(self) -> str:
        return f"ToolCall(name={self.tool_name}, status={self.status.value}, args={self.arguments})"


@dataclass
class ToolResult:
    """
    Tool execution result

    Contains the output from a tool execution.
    """

    output: Any
    result_id: str = field(default_factory=lambda: str(uuid4()))
    tool_name: str = ""
    success: bool = True
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_output_as_string(self) -> str:
        """
        Get output as string representation

        Returns:
            String output
        """
        if isinstance(self.output, str):
            return self.output
        elif isinstance(self.output, (list, dict)):
            import json
            return json.dumps(self.output, ensure_ascii=False)
        else:
            return str(self.output)

    def truncate_output(self, max_length: int = 500) -> str:
        """
        Get truncated output

        Args:
            max_length: Maximum length

        Returns:
            Truncated output
        """
        output_str = self.get_output_as_string()
        if len(output_str) <= max_length:
            return output_str
        return output_str[:max_length] + "..."

    def __repr__(self) -> str:
        output_preview = self.truncate_output(50)
        return f"ToolResult(tool={self.tool_name}, success={self.success}, output='{output_preview}')"

