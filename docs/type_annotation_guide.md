Got it 👍 I’ll draft you a **Type Annotation & Protocols Guide** in Markdown, designed as if it were part of your library’s developer docs.

Here’s a clean and structured version:

---

# 📘 Type Annotation & Protocols Guide

This guide defines the rules and best practices for type annotations in the library. Following these ensures consistent, reliable, and extensible code.

---

## 1. ✅ General Principles

* **Always annotate** function/method signatures (parameters and return types).
* **Prefer explicit over implicit**: even when type inference works, explicit annotations improve readability.
* **Document intent, not implementation**: annotations describe *what* values mean to the consumer, not *how* they’re computed.
* Use `from __future__ import annotations` to avoid forward-reference issues and speed up imports.

---

## 2. 🔑 Protocols & Interfaces

* **Public-facing classes** must have a corresponding `Protocol`.

  * Example: a `Cache` class should have a `CacheProtocol`.
* **Internal/helper classes** may skip a protocol unless multiple interchangeable implementations are expected.
* When in doubt: if you could imagine mocking it in tests, write a protocol.

```python
from typing import Protocol

class CacheProtocol(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
```

---

## 3. 📦 Collections & Generics

* Use **generic types** from `typing`:

  * `list[int]`, `dict[str, Any]`, `set[tuple[str, int]]`
* Avoid untyped `list`, `dict`, `set`, `tuple`.
* Use `Iterable[T]` for inputs and `Sequence[T]` for ordered read-only data.

```python
from collections.abc import Iterable, Sequence

def normalize(values: Iterable[float]) -> list[float]: ...
def get_top(scores: Sequence[int], n: int) -> list[int]: ...
```

---

## 4. ⚖️ Optional & Union

* Use `Optional[T]` (or `T | None`) when a value can be missing.
* Avoid bare `None` returns unless explicitly meaningful.

```python
def find_user(id: int) -> User | None: ...
```

---

## 5. 🛠️ Callable Types

* Always type callbacks with `Callable`.
* If arguments are flexible, use `ParamSpec` and `Concatenate`.

```python
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def with_logging(fn: Callable[P, R]) -> Callable[P, R]: ...
```

---

## 6. 🧩 Any, cast, and object

* **Avoid `Any`** unless absolutely necessary (e.g., third-party integration).
* Use `cast(T, value)` to override inference when safe.
* Use `object` instead of `Any` when a value is opaque but should not allow arbitrary method calls.

---

## 7. 🏗️ Data Models

* Use `@dataclass` for simple immutable data carriers.
* Use `TypedDict` for structured dictionaries.

```python
from dataclasses import dataclass
from typing import TypedDict

@dataclass(frozen=True)
class Point:
    x: float
    y: float

class UserDict(TypedDict):
    id: int
    name: str
```

---

## 8. 🧪 Testing & Type Safety

* Run `mypy` (or `pyright`) in **strict mode** on the library.
* Tests should verify that protocol contracts are respected.
* Encourage consumers to depend on protocols, not concrete classes.

---

## 9. 🧹 Style & Formatting

* Use **PEP 8 + Ruff/Black** for formatting.
* Keep annotations short and readable:

  * Prefer `list[int]` over `List[int]` (Python 3.9+ syntax).
* Break long type hints across lines with parentheses:

```python
def process(
    data: dict[str, list[tuple[str, int]]],
    options: dict[str, str] | None = None,
) -> list[str]: ...
```

---

## 10. 🚦 Summary Rules

* ✅ Annotate everything.
* ✅ Protocols for **public classes** and extensible designs.
* ✅ Use `Iterable`, `Sequence`, `Mapping` instead of concrete types when possible.
* ❌ No raw `Any` or untyped containers.
* ❌ Don’t expose concrete classes where a protocol would suffice.

---

Would you like me to also add a **“decision tree” style checklist** (e.g. *Does this class face the outside world? → Yes → write a protocol*), so your team has a quick reference?
