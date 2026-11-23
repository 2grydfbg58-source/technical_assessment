# RevoData's Technical Assessment

## Introduction

The project idea is investing money in Amsterdam's property market for passive income. The objective is purchasing houses and apartments for leasing either through long-term agreements on Kamernet or short-term listings on Airbnb. The dataset containing house locations and nightly prices from Kamernet and Airbnb are already collected.

## Goal of the Assessment

The goal is identifying postcodes with investment potential and determine whether renting properties long-term through Kamernet or via Airbnb would be more profitable.

## Engineering Deliverables

The MVP of this project must be capable of the following:

- Ingest rental data scraped from Kamernet (`./data/rentals.json`)
- Ingest data from Airbnb (`./data/airbnb.csv`)
- Clean both datasets
- Identify and address any missing or improper data by designing and implementing a backfill
strategy
- Calculate potential revenue per property and per postal code for both sources
- Follow the principles of the Medallion Architecture

The following deliverables are expected as part of the project:

- Exploratory notebooks with data validation checks (placed in the `./scratch` folder)
- Notebooks containing the pipeline implementation (located in the `./notebooks` folder)
- Libraries or buildable packages for the pipeline (stored in `./src/<package_name>`)
- Unit tests for the pipeline (included in the `./tests` folder)
- Documentation for the pipeline (documented in the `README` and `./docs` folders), explaining the WHY
- Export of datasets produced by the pipeline, formatted as Parquet files (placed in `./data/output`)
- Pipeline job configurations (included in the `./resources` folder)

Databricks should be used with a free trial.

### Stretch Goals

Following are a number of stretch goals of increasing difficulty, once the MVP is complete and has high-quality.

#### Level 1 / Engineer

- [ ] Build a CI/CD pipeline that deploys your data pipeline
- [ ] Run tests in your CI/CD pipeline
- [ ] Use pre-commit hooks to ensure code quality

#### Level 2 / Artist

- [ ] Build a visualization or dashboard displaying potential revenue per postcode (rental and Airbnb)
- [ ] Create diagrams of the data flows and of your CI/CD pipeline

#### Level 3 / Future-Proof

- [ ] Use Lakeflow Spark Declarative Pipelines (SDP) to build your pipelines
- [ ] Use expectations (if using SDP) or another framework (if not), to ensure data quality
- [ ] Deploy your pipeline using Declarative Automation Bundles

#### Level 4 / over 9000

- [ ] Load the data from `rentals.json` one record at a time with streaming ingestion
- [ ] Update the gold layer table(s) in real time as new streaming data arrives

#### Level 5 / 10x Developer

- [ ] Use the `./data/geo/post_codes.geojson` geographic dataset to enrich the Airbnb data with missing postcodes
- [ ] Use the `./data/geo/amsterdam_areas.geojson` geographic dataset for your visualization