"""Cache Result Value Object - represents cache check result"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class CacheResult:
    """
    Cache result value object

    Represents the result of a cache check operation.
    Immutable to ensure result integrity.
    """

    answer: Optional[str]
    cache_hit_layer: Optional[str]  # "cache1", "cache3", "cache4", None
    query_vector: Optional[List[float]]
    is_blocked: bool = False

    def __post_init__(self):
        """Validate cache result"""
        valid_layers = {"cache1", "cache3", "cache4", None, "blocked"}
        if self.cache_hit_layer not in valid_layers:
            raise ValueError(f"Invalid cache_hit_layer: {self.cache_hit_layer}")

        if self.is_blocked and self.cache_hit_layer != "blocked":
            raise ValueError("is_blocked=True requires cache_hit_layer='blocked'")

        if self.cache_hit_layer == "blocked" and not self.is_blocked:
            raise ValueError("cache_hit_layer='blocked' requires is_blocked=True")

    @property
    def is_hit(self) -> bool:
        """Check if cache hit occurred"""
        return self.cache_hit_layer is not None and not self.is_blocked

    @property
    def is_cache1(self) -> bool:
        """Check if Cache #1 hit"""
        return self.cache_hit_layer == "cache1"

    @property
    def is_cache3(self) -> bool:
        """Check if Cache #3 hit"""
        return self.cache_hit_layer == "cache3"

    @property
    def is_cache4(self) -> bool:
        """Check if Cache #4 hit"""
        return self.cache_hit_layer == "cache4"

    @property
    def is_miss(self) -> bool:
        """Check if cache miss"""
        return self.cache_hit_layer is None and not self.is_blocked

    @classmethod
    def hit(cls, answer: str, layer: str, query_vector: Optional[List[float]] = None) -> 'CacheResult':
        """Create cache hit result"""
        return cls(
            answer=answer,
            cache_hit_layer=layer,
            query_vector=query_vector,
            is_blocked=False
        )

    @classmethod
    def miss(cls, query_vector: Optional[List[float]] = None) -> 'CacheResult':
        """Create cache miss result"""
        return cls(
            answer=None,
            cache_hit_layer=None,
            query_vector=query_vector,
            is_blocked=False
        )

    @classmethod
    def blocked(cls) -> 'CacheResult':
        """Create blocked result"""
        return cls(
            answer=None,
            cache_hit_layer="blocked",
            query_vector=None,
            is_blocked=True
        )

    def __repr__(self) -> str:
        if self.is_blocked:
            return "CacheResult(blocked=True)"
        if self.is_hit:
            return f"CacheResult(hit={self.cache_hit_layer}, answer_length={len(self.answer) if self.answer else 0})"
        return "CacheResult(miss=True)"

