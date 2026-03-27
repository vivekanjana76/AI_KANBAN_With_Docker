from copy import deepcopy

from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


class CardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    details: str


class ColumnPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str
    cardIds: list[str] = Field(default_factory=list)


class BoardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_board_integrity(self) -> "BoardPayload":
        column_ids = [column.id for column in self.columns]
        if len(column_ids) != len(set(column_ids)):
            raise ValueError("columns must have unique ids")

        card_keys = set(self.cards.keys())
        for card_key, card in self.cards.items():
            if card.id != card_key:
                raise ValueError(f"card id mismatch for '{card_key}'")

        ordered_card_ids: list[str] = []
        for column in self.columns:
            ordered_card_ids.extend(column.cardIds)

        seen_card_ids: set[str] = set()
        duplicate_card_ids: set[str] = set()
        for card_id in ordered_card_ids:
            if card_id in seen_card_ids:
                duplicate_card_ids.add(card_id)
            seen_card_ids.add(card_id)

        if duplicate_card_ids:
            duplicate_ids = ", ".join(sorted(duplicate_card_ids))
            raise ValueError(f"card ids must not repeat across columns: {duplicate_ids}")

        missing_card_ids = seen_card_ids - card_keys
        if missing_card_ids:
            missing_ids = ", ".join(sorted(missing_card_ids))
            raise ValueError(f"column references missing cards: {missing_ids}")

        orphan_card_ids = card_keys - seen_card_ids
        if orphan_card_ids:
            orphan_ids = ", ".join(sorted(orphan_card_ids))
            raise ValueError(f"cards must appear in a column: {orphan_ids}")

        return self


class BoardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    board: BoardPayload


def default_board() -> dict:
    return deepcopy(DEFAULT_BOARD)
