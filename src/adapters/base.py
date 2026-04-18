from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import Scenario, SubmissionResult


class BaseAdapter(ABC):
    @abstractmethod
    def submit(self, scenario: Scenario, network: str, gaslimit: int) -> SubmissionResult:
        raise NotImplementedError

    @abstractmethod
    def get_status(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_receipt(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_trace(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def read_state(self, contract_address: str, function_name: str, args: list[Any] | None = None, network: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError
