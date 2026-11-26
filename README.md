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

## Pipeline configuration and Databricks

`amsterdam_investment.pipeline.PipelineConfig` defines source and geography
paths, the output directory, and output table names. Use
`PipelineConfig.for_root(root, **overrides)` to override defaults without
editing transformation code:

```python
from amsterdam_investment.pipeline import PipelineConfig, run_full_pipeline

config = PipelineConfig.for_root(
    "/mnt/project",
    kamernet_source="/mnt/data/rentals.json",
    airbnb_source="/mnt/data/airbnb.csv",
    output_dir="/dbfs/mnt/output",
)
run_full_pipeline("/mnt/project", config=config)
```

The Databricks bundle job uses `notebooks/run_pipeline.py` and resources under
`resources/`. Deploy and run it with:

```bash
databricks bundle validate
databricks bundle deploy --target dev
databricks bundle run amsterdam_investment_pipeline --target dev
```

Job parameters expose the source, geography, output, and table-name settings.
Failures raised by the package include the pipeline stage and source paths;
gold-stage failures also include Kamernet and Airbnb quality counts.
