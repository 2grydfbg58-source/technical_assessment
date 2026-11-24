# Exploration and Data Contracts

## Reproduction

Run from the repository root:

```bash
jupyter execute scratch/explore_source_data.ipynb
```

The source inputs are `data/rentals.json`, `data/airbnb.csv`,
`data/geo/post_codes.geojson`, and `data/geo/amsterdam_areas.geojson`.

## Measured source findings

| Measure | Measured result |
|---|---:|
| Kamernet rows | 46,722 |
| Airbnb rows | 9,913 |
| Amsterdam Kamernet rows | 8,095 |
| Active Amsterdam Kamernet rows | 7,722 |
| Inactive Amsterdam Kamernet rows | 353 |
| Amsterdam Kamernet rows with unknown active status | 20 |
| Kamernet duplicate `_id` values | 0 |
| Exact duplicate Airbnb rows | 382 |
| Airbnb missing postcodes | 2,254 |
| Airbnb missing bedrooms | 14 |
| Airbnb missing review scores | 1,711 |
| Airbnb postcode forms: PC4 / full / invalid / missing | 3,119 / 4,531 / 9 / 2,254 |
| Kamernet Amsterdam valid postcode rows | 8,095 |
| Distinct Amsterdam Kamernet PC4 values | 73 |
| Airbnb coordinates | latitude 52.29031–52.42538071; longitude 4.763264201–5.019667018 |
| Amsterdam Kamernet coordinates | latitude 52.289948–52.423914; longitude 4.771238–5.018227 |

The 46,722 and 9,913 totals and the 8,095/7,722/353 Amsterdam counts reconcile exactly with the constitution. The constitution also reports 2,254 missing Airbnb postcodes, 14 missing bedrooms, and 1,711 missing review scores; all reconcile exactly. Exact-row duplicate Airbnb records were not stated in the constitution.

## Malformed and optional fields

- Kamernet rent is present and parseable for all 8,095 Amsterdam rows; measured rent values range from EUR 1 to EUR 5,000.
- Airbnb price is numeric and present for all 9,913 rows; measured nightly prices range from EUR 15 to EUR 9,000.
- The Kamernet JSON is valid, is a top-level array, and has no duplicate `_id` values.
- CSV width is uniform at eight fields plus the header.
- Nine supplied Airbnb zipcode values are nonconforming text examples include `....`, `b`, and address-like strings.
- Bedrooms and review scores are optional enrichment fields. No revenue-eligible Airbnb row is rejected because of a missing bedroom or review score.
- Coordinate-based recovery was measured with Shapely `polygon.contains(point)`. For missing or invalid values, 2,262 records had a unique containing PC4 polygon. No record produced multiple containing polygons, and no record was outside all postcode polygons. The supplied `0` postcode is invalid and is not assigned a recovered PC4; it remains unknown.

## Revenue input minimum

### Kamernet

Revenue candidates require `_id`, Amsterdam candidate scope, `isRoomActive = "true"`, and a valid positive monthly rent in EUR.

| Field | Canonical type | Required | Rejection or handling |
|---|---|---|---|
| `_id` | string | Yes | Reject `missing_source_id` |
| `city` | string | Yes | Non-Amsterdam is outside scope |
| `isRoomActive` | enum `true`/`false` | Yes for candidates | Inactive or unknown remains in audit; excluded from current gold |
| `rent` | decimal EUR | Yes | Reject `missing_rent`, `invalid_rent_format`, or `non_positive_rent` |
| `postalCode` | canonical `NNNN LL` or PC4 | No for property revenue | Unknown is retained outside postcode gold |
| coordinates | decimal latitude/longitude | No for direct revenue | May support location recovery |

Annual gross revenue is `monthly rent EUR * 12`. The property grain is scalar `_id`.

### Airbnb

Revenue candidates require a stable listing identifier or documented row hash, Amsterdam location scope, and a valid positive nightly EUR price.

| Field | Canonical type | Required | Rejection or handling |
|---|---|---|---|
| stable listing identifier | string | Yes | Documented row hash if no source identifier exists |
| location/candidate scope | decimal coordinates or Amsterdam scope | Yes | Reject `outside_amsterdam_scope` or `missing_location` |
| `price` | decimal EUR/night | Yes | Reject `missing_price`, `invalid_price_format`, or `non_positive_price` |
| `zipcode` | canonical PC4/full postcode | No, recoverable | Normalize, infer, or retain explicitly unknown |

`bedrooms` and `review_scores_value` are optional enrichment and never disqualify revenue.
Annual gross revenue is `nightly price EUR * 365`.

## Canonical silver contract

| Field | Type | Requiredness | Description |
|---|---|---|---|
| `source_listing_key` | string | required | Kamernet `_id` or deterministic Airbnb key |
| `source_name` | enum `kamernet`,`airbnb` | required | Source identifier |
| `source_record` | original payload or trace key | required | Bronze traceability |
| `city` | string | required for scope | Canonical city |
| `latitude` | decimal nullable | coordinates | WGS84 latitude |
| `longitude` | decimal nullable | coordinates | WGS84 longitude |
| `postcode_full` | string nullable | canonical | `NNNN LL` when known |
| `pc4` | string nullable | canonical | Four digits or null |
| `postcode_source` | enum `original`,`normalized`,`inferred`,`unknown` | required | Origin of location value |
| `postcode_quality` | enum `known`,`unknown`,`ambiguous`,`out_of_bounds`,`invalid` | required | Location quality |
| `location_scope` | enum `amsterdam`,`non_amsterdam`,`unknown` | required | Candidate scope |
| `status` | string nullable | source-specific | Kamernet active status or Airbnb status |
| `currency_code` | enum `EUR` | required for revenue | Currency unit |
| `revenue_input_amount` | decimal nullable | revenue-eligible | Monthly rent or nightly price |
| `annual_gross_revenue_eur` | decimal nullable | derived | Source formula result |
| `bedrooms` | decimal nullable | optional | Airbnb only |
| `review_score` | decimal nullable | optional | Airbnb only |
| `quality_flags` | array<string> | required | Missing, inferred, duplicate, rejected indicators |
| `rejection_reason` | string nullable | quarantine | Stable machine-readable reason |
| `ingestion_timestamp` | timestamp UTC | required | Provenance |

Unknown postcodes use `pc4 = null`, `postcode_source = unknown`, and an explicit quality flag. An arbitrary PC4 is never assigned.

## Gold contracts

### Property grain

One row per `source_listing_key`.

| Field | Type | Required |
|---|---|---|
| `source_listing_key` | string | yes |
| `source_name` | enum | yes |
| `pc4` | string nullable | no |
| `location_scope` | enum | yes |
| `monthly_rent_eur` | decimal nullable | Kamernet |
| `nightly_price_eur` | decimal nullable | Airbnb |
| `annual_gross_revenue_eur` | decimal | yes |
| `bedrooms` | decimal nullable | no |
| `review_score` | decimal nullable | no |
| `postcode_quality` | enum | yes |

Only active Amsterdam Kamernet listings and valid-scope Airbnb listings enter property gold. Inactive and unknown-status Kamernet listings remain audited and are excluded from current rankings.

### Postcode grain

One row per `pc4` and source.

| Field | Type | Required |
|---|---|---|
| `pc4` | string | yes |
| `source_name` | enum | yes |
| `property_count` | integer | yes |
| `total_annual_gross_revenue_eur` | decimal | yes |
| `average_annual_gross_revenue_eur` | decimal | yes |

Unknown postcodes are excluded from postcode gold. A source-comparison table may place Kamernet and Airbnb metrics side-by-side for comparable PC4 values.

## Backfill and rejection examples

| Input | Expected outcome |
|---|---|
| Kamernet `_id=["abc"]`, rent `€ 500,-`, city Amsterdam, active `true`, postcode `1018AS` | `source_listing_key="abc"`, `pc4="1018"`, `postcode_full="1018 AS"`, source normalized, `annual_gross_revenue_eur=6000` |
| Kamernet inactive listing with valid rent | Retained in silver audit; excluded from active current gold revenue |
| Kamernet rent missing or `€ 0,-` | Quarantined with `missing_rent` or `non_positive_rent` |
| Airbnb zipcode `1016 AM`, positive price | `postcode_full="1016 AM"`, `pc4="1016"`, normalized |
| Airbnb zipcode missing, coordinates uniquely inside 1053 polygon | `pc4="1053"`, `postcode_source="inferred"`, `postcode_quality="known"` |
| Airbnb zipcode missing, coordinates outside or ambiguous | `pc4=null`, `postcode_source="unknown"`, quality `out_of_bounds` or `ambiguous`; retain in property silver, exclude from postcode gold |
| Airbnb missing bedrooms/review score, valid price | Revenue eligible; optional fields remain null |
| Airbnb non-positive or invalid price | Quarantined with `non_positive_price` or `invalid_price_format` |

## Open issue

The supplied zipcode `0` is invalid and is not recovered. It remains unknown unless future source rules establish that value as valid.
