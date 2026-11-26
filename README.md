# technical_assessment
Repository for the RevoData Technical Assessment

## Bronze and silver pipeline

Install the package and dependencies in a local Python environment:

```bash
python -m pip install -e .
pytest
```

Run the bronze/silver transformation through the portable package:

```python
from amsterdam_investment.pipeline import run_bronze_silver

products = run_bronze_silver(".")
```

The pipeline preserves source payloads and ingestion metadata in bronze, emits typed
silver records, and publishes quality and rejection counts through
`amsterdam_investment.quality.quality_report`. Use
`amsterdam_investment.pipeline.run_full_pipeline` to build annual gross revenue,
reconcile postcode totals, and export the property, postcode, and source-comparison
Parquet products under `data/output`. See [docs/revenue-gold.md](docs/revenue-gold.md)
for eligibility rules, schemas, keys, and reconciliation details.
