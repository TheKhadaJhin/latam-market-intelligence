# Data Sources and Licensing

## World Bank World Development Indicators

- API: `https://api.worldbank.org/v2`
- Documentation: `https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information`
- Dataset terms: `https://data.worldbank.org/summary-terms-of-use`
- Default open-data license: CC BY 4.0 with the World Bank's additional dataset terms,
  unless specific indicator metadata states otherwise.

Attribution used by this project:

> The World Bank, World Development Indicators. Data retrieved through the World Bank
> Indicators API. The source may revise historical observations.

The project does not imply World Bank sponsorship, approval, or endorsement.

## Snapshot policy

`data/sample/world_bank_snapshot.json` is a reproducibility fixture containing source
responses for only the configured countries, indicators, and years. Its metadata records
generation time, source URL, period, and license summary. Regenerate it with:

```bash
uv run python scripts/download_snapshot.py
```

Review upstream indicator metadata and terms before using or redistributing the data for a
different purpose.
