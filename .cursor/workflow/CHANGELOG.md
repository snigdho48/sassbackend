# Changelog — sassbackend (WaterSight API)

All notable changes to the WaterSight backend are documented here.
Entries are grouped under `[Unreleased]`, newest first, and follow the
format defined in `.cursor/rules/sassbackend-workflow.mdc`.

## [Unreleased]

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
