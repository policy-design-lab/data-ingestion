# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] 2025-08-20

### Changed

- Update SNAP data to include the year range 2014-2024 [#69](https://github.com/policy-design-lab/data-ingestion/issues/69)

## [0.5.0] - 2025-06-26

### Added

- Add option to specify a schema name [#44](https://github.com/policy-design-lab/data-ingestion/issues/44)

### Fixed

- Bug in practice names when there are nested parentheses in the raw
  data [#51](https://github.com/policy-design-lab/data-ingestion/issues/51)
- Create database was not passing in db_port when connecting to
  database [#65](https://github.com/policy-design-lab/data-ingestion/issues/65)

### Changed

- Update code to include Title-II data from years 2014 to
  2023 [#54](https://github.com/policy-design-lab/data-ingestion/issues/54)
- Update code to include Crop Insurance data from years 2014 to
  2023 [#63](https://github.com/policy-design-lab/data-ingestion/issues/63)
- Update code to include Title-I data from years 2014 to
  2023 [#68](https://github.com/policy-design-lab/data-ingestion/issues/68)

## [0.4.1] - 2024-11-05

### Fixed

- Added missing DC entry in the data parser [#45](https://github.com/policy-design-lab/data-ingestion/issues/45)

## [0.4.0] - 2024-10-07

### Added

- Feature to parse and ingest Title-II CRP
  data. [#14](https://github.com/policy-design-lab/data-ingestion/issues/14)
- Feature to parse and ingest Title-II ACEP
  data. [#34](https://github.com/policy-design-lab/data-ingestion/issues/34)
- Feature to parse and ingest Title-II RCPP
  data. [#16](https://github.com/policy-design-lab/data-ingestion/issues/16)
- Feature to parse and ingest Title-XI Crop Insurance
  data. [#18](https://github.com/policy-design-lab/data-ingestion/issues/18)

### Changed

- Update Crop Insurance raw data file based on latest updates from the research
  team. [#38](https://github.com/policy-design-lab/data-ingestion/issues/38)

## [0.3.0] - 2024-08-16

### Added

- Feature to parse and ingest Title-II EQIP and CSP
  data. [#7](https://github.com/policy-design-lab/data-ingestion/issues/7)

### Changed

- Create schema now uses a new command-line
  argument. [#27](https://github.com/policy-design-lab/data-ingestion/issues/27)
- EQIP data, CSP data and its practice category grouping based on latest data share and
  feedback. [#28](https://github.com/policy-design-lab/data-ingestion/issues/28)

#### Fixed

- Issue with the CLI not using password provided as command-line
  argument. [#25](https://github.com/policy-design-lab/data-ingestion/issues/25)

## [0.2.0] - 2024-07-22

### Added

- SNAP data ingestion feature. [#1](https://github.com/policy-design-lab/data-ingestion/issues/1)

### Changed

- Issue templates.

## [0.1.0] - 2024-05-30

### Added

- This CHANGELOG file.
- Feature to parse and ingest Title II data. [#7](https://github.com/policy-design-lab/data-ingestion/issues/7)

[0.6.0]: https://github.com/policy-design-lab/data-ingestion/compare/0.5.0...0.6.0

[0.5.0]: https://github.com/policy-design-lab/data-ingestion/compare/0.4.1...0.5.0

[0.4.1]: https://github.com/policy-design-lab/data-ingestion/compare/0.4.0...0.4.1

[0.4.0]: https://github.com/policy-design-lab/data-ingestion/compare/0.3.0...0.4.0

[0.3.0]: https://github.com/policy-design-lab/data-ingestion/compare/0.2.0...0.3.0

[0.2.0]: https://github.com/policy-design-lab/data-ingestion/compare/0.1.0...0.2.0

[0.1.0]: https://github.com/policy-design-lab/data-ingestion/releases/tag/0.1.0
