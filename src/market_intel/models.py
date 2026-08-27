from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)

    observations: Mapped[list["Observation"]] = relationship(back_populates="country")


class Indicator(Base):
    __tablename__ = "indicators"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    polarity: Mapped[str] = mapped_column(String(16), nullable=False)
    base_weight: Mapped[float] = mapped_column(Float, nullable=False)

    observations: Mapped[list["Observation"]] = relationship(back_populates="indicator")


class Observation(Base):
    __tablename__ = "observations"

    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), primary_key=True)
    indicator_code: Mapped[str] = mapped_column(ForeignKey("indicators.code"), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source_updated_at: Mapped[str | None] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    country: Mapped[Country] = relationship(back_populates="observations")
    indicator: Mapped[Indicator] = relationship(back_populates="observations")


class MarketScore(Base):
    __tablename__ = "market_scores"
    __table_args__ = (
        UniqueConstraint("country_code", "reference_year", "scenario", name="uq_market_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), index=True)
    reference_year: Mapped[int] = mapped_column(Integer, index=True)
    scenario: Mapped[str] = mapped_column(String(24), index=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    dimensions_json: Mapped[str] = mapped_column(Text, nullable=False)
    indicator_scores_json: Mapped[str] = mapped_column(Text, nullable=False)
    indicator_years_json: Mapped[str] = mapped_column(Text, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    records_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rankings_calculated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reference_year: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[str | None] = mapped_column(String(32))
    error: Mapped[str | None] = mapped_column(Text)
