from abc import ABC, abstractmethod
from collections.abc import Iterator


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, *, system: str, user: str, json_mode: bool = False) -> str: ...

    def stream(self, *, system: str, user: str) -> Iterator[str]:
        yield self.generate(system=system, user=user)
