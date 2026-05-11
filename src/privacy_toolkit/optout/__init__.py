"""Opt-out subsystem: workflow engine, status machine, manual steps."""

from privacy_toolkit.optout.workflow import OptOutWorkflow, WorkflowResult
from privacy_toolkit.optout.status_machine import validate_transition, allowed_transitions

__all__ = ["OptOutWorkflow", "WorkflowResult", "validate_transition", "allowed_transitions"]
