from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generator, Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass
class DoublyCircularNode(Generic[T]):
    """Node used by a doubly circular linked list."""

    value: T
    next: Optional["DoublyCircularNode[T]"] = None
    previous: Optional["DoublyCircularNode[T]"] = None


class DoublyCircularLinkedList(Generic[T]):
    """Manual doubly circular linked list with forward and backward traversal."""

    def __init__(self) -> None:
        self._head: Optional[DoublyCircularNode[T]] = None
        self._size = 0

    @property
    def head(self) -> Optional[DoublyCircularNode[T]]:
        return self._head

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def append(self, value: T) -> DoublyCircularNode[T]:
        node = DoublyCircularNode(value=value)

        if self._head is None:
            node.next = node
            node.previous = node
            self._head = node
        else:
            tail = self._head.previous
            if tail is None:
                raise RuntimeError("Circular links are corrupted.")
            node.previous = tail
            node.next = self._head
            tail.next = node
            self._head.previous = node

        self._size += 1
        return node

    def find_node(self, predicate: Callable[[T], bool]) -> Optional[DoublyCircularNode[T]]:
        if self._head is None:
            return None

        current = self._head
        for _ in range(self._size):
            if predicate(current.value):
                return current
            if current.next is None:
                raise RuntimeError("Circular links are corrupted.")
            current = current.next

        return None

    def iter_forward(
        self,
        start_node: Optional[DoublyCircularNode[T]] = None,
        steps: Optional[int] = None,
    ) -> Generator[T, None, None]:
        """Yield values by following next links around the circle."""

        yield from self._iterate(start_node=start_node, steps=steps, forward=True)

    def iter_backward(
        self,
        start_node: Optional[DoublyCircularNode[T]] = None,
        steps: Optional[int] = None,
    ) -> Generator[T, None, None]:
        """Yield values by following previous links around the circle."""

        yield from self._iterate(start_node=start_node, steps=steps, forward=False)

    def next_value(self, node: DoublyCircularNode[T]) -> T:
        if node.next is None:
            raise RuntimeError("Circular links are corrupted.")
        return node.next.value

    def previous_value(self, node: DoublyCircularNode[T]) -> T:
        if node.previous is None:
            raise RuntimeError("Circular links are corrupted.")
        return node.previous.value

    def _iterate(
        self,
        start_node: Optional[DoublyCircularNode[T]],
        steps: Optional[int],
        forward: bool,
    ) -> Generator[T, None, None]:
        if self._head is None:
            return

        current = start_node or self._head
        total_steps = self._size if steps is None else steps

        for _ in range(total_steps):
            yield current.value
            next_node = current.next if forward else current.previous
            if next_node is None:
                raise RuntimeError("Circular links are corrupted.")
            current = next_node
