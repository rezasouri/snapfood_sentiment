"""Versioned extraction contract; validation proves provenance, not semantic truth."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Aspect = Literal[
    "taste_quality", "temperature", "packaging", "price_value",
    "delivery_delay", "courier_behavior", "portion_size", "missing_wrong_items",
]
Sentiment = Literal["positive", "negative", "neutral", "mixed", "uncertain"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceSpan(ContractModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_offsets(self) -> EvidenceSpan:
        if self.end <= self.start:
            raise ValueError("evidence end must be greater than start")
        return self


class ExtractionRecord(ContractModel):
    review_id: str = Field(min_length=1)
    aspect: Aspect
    sentiment: Sentiment
    evidence_span: EvidenceSpan
    label_source: Literal["model_generated", "rule_based", "public_gold"]
    model_version: str = Field(min_length=1)
    validation_status: Literal["proposed", "validated", "rejected"] = "proposed"


class ReviewExtraction(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    review_id: str = Field(min_length=1)
    records: list[ExtractionRecord]


def validate_extraction(payload: str, *, review_id: str, original_text: str) -> ReviewExtraction:
    """Accept JSON only; match IDs and exact Unicode code-point offsets to original text."""
    result = ReviewExtraction.model_validate_json(payload)
    if result.review_id != review_id:
        raise ValueError("unexpected review_id")
    validated = []
    for record in result.records:
        if record.review_id != review_id:
            raise ValueError("record review_id differs from requested review")
        span = record.evidence_span
        if span.end > len(original_text) or original_text[span.start:span.end] != span.text:
            raise ValueError("evidence does not match original text and offsets")
        validated.append(record.model_copy(update={"validation_status": "validated"}))
    # Empty records are valid for reviews without an explicit supported aspect.
    return result.model_copy(update={"records": validated})
