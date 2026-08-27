from market_intel.domain import CountryDefinition, IndicatorDefinition, Polarity, Scenario

COUNTRIES: tuple[CountryDefinition, ...] = (
    CountryDefinition(code="ARG", name="Argentina"),
    CountryDefinition(code="BRA", name="Brazil"),
    CountryDefinition(code="CHL", name="Chile"),
    CountryDefinition(code="COL", name="Colombia"),
    CountryDefinition(code="MEX", name="Mexico"),
    CountryDefinition(code="PER", name="Peru"),
)

INDICATORS: tuple[IndicatorDefinition, ...] = (
    IndicatorDefinition(
        code="NY.GDP.MKTP.KD.ZG",
        name="GDP growth",
        unit="annual %",
        category="growth",
        polarity=Polarity.POSITIVE,
        base_weight=0.18,
    ),
    IndicatorDefinition(
        code="NY.GDP.PCAP.CD",
        name="GDP per capita",
        unit="current US$",
        category="scale",
        polarity=Polarity.POSITIVE,
        base_weight=0.10,
    ),
    IndicatorDefinition(
        code="NY.GDP.MKTP.CD",
        name="GDP",
        unit="current US$",
        category="scale",
        polarity=Polarity.POSITIVE,
        base_weight=0.10,
    ),
    IndicatorDefinition(
        code="FP.CPI.TOTL.ZG",
        name="Inflation",
        unit="annual %",
        category="stability",
        polarity=Polarity.NEGATIVE,
        base_weight=0.14,
    ),
    IndicatorDefinition(
        code="SL.UEM.TOTL.ZS",
        name="Unemployment",
        unit="% of labor force",
        category="stability",
        polarity=Polarity.NEGATIVE,
        base_weight=0.10,
    ),
    IndicatorDefinition(
        code="IT.NET.USER.ZS",
        name="Internet adoption",
        unit="% of population",
        category="digital",
        polarity=Polarity.POSITIVE,
        base_weight=0.14,
    ),
    IndicatorDefinition(
        code="SP.URB.TOTL.IN.ZS",
        name="Urban population",
        unit="% of population",
        category="access",
        polarity=Polarity.POSITIVE,
        base_weight=0.10,
    ),
    IndicatorDefinition(
        code="NE.TRD.GNFS.ZS",
        name="Trade openness",
        unit="% of GDP",
        category="connectivity",
        polarity=Polarity.POSITIVE,
        base_weight=0.14,
    ),
)

SCENARIO_WEIGHTS: dict[Scenario, dict[str, float]] = {
    Scenario.BASE: {item.code: item.base_weight for item in INDICATORS},
    Scenario.GROWTH: {
        "NY.GDP.MKTP.KD.ZG": 0.26,
        "NY.GDP.PCAP.CD": 0.08,
        "NY.GDP.MKTP.CD": 0.10,
        "FP.CPI.TOTL.ZG": 0.08,
        "SL.UEM.TOTL.ZS": 0.06,
        "IT.NET.USER.ZS": 0.18,
        "SP.URB.TOTL.IN.ZS": 0.08,
        "NE.TRD.GNFS.ZS": 0.16,
    },
    Scenario.RESILIENCE: {
        "NY.GDP.MKTP.KD.ZG": 0.12,
        "NY.GDP.PCAP.CD": 0.14,
        "NY.GDP.MKTP.CD": 0.10,
        "FP.CPI.TOTL.ZG": 0.22,
        "SL.UEM.TOTL.ZS": 0.16,
        "IT.NET.USER.ZS": 0.10,
        "SP.URB.TOTL.IN.ZS": 0.08,
        "NE.TRD.GNFS.ZS": 0.08,
    },
}

if not all(abs(sum(weights.values()) - 1.0) < 1e-9 for weights in SCENARIO_WEIGHTS.values()):
    raise RuntimeError("Every scenario must define weights that sum to 1.0")
