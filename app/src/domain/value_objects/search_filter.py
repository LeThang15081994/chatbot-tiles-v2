"""
Search Filter Value Object
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class FilterOperator(str, Enum):
    """Filter operator enumeration"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


@dataclass(frozen=True)
class SearchFilter:
    """
    Search filter value object

    Represents metadata filters for search operations.
    Immutable to ensure filter consistency.
    """

    filters: Dict[str, Any]
    operator: str = "AND"  # AND, OR

    def __post_init__(self):
        """Validate search filter"""
        if not isinstance(self.filters, dict):
            raise ValueError("filters must be a dictionary")

        if self.operator not in ["AND", "OR"]:
            raise ValueError("operator must be AND or OR")

    @classmethod
    def empty(cls) -> 'SearchFilter':
        """
        Create empty filter

        Returns:
            Empty SearchFilter
        """
        return cls(filters={})

    @classmethod
    def by_source(cls, source: str) -> 'SearchFilter':
        """
        Create filter by source

        Args:
            source: Source value

        Returns:
            SearchFilter for source
        """
        return cls(filters={"source": source})

    @classmethod
    def by_category(cls, category: str) -> 'SearchFilter':
        """
        Create filter by category

        Args:
            category: Category value

        Returns:
            SearchFilter for category
        """
        return cls(filters={"category": category})

    @classmethod
    def by_date_range(
        cls,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> 'SearchFilter':
        """
        Create filter by date range

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            SearchFilter for date range
        """
        filters = {}
        if start_date:
            filters["date_gte"] = start_date.isoformat()
        if end_date:
            filters["date_lte"] = end_date.isoformat()
        return cls(filters=filters)

    @classmethod
    def by_tags(cls, tags: List[str]) -> 'SearchFilter':
        """
        Create filter by tags

        Args:
            tags: List of tags

        Returns:
            SearchFilter for tags
        """
        return cls(filters={"tags": {"$in": tags}})

    def is_empty(self) -> bool:
        """
        Check if filter is empty

        Returns:
            True if no filters
        """
        return len(self.filters) == 0

    def has_filter(self, key: str) -> bool:
        """
        Check if filter has specific key

        Args:
            key: Filter key

        Returns:
            True if key exists
        """
        return key in self.filters

    def get_filter_value(self, key: str, default: Any = None) -> Any:
        """
        Get filter value by key

        Args:
            key: Filter key
            default: Default value

        Returns:
            Filter value
        """
        return self.filters.get(key, default)

    def combine_with(
        self,
        other: 'SearchFilter',
        operator: str = "AND"
    ) -> 'SearchFilter':
        """
        Combine with another filter

        Args:
            other: Other SearchFilter
            operator: Combination operator (AND/OR)

        Returns:
            Combined SearchFilter
        """
        if self.is_empty():
            return other
        if other.is_empty():
            return self

        combined_filters = {
            "$" + operator.lower(): [
                self.filters,
                other.filters
            ]
        }
        return SearchFilter(filters=combined_filters, operator=operator)

    def to_milvus_expr(self) -> str:
        """
        Convert to Milvus expression format

        Returns:
            Milvus filter expression
        """
        if self.is_empty():
            return ""

        expressions = []
        for key, value in self.filters.items():
            if isinstance(value, str):
                expressions.append(f'{key} == "{value}"')
            elif isinstance(value, (int, float)):
                expressions.append(f'{key} == {value}')
            elif isinstance(value, list):
                values_str = ', '.join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                expressions.append(f'{key} in [{values_str}]')
            elif isinstance(value, dict):
                # Handle operators like $in, $gt, etc.
                if "$in" in value:
                    values_str = ', '.join(f'"{v}"' if isinstance(v, str) else str(v) for v in value["$in"])
                    expressions.append(f'{key} in [{values_str}]')
                elif "$gt" in value:
                    expressions.append(f'{key} > {value["$gt"]}')
                elif "$gte" in value:
                    expressions.append(f'{key} >= {value["$gte"]}')
                elif "$lt" in value:
                    expressions.append(f'{key} < {value["$lt"]}')
                elif "$lte" in value:
                    expressions.append(f'{key} <= {value["$lte"]}')

        if not expressions:
            return ""

        operator_str = " && " if self.operator == "AND" else " || "
        return operator_str.join(expressions)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "filters": self.filters,
            "operator": self.operator
        }

    def __repr__(self) -> str:
        return f"SearchFilter(filters={self.filters}, operator={self.operator})"

