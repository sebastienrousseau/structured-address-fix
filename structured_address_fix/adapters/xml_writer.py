# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Apply remediation patches back onto an ISO 20022 message.

:func:`apply_operations` parses the document with ``defusedxml`` (XXE-safe),
applies each :class:`~structured_address_fix.domain.remediation.PatchOperation`
to the element addressed by its JSON pointer, and re-serialises the tree with
namespaces and element order preserved. Structured elements created by a
``SET`` are inserted ahead of any residual ``AdrLine`` children so the output
keeps ISO 20022 sequence order. An empty operation list round-trips the
document unchanged apart from insignificant whitespace.
"""

from __future__ import annotations

from collections.abc import Sequence
from xml.etree.ElementTree import (
    Element,
    ParseError,
    register_namespace,
    tostring,
)

from defusedxml.ElementTree import fromstring

from structured_address_fix.adapters._xmlutil import (
    PointerResolutionError,
    children_named,
    local_name,
    namespace_of,
    resolve_steps,
    split_pointer_steps,
)
from structured_address_fix.domain.remediation import PatchOp, PatchOperation
from structured_address_fix.errors import (
    MalformedXMLError,
    PatchApplicationError,
)


def apply_operations(
    xml: str,
    operations: Sequence[PatchOperation],
) -> str:
    """Apply ``operations`` to ``xml`` and return the serialised result.

    Args:
        xml: The raw ISO 20022 XML document.
        operations: The patch operations to apply, in order.

    Returns:
        The re-serialised document with all operations applied. With no
        operations the document round-trips unchanged apart from
        insignificant whitespace.

    Raises:
        MalformedXMLError: if ``xml`` is not well-formed XML.
        PatchApplicationError: if an operation's target parent (or a
            ``MOVE`` source) cannot be located.
    """
    try:
        root: Element = fromstring(xml)
    except ParseError as exc:
        raise MalformedXMLError(
            f"could not parse XML: {exc}", context={"detail": str(exc)}
        ) from exc

    namespace = namespace_of(root.tag)
    if namespace:
        register_namespace("", namespace)

    for operation in operations:
        _apply_one(root, operation)

    body = tostring(root, encoding="unicode")
    return _prolog(xml) + body


def _prolog(xml: str) -> str:
    """Return the XML declaration of ``xml`` (with newline), or ``""``.

    Args:
        xml: The original document text.

    Returns:
        The leading ``<?xml ... ?>`` declaration plus a newline if present,
        else the empty string.
    """
    stripped = xml.lstrip()
    if stripped.startswith("<?xml"):
        end = stripped.find("?>")
        if end != -1:
            return stripped[: end + 2] + "\n"
    return ""


def _apply_one(root: Element, operation: PatchOperation) -> None:
    """Dispatch a single patch operation to its handler.

    Args:
        root: The document root element.
        operation: The operation to apply.

    Raises:
        PatchApplicationError: if the operation cannot be applied.
    """
    if operation.op is PatchOp.SET:
        _set(root, operation.path, operation.value)
    elif operation.op is PatchOp.REMOVE:
        _remove(root, operation.path)
    else:
        _move(root, operation)


def _parent_and_leaf(root: Element, path: str) -> tuple[Element, str, int]:
    """Resolve a pointer to its parent element and final ``(name, index)``.

    Args:
        root: The document root element.
        path: The JSON pointer to the target element.

    Returns:
        A ``(parent, name, index)`` tuple for the final step.

    Raises:
        PatchApplicationError: if the parent cannot be resolved.
    """
    try:
        steps = split_pointer_steps(path)
        name, index = steps[-1]
        parent = resolve_steps(root, steps[:-1])
    except PointerResolutionError as exc:
        raise PatchApplicationError(
            f"cannot resolve parent of {path}: {exc}",
            context={"path": path},
        ) from exc
    return parent, name, index


def _set(root: Element, path: str, value: str | None) -> None:
    """Create or replace the element at ``path`` with text ``value``.

    Args:
        root: The document root element.
        path: The JSON pointer to the target element.
        value: The text to set (``None`` yields an empty element).

    Raises:
        PatchApplicationError: if the target parent cannot be located.
    """
    parent, name, index = _parent_and_leaf(root, path)
    existing = children_named(parent, name)
    if index < len(existing):
        existing[index].text = value
        return

    namespace = namespace_of(parent.tag)
    tag = f"{{{namespace}}}{name}" if namespace else name
    child = Element(tag)
    child.text = value
    _insert_in_order(parent, child, name)


def _insert_in_order(parent: Element, child: Element, name: str) -> None:
    """Insert ``child`` into ``parent`` respecting ISO 20022 order.

    Structured elements are inserted before the first ``AdrLine`` child so
    residual address lines stay last; ``AdrLine`` and any element with no
    ``AdrLine`` present are appended.

    Args:
        parent: The element to insert into.
        child: The new child element.
        name: The local name of ``child``.
    """
    if name != "AdrLine":
        for pos, existing in enumerate(parent):
            if local_name(existing.tag) == "AdrLine":
                parent.insert(pos, child)
                return
    parent.append(child)


def _remove(root: Element, path: str) -> None:
    """Remove the element at ``path`` if present (idempotent).

    Args:
        root: The document root element.
        path: The JSON pointer to the target element.

    Raises:
        PatchApplicationError: if the target parent cannot be located.
    """
    parent, name, index = _parent_and_leaf(root, path)
    existing = children_named(parent, name)
    if index < len(existing):
        parent.remove(existing[index])


def _move(root: Element, operation: PatchOperation) -> None:
    """Move the element at ``operation.from_`` to ``operation.path``.

    The source element's text is transplanted; the source element is then
    removed and re-created (or its target replaced) at the destination.

    Args:
        root: The document root element.
        operation: The ``MOVE`` operation.

    Raises:
        PatchApplicationError: if ``from`` is missing, or the source or a
            target parent cannot be located.
    """
    if operation.from_ is None:
        raise PatchApplicationError(
            f"MOVE requires a 'from' pointer: {operation.path}",
            context={"path": operation.path},
        )

    src_parent, src_name, src_index = _parent_and_leaf(root, operation.from_)
    src_children = children_named(src_parent, src_name)
    if src_index >= len(src_children):
        raise PatchApplicationError(
            f"MOVE source not found: {operation.from_}",
            context={"from": operation.from_},
        )

    source = src_children[src_index]
    text = source.text
    src_parent.remove(source)
    _set(root, operation.path, text)
