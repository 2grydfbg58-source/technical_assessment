# Revenue and Gold Products

The portable `amsterdam_investment` pipeline builds annual gross revenue from
the silver records and writes three Parquet products to `data/output`.
`pipeline.run_bronze_silver` remains the bronze/silver-only entry point;
`pipeline.run_full_pipeline` runs all three layers and accepts an optional
output directory.

## Revenue eligibility

- Kamernet candidates must have a stable listing key, Amsterdam location scope,
  `status="true"`, EUR monthly rent, and a finite positive amount. Annual gross
  revenue is monthly rent × 12.
- Airbnb candidates must have a stable content hash, Amsterdam geographic
  scope, EUR nightly price, and a finite positive amount. Annual gross revenue
  is nightly price × 365. Bedrooms and review scores are not eligibility
  requirements.
- These values annualize snapshot prices; they do not model occupancy, costs,
  taxes, financing, or forecasts.
- Eligible properties remain in the property product when PC4 is unknown.
  Such rows are counted in reconciliation and omitted only from postcode
  products.
- Property keys are `(source_name, source_listing_key)`. Repeated identical
  keys are collapsed to one property row. The representative retains the
  total source-row duplicate count; inconsistent eligible records for the same
  key fail explicitly rather than selecting a revenue value arbitrarily.
  Airbnb's content hash is a provisional key and does not establish
  real-world listing identity.

## Output schemas and grains

All monetary fields are EUR `decimal128` values. Their scale is selected to
preserve the exact source decimal precision, with a minimum scale of two.

| File | Grain / key | Fields |
| --- | --- | --- |
| `property_revenue.parquet` | One row per `(source_name, source_listing_key)` | `source_name`, `source_listing_key`, nullable `pc4`, `annual_gross_revenue_eur`, `revenue_input_amount_eur`, `revenue_input_unit`, `currency_code`, `location_scope`, nullable `status`, `postcode_source`, `postcode_quality`, `quality_flags`, `duplicate_count` |
| `postcode_revenue.parquet` | One row per `(source_name, pc4)` with known PC4 | `source_name`, `pc4`, `property_count`, `annual_gross_revenue_eur` |
| `source_comparison.parquet` | One row per known PC4 present in either source | `pc4`, both source property counts and revenue totals, `airbnb_minus_kamernet_revenue_eur`, `higher_revenue_source` (`airbnb`, `kamernet`, or `tie`), nullable `kamernet_pc4_rank`, and nullable `airbnb_pc4_rank` |

An absent source at a postcode has a count and total of zero in the comparison.
The revenue difference is Airbnb minus Kamernet. Source totals are compared
within each PC4; no proximity matching or investment recommendation is implied.
Each source rank is calculated independently over only the PC4 rows where that
source has one or more eligible properties. Ranks are descending by that
source's annual gross revenue. Equal totals receive the same standard
competition rank, so values of `1, 1, 3` preserve the position gap after a tie.
When a source has no eligible properties at a PC4, its rank is null even though
the comparison row remains present for the other source.

## Reconciliation

The full pipeline returns per-source reconciliation measures alongside the
products: eligible deduplicated property count and revenue total, source rows
collapsed, known-PC4 count and revenue total, and unknown-PC4 count and revenue
total. Property totals equal known-PC4 plus unknown-PC4 totals. Postcode totals
equal the known-PC4 property subset; unknown-PC4 properties are deliberately
excluded from postcode aggregation.

Run the supplied-data pipeline with:

```bash
python3 - <<'PY'
from amsterdam_investment.pipeline import run_full_pipeline

result = run_full_pipeline(".")
print(result["reconciliation"])
print(result["output_paths"])
PY
```
