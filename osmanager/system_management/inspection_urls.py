"""Read-only inspection routes beneath the system API."""

from django.urls import path

from . import inspection_views


urlpatterns = [
    path('overview', inspection_views.overview, name='inspection-overview'),
    path('plans', inspection_views.plans, name='inspection-plans'),
    path('plans/create', inspection_views.create_plan, name='inspection-plan-create'),
    path('plans/<int:plan_id>/update', inspection_views.edit_plan, name='inspection-plan-update'),
    path('plans/<int:plan_id>/toggle', inspection_views.toggle_plan, name='inspection-plan-toggle'),
    path('run', inspection_views.run, name='inspection-run'),
    path('runs', inspection_views.runs, name='inspection-runs'),
    path('runs/<int:run_id>', inspection_views.run_detail, name='inspection-run-detail'),
    path('runs/<int:run_id>/report', inspection_views.report, name='inspection-report'),
]