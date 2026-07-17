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

"""Namespace-aware XML pointer utilities shared by the reader and writer.

ISO 20022 documents use a single default namespace, so ``ElementTree``
renders every tag in Clark notation (``{namespace}LocalName``). These
helpers strip that namespace for local-name matching and resolve the
slash-separated JSON pointers that :mod:`xml_reader` emits and
:mod:`xml_writer` consumes.

Pointer grammar: ``/Seg/Seg/...`` where each ``Seg`` is either an element
local name or a decimal index. An index immediately follows the element-name
segment it disambiguates and selects the zero-based occurrence among
same-named siblings; a name with no following index means occurrence ``0``.
The first segment must be the root element's local name.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element


class PointerResolutionError(ValueError):
    """A JSON pointer did not resolve to an element in the tree."""


def local_name(tag: str) -> str:
    """Return the local name of a (possibly namespaced) Clark-notation tag.

    Args:
        tag: An element tag, optionally in ``{namespace}LocalName`` form.

    Returns:
        The tag with any ``{namespace}`` prefix removed.
    """
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def namespace_of(tag: str) -> str:
    """Return the namespace URI of a Clark-notation tag, or ``""``.

    Args:
        tag: An element tag, optionally in ``{namespace}LocalName`` form.

    Returns:
        The namespace URI, or the empty string if the tag is unqualified.
    """
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return ""


def children_named(parent: Element, name: str) -> list[Element]:
    """Return ``parent``'s direct children whose local name is ``name``.

    Args:
        parent: The element whose children to scan.
        name: The local name to match.

    Returns:
        The matching child elements, in document order.
    """
    return [child for child in parent if local_name(child.tag) == name]


def split_pointer_steps(pointer: str) -> list[tuple[str, int]]:
    """Parse a JSON pointer into ``(local_name, index)`` steps.

    Args:
        pointer: A slash-separated pointer, e.g.
            ``"/Document/FIToFICstmrCdtTrf/CdtTrfTxInf/0/Cdtr/PstlAdr"``.

    Returns:
        One ``(name, index)`` tuple per element step, with ``index``
        defaulting to ``0`` when no explicit index segment follows.

    Raises:
        PointerResolutionError: if the pointer is empty or an index segment
            has no preceding element name.
    """
    raw = [seg for seg in pointer.split("/") if seg != ""]
    if not raw:
        raise PointerResolutionError(f"empty pointer: {pointer!r}")

    steps: list[tuple[str, int]] = []
    for seg in raw:
        if seg.isdigit():
            if not steps:
                raise PointerResolutionError(
                    f"index segment with no element name: {pointer!r}"
                )
            name, _ = steps[-1]
            steps[-1] = (name, int(seg))
        else:
            steps.append((seg, 0))
    return steps


def resolve_steps(root: Element, steps: list[tuple[str, int]]) -> Element:
    """Resolve parsed pointer ``steps`` to an element, starting at ``root``.

    Args:
        root: The document root element.
        steps: Parsed ``(name, index)`` steps; the first must name the root.

    Returns:
        The element the steps address.

    Raises:
        PointerResolutionError: if the root name mismatches or any step
            selects a missing child/occurrence.
    """
    if not steps:
        raise PointerResolutionError("cannot resolve empty steps")

    root_name, _ = steps[0]
    if local_name(root.tag) != root_name:
        raise PointerResolutionError(
            f"root is {local_name(root.tag)!r}, pointer expects {root_name!r}"
        )

    current = root
    for name, index in steps[1:]:
        matches = children_named(current, name)
        if index >= len(matches):
            raise PointerResolutionError(
                f"no {name!r} occurrence {index} under "
                f"{local_name(current.tag)!r}"
            )
        current = matches[index]
    return current
