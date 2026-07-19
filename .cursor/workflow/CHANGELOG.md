# Changelog — sassbackend (WaterSight API)

All notable changes to the WaterSight backend are documented here.
Entries are grouped under `[Unreleased]`, newest first, and follow the
format defined in `.cursor/rules/sassbackend-workflow.mdc`.

## [Unreleased]

### Fixed — 2026-07-19

**Time:** 2026-07-19 17:58 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Yearly report generation no longer fails with `Decimal * float` (values are cast to float before averaging/graphing) and months are now ordered chronologically. Daily PDF time columns show 12-hour AM/PM times, and monthly/yearly column headers show month + day/year on two lines (e.g. "Jul" / "03").

**Files:**
- `reports/utils/report_generators.py` — float casting in yearly aggregation, chronological month sort, AM/PM time headers, two-line date/month headers

**Impact:** Reports / PDF

### Changed — 2026-07-19

**Time:** 2026-07-19 17:44 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Report availability listing (`daily-groups`, `report-periods`) is now available to any user with water-system access. Non–Super Admin results are scoped to their own analyses; delete-day remains Super Admin only.

**Files:**
- `api/views.py` — shared access/scoping helpers for report discovery endpoints
- `api/tests_daily_groups.py` — access and scoped-data coverage for general users

**Impact:** API

### Added — 2026-07-19

**Time:** 2026-07-19 17:28 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Added a Super Admin report-period availability API that groups analyses into paginated months or years, returning distinct-day and record counts for report discovery.

**Files:**
- `api/views.py` — `report_periods` action with monthly/yearly grouping and pagination
- `api/urls.py` — `/water-analysis/report-periods/` route
- `api/tests_daily_groups.py` — grouping and Super Admin permission coverage

**Impact:** API / route

### Added — 2026-07-19

**Time:** 2026-07-19 16:45 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Super Admin daily report management APIs: grouped date pagination with ordered time entries, whole-day delete, update recalculation (indices/recommendations/trends), and daily PDFs that render every same-day sample as a time column with averages.

**Files:**
- `api/views.py` — `daily_groups`, `delete_day`, Super Admin queryset scope, `perform_update` recalculation
- `api/urls.py` — `/water-analysis/daily-groups/`, `/water-analysis/delete-day/`, PATCH on detail
- `api/serializers.py` — plant/system names; computed fields read-only
- `reports/utils/report_queries.py` — select/order by `analysis_time`
- `reports/utils/report_generators.py` — multi-time daily PDF table + Windows WeasyPrint DLL discovery
- `reports/pdf_generator.py` — also discovers PostgreSQL/PostGIS GTK DLL path on Windows
- `api/tests_daily_groups.py` — API coverage for groups/delete/update

**Impact:** API / route

### Changed — 2026-07-19

**Time:** 2026-07-19 15:56 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Set the project timezone to `Asia/Dhaka` so server-side date/time defaults (`analysis_date`, `analysis_time`) and displayed times match Bangladesh local time instead of UTC.

**Files:**
- `sass_project/settings.py` — `TIME_ZONE = 'Asia/Dhaka'` (`USE_TZ` stays on; DB still stores aware datetimes in UTC)

**Impact:** none

### Added — 2026-07-19

**Time:** 2026-07-19 15:40 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Water analyses now persist an explicit analysis time so multiple samples on the same date retain their user-selected collection times.

**Files:**
- `data_entry/models.py` — added `analysis_time`, configured-timezone default, and date/time ordering
- `data_entry/migrations/0020_wateranalysis_analysis_time.py` — adds and backfills analysis time from existing creation timestamps
- `data_entry/migrations/0021_alter_wateranalysis_analysis_time.py` — aligns the model default with the configured server timezone
- `api/serializers.py` — accepts/returns `analysis_time`
- `data_entry/serializers.py` — exposes `analysis_time`
- `data_entry/admin.py` — displays and edits analysis time

**Impact:** API / migration

### Added — 2026-07-19

**Time:** 2026-07-19 12:23 (UTC+6)
**Author:** Cursor agent
**Issue:** #none

**Summary:** Scaffolded project workflow infrastructure (rule + changelog + README) under `.cursor/` so changelog updates are enforced per the global workflow rule.

**Files:**
- `.cursor/rules/sassbackend-workflow.mdc` — backend workflow rule and conventions
- `.cursor/workflow/CHANGELOG.md` — this changelog
- `.cursor/workflow/README.md` — workflow documentation

**Impact:** none
