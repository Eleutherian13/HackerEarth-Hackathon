from __future__ import annotations

from typing import Any

from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression
from sqlalchemy.sql.operators import eq


class FakeQuery:
    def __init__(self, items: list[Any]) -> None:
        self._items = list(items)
        self._offset = 0
        self._limit: int | None = None

    def filter(self, *conditions: Any) -> "FakeQuery":
        filtered = [item for item in self._items if all(self._matches_condition(item, cond) for cond in conditions)]
        query = FakeQuery(filtered)
        query._offset = self._offset
        query._limit = self._limit
        return query

    def order_by(self, *orderings: Any) -> "FakeQuery":
        items = list(self._items)
        for ordering in reversed(orderings):
            reverse = self._is_descending(ordering)
            key = self._order_key(ordering)
            items.sort(key=key, reverse=reverse)
        query = FakeQuery(items)
        query._offset = self._offset
        query._limit = self._limit
        return query

    def offset(self, offset: int) -> "FakeQuery":
        query = FakeQuery(self._items)
        query._offset = offset
        query._limit = self._limit
        return query

    def limit(self, limit: int) -> "FakeQuery":
        query = FakeQuery(self._items)
        query._offset = self._offset
        query._limit = limit
        return query

    def all(self) -> list[Any]:
        items = self._items
        if self._offset:
            items = items[self._offset :]
        if self._limit is not None:
            items = items[: self._limit]
        return list(items)

    def count(self) -> int:
        return len(self._items)

    def first(self) -> Any | None:
        items = self.all()
        return items[0] if items else None

    def scalar_one_or_none(self) -> Any | None:
        items = self.all()
        if len(items) == 1:
            return items[0]
        if len(items) == 0:
            return None
        raise ValueError("Expected exactly one result or none")

    def _matches_condition(self, item: Any, condition: Any) -> bool:
        if isinstance(condition, BinaryExpression):
            left = condition.left
            right = condition.right
            right_value = getattr(right, "value", right)
            actual_value = getattr(item, left.key, None)
            if condition.operator == eq:
                return actual_value == right_value
            operator_name = getattr(condition.operator, "__name__", "")
            if operator_name == "in_op":
                return actual_value in right_value
            if operator_name == "is_":
                return actual_value is right_value
            if operator_name == "is_not":
                return actual_value is not right_value
        raise NotImplementedError(f"Unsupported filter condition: {condition}")

    def _is_descending(self, ordering: Any) -> bool:
        if isinstance(ordering, UnaryExpression):
            modifier = getattr(ordering, "modifier", None)
            return getattr(modifier, "__name__", "") == "desc_op"
        return False

    def _order_key(self, ordering: Any) -> Any:
        if isinstance(ordering, UnaryExpression):
            key = ordering.element.key
            return lambda item: getattr(item, key, None)
        if hasattr(ordering, "key"):
            return lambda item: getattr(item, ordering.key, None)
        return lambda item: item


class FakeSession:
    def __init__(self, data: dict[type, list[Any]] | None = None) -> None:
        self._data: dict[type, list[Any]] = {model: list(items) for model, items in (data or {}).items()}

    def query(self, model: type) -> FakeQuery:
        return FakeQuery(self._data.get(model, []))

    def get(self, model: type, pk: Any) -> Any | None:
        return next((item for item in self._data.get(model, []) if getattr(item, "id", None) == pk), None)

    def add(self, obj: Any) -> None:
        existing = next((item for item in self._data.get(type(obj), []) if getattr(item, "id", None) == getattr(obj, "id", None)), None)
        if existing is None:
            self._data.setdefault(type(obj), []).append(obj)

    def commit(self) -> None:
        return None

    def refresh(self, obj: Any) -> None:
        return None

    def close(self) -> None:
        return None
