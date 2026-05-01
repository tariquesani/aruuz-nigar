# Changelog

All notable changes to this project are documented in this file.

## 1.1.0 - 2026-05-01

### Highlights
- Improved qafiya results with clearer grouping, better on-page navigation, and richer summary information.
- Expanded qafiya word support with better meanings and matching context for more useful lookup results.
- Improved rhyme-check reliability for short-suffix and open-matching edge cases.

### Notable Changes
- Updated user-facing terminology from "kafiya" to "qafiya" for consistency across pages and routes.
- Added pagination for qafiya results and improved handling for dynamic result updates.
- Improved qafiya match sorting and display details, including stronger classification and count summaries.
- Refined UI presentation (layout, direction, and color guidance) for easier reading of rhyme groups.
- Fixed tooltip/lookup edge cases to improve meaning display consistency.
- Expanded supporting documentation and inline help text around qafiya behavior.

## 1.0.2 - 2026-04-12

### Highlights
- Added a full kafiya dictionary workflow for Urdu rhyme lookup, including phonetic normalization and ranked rhyme quality groups.
- Introduced strict radeef + kafiya analysis for ghazals via `/api/radeefkafiya`.
- Improved `islah` feedback with better rhyme visualization and verse-level diagnostics.

### Notable Changes
- Added a new rhyme utilities module and stricter Urdu-script rhyme checks.
- Added scripts to build and check radeef and kafiya assets.
- Updated docs and references for the kafiya dictionary index.
- Removed deprecated `islah_refactored.html`.

## 1.0.1 - 2026-02-28

### Highlights
- Improved meter summary output and template display for clearer scansion interpretation.
- Added a development heartbeat/status indicator for local environment visibility.
- Improved API compatibility by enhancing module discovery with `pkgutil`.

### Notable Changes
- Added `gunicorn` to requirements for Unix/Linux deployments.
- Refreshed documentation with demo links and updated interface screenshot.

## 1.0 - 2026-02-03

### Highlights
- Major islah UI overhaul with multi-line results, better grid layout, and stronger responsiveness.
- Added dominant meter API + UI support, including richer foot and meter details.
- Introduced alignment and diff utilities to compare text against closest bahr patterns.

### Notable Changes
- Added `/api/scan` route with discovery-based API routing.
- Added debounce and performance/memoization improvements in UI.
- Added local static asset loading for Bootstrap/Alpine and Urdu font stylesheet.
- Applied naming and structure refactors for clearer API and UI internals.

## 1.0.1-beta - 2026-01-28

### Highlights
- Added word-level tooltip explanations for scansion output.
- Refined meter selection logic and fallback explanations for non-muarrab words.
- Expanded UI polish with theme updates, server status indicator, and logo/about/download improvements.

### Notable Changes
- Introduced `get_scansion` simplification and explanation-builder improvements.
- Improved handling around nasal coda and final vowel weakening edge cases.
- Improved documentation wording and clarity.

## 1.0.0-beta - 2026-01-23

### Highlights
- First public beta foundation with core Urdu scansion analysis workflows.
- Initial architecture for detailed explanation and trace generation during scansion.
- Early documentation and packaging groundwork.

### Notable Changes
- Established explanation-builder and tracing model used by later releases.
- Simplified routes and cleanup before beta tagging.
- Added initial docs site setup and baseline distribution/docs preparation.
