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

"""The canonical postal-address entity.

:class:`CanonicalAddress` is the Pydantic v2 successor to the frozen
``PostalAddress`` dataclass in ``pacs008.standards.address``. It models
the ISO 20022 ``PostalAddress27`` complex type, enforces the schema's
per-field maximum lengths as validation invariants, and exposes the
classification logic that the November 2026 cliff tooling turns on.

Field names are snake_case translations of the ISO 20022 XML element
names (``StrtNm`` -> ``street_name``); each field's ``serialization_alias``
carries the original element name so ``model_dump(by_alias=True)`` speaks
ISO 20022 back out.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, computed_field

from structured_address_fix.domain.enums import AddressClassification

# ISO 20022 PostalAddress27 maximum lengths (per the message
# definition). Scheme profiles may tighten these further; they are the
# base maxima enforced here.
MAX_DEPARTMENT = 70
MAX_SUB_DEPARTMENT = 70
MAX_STREET_NAME = 70
MAX_BUILDING_NUMBER = 16
MAX_BUILDING_NAME = 35
MAX_FLOOR = 70
MAX_POST_BOX = 16
MAX_ROOM = 70
MAX_POST_CODE = 16
MAX_TOWN_NAME = 35
MAX_TOWN_LOCATION_NAME = 35
MAX_DISTRICT_NAME = 35
MAX_COUNTRY_SUB_DIVISION = 35
MAX_ADDRESS_LINE = 70
MAX_ADDRESS_LINE_COUNT = 7

#: CBPR+ UG2026 caps a hybrid address at two residual ``AdrLine`` lines.
MAX_HYBRID_ADDRESS_LINE_COUNT = 2

#: The structured detail fields, excluding ``town_name`` and ``country``
#: which are handled separately in classification.
STRUCTURED_DETAIL_FIELDS: tuple[str, ...] = (
    "department",
    "sub_department",
    "street_name",
    "building_number",
    "building_name",
    "floor",
    "post_box",
    "room",
    "post_code",
    "town_location_name",
    "district_name",
    "country_sub_division",
)


class CanonicalAddress(BaseModel):
    """ISO 20022 ``PostalAddress27``, canonicalized and self-classifying.

    Immutable and closed to extra fields. Construction fails with a
    Pydantic ``ValidationError`` if any element exceeds its ISO 20022
    maximum length, if more than seven ``address_lines`` are supplied, or
    if ``country`` is not a two-letter code.
    """

    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True
    )

    department: str | None = Field(
        None, max_length=MAX_DEPARTMENT, serialization_alias="Dept"
    )
    sub_department: str | None = Field(
        None, max_length=MAX_SUB_DEPARTMENT, serialization_alias="SubDept"
    )
    street_name: str | None = Field(
        None, max_length=MAX_STREET_NAME, serialization_alias="StrtNm"
    )
    building_number: str | None = Field(
        None, max_length=MAX_BUILDING_NUMBER, serialization_alias="BldgNb"
    )
    building_name: str | None = Field(
        None, max_length=MAX_BUILDING_NAME, serialization_alias="BldgNm"
    )
    floor: str | None = Field(
        None, max_length=MAX_FLOOR, serialization_alias="Flr"
    )
    post_box: str | None = Field(
        None, max_length=MAX_POST_BOX, serialization_alias="PstBx"
    )
    room: str | None = Field(
        None, max_length=MAX_ROOM, serialization_alias="Room"
    )
    post_code: str | None = Field(
        None, max_length=MAX_POST_CODE, serialization_alias="PstCd"
    )
    town_name: str | None = Field(
        None, max_length=MAX_TOWN_NAME, serialization_alias="TwnNm"
    )
    town_location_name: str | None = Field(
        None,
        max_length=MAX_TOWN_LOCATION_NAME,
        serialization_alias="TwnLctnNm",
    )
    district_name: str | None = Field(
        None, max_length=MAX_DISTRICT_NAME, serialization_alias="DstrctNm"
    )
    country_sub_division: str | None = Field(
        None,
        max_length=MAX_COUNTRY_SUB_DIVISION,
        serialization_alias="CtrySubDvsn",
    )
    country: str | None = Field(
        None, min_length=2, max_length=2, serialization_alias="Ctry"
    )
    address_lines: tuple[str, ...] = Field(
        default=(),
        max_length=MAX_ADDRESS_LINE_COUNT,
        serialization_alias="AdrLine",
    )

    def has_structured_fields(self) -> bool:
        """Return ``True`` if any structured detail field is populated."""
        return any(
            getattr(self, name) is not None
            for name in STRUCTURED_DETAIL_FIELDS
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def classification(self) -> AddressClassification:
        """Classify this address per CBPR+ UG2026.

        - ``STRUCTURED`` — ``town_name`` + ``country`` present, at least
          one other structured field, and no ``address_lines``.
        - ``HYBRID`` — ``town_name`` + ``country`` present with 1..2
          ``address_lines``.
        - ``UNSTRUCTURED`` — anything else.
        """
        has_town_country = (
            self.town_name is not None and self.country is not None
        )
        n_lines = len(self.address_lines)

        if has_town_country and n_lines == 0 and self.has_structured_fields():
            return AddressClassification.STRUCTURED
        if has_town_country and 1 <= n_lines <= MAX_HYBRID_ADDRESS_LINE_COUNT:
            return AddressClassification.HYBRID
        return AddressClassification.UNSTRUCTURED
