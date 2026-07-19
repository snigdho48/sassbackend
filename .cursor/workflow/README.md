# sassbackend workflow

Development workflow and conventions for the **WaterSight** Django backend.

## Overview

`sassbackend` is a Django 5.2 + DRF API for water-analysis data logging,
dashboards, and PDF reporting. Authentication is JWT (SimpleJWT); API docs are
served via Swagger/Redoc (drf-yasg).

### Apps

| App          | Responsibility                                              |
| ------------ | ----------------------------------------------------------- |
| `users`      | Custom user model, roles, admin assignment, profiles        |
| `api`        | URL routing, serializers, middleware, shared endpoints      |
| `data_entry` | Plants, water systems, water analysis, trends, recommendations |
| `dashboard`  | Dashboard aggregation queries                               |
| `reports`    | Report generation, PDF output, graph utilities              |

## Local setup

```bash
cd sassbackend
python -m venv venv
venv\Scripts\activate            # Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

- API root: `http://localhost:8000/api/`
- Swagger: `http://localhost:8000/swagger/`
- Redoc: `http://localhost:8000/redoc/`
- Admin: `http://localhost:8000/admin/`

## Day-to-day workflow

1. Create a focused branch; use conventional commits (`feat`, `fix`, `chore`,
   `docs`, `refactor`, `test`) and reference GitLab issues with `#<id>`.
2. Make the change. If models change, generate and commit a migration:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Update Swagger-visible endpoints and keep serializers in sync.
4. **Append a CHANGELOG entry** under `[Unreleased]` in
   `.cursor/workflow/CHANGELOG.md` (see the entry format in the workflow rule).
5. Open a small, focused merge request.

## Impact tags for changelog entries

- `API` — request/response contract changed
- `migration` — a DB migration was added
- `route` — a URL route was added/changed
- `calculation` — water chemistry logic changed (LSI/RSI, cycles, dosing, etc.)
- `none` — docs/tooling only

## Daily report management (Super Admin)

- `GET /api/water-analysis/daily-groups/?analysis_type=&water_system=&page=&page_size=`
  — paginates distinct analysis dates with ordered time entries (any user with
  water-system access; non–Super Admin results are scoped to their own data)
- `GET /api/water-analysis/report-periods/?analysis_type=&water_system=&period_type=&page=&page_size=`
  — paginates months or years that contain reportable data, with distinct-day
  and record counts (`period_type=monthly|yearly`; same access/scoping rules)
- `DELETE /api/water-analysis/delete-day/` — deletes all analyses for one date/type/system
- `PATCH /api/water-analysis/<id>/` — edit measurements/date-time; recalculates indices
- Daily PDF generation includes every same-day sample as a time column (+ average)

See `.cursor/rules/sassbackend-workflow.mdc` for the full rule.
