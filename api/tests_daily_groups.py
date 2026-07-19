from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from data_entry.models import Plant, WaterAnalysis, WaterSystem

User = get_user_model()


class DailyAnalysisGroupsAPITests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            email='super@example.com',
            username='super',
            password='pass12345',
            role=User.UserRole.SUPER_ADMIN,
        )
        self.general = User.objects.create_user(
            email='user@example.com',
            username='general',
            password='pass12345',
            role=User.UserRole.GENERAL_USER,
        )
        self.plant = Plant.objects.create(name='Test Plant')
        self.water_system = WaterSystem.objects.create(
            plant=self.plant,
            name='Cooling Tower 1',
            system_type='cooling',
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        self.a1 = self._make_analysis(self.super_admin, today, time(9, 15), ph=Decimal('7.20'))
        self.a2 = self._make_analysis(self.super_admin, today, time(14, 30), ph=Decimal('7.40'))
        self.a3 = self._make_analysis(self.general, yesterday, time(10, 0), ph=Decimal('7.10'))

        self.groups_url = reverse('water_analysis_daily_groups')
        self.periods_url = reverse('water_analysis_report_periods')
        self.delete_day_url = reverse('water_analysis_delete_day')

    def _make_analysis(self, user, analysis_date, analysis_time, ph):
        return WaterAnalysis.objects.create(
            user=user,
            plant=self.plant,
            water_system=self.water_system,
            analysis_type='cooling',
            analysis_date=analysis_date,
            analysis_time=analysis_time,
            ph=ph,
            tds=Decimal('500.00'),
            hardness=Decimal('100.00'),
            total_alkalinity=Decimal('80.00'),
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_daily_groups_requires_water_system_access(self):
        self._auth(self.general)
        response = self.client.get(
            self.groups_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_daily_groups_scopes_to_assigned_user_data(self):
        self.water_system.assigned_users.add(self.general)
        self._auth(self.general)
        response = self.client.get(
            self.groups_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'page': 1,
                'page_size': 10,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # General user only sees their own yesterday sample, not Super Admin rows.
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['date'],
            (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
        )
        self.assertEqual(response.data['results'][0]['record_count'], 1)

    def test_daily_groups_paginates_dates_with_ordered_times(self):
        self._auth(self.super_admin)
        response = self.client.get(
            self.groups_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'page': 1,
                'page_size': 10,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        first = response.data['results'][0]
        self.assertEqual(first['record_count'], 2)
        times = [entry['analysis_time'] for entry in first['entries']]
        self.assertEqual(times, ['09:15:00', '14:30:00'])

    def test_report_periods_groups_available_months_and_years(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        older_date = date(today.year - 1, today.month, 10)
        self._make_analysis(
            self.super_admin,
            older_date,
            time(8, 0),
            ph=Decimal('7.00'),
        )
        self._auth(self.super_admin)

        monthly_response = self.client.get(
            self.periods_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'period_type': 'monthly',
            },
        )
        self.assertEqual(monthly_response.status_code, status.HTTP_200_OK)
        self.assertEqual(monthly_response.data['period_type'], 'monthly')
        expected_months = {
            value.strftime('%Y-%m') for value in (today, yesterday, older_date)
        }
        self.assertEqual(monthly_response.data['count'], len(expected_months))
        current_month = monthly_response.data['results'][0]
        self.assertEqual(current_month['period'], today.strftime('%Y-%m'))
        self.assertEqual(
            current_month['record_count'],
            3 if yesterday.month == today.month else 2,
        )
        self.assertEqual(
            current_month['day_count'],
            2 if yesterday.month == today.month else 1,
        )

        yearly_response = self.client.get(
            self.periods_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'period_type': 'yearly',
            },
        )
        self.assertEqual(yearly_response.status_code, status.HTTP_200_OK)
        self.assertEqual(yearly_response.data['count'], 2)
        self.assertEqual(
            yearly_response.data['results'][0]['period'],
            str(today.year),
        )
        self.assertEqual(
            yearly_response.data['results'][0]['record_count'],
            3 if yesterday.year == today.year else 2,
        )

    def test_report_periods_requires_water_system_access(self):
        self._auth(self.general)
        response = self.client.get(
            self.periods_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'period_type': 'monthly',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_report_periods_scopes_to_assigned_user_data(self):
        self.water_system.assigned_users.add(self.general)
        self._auth(self.general)
        response = self.client.get(
            self.periods_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'period_type': 'monthly',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['period'],
            (date.today() - timedelta(days=1)).strftime('%Y-%m'),
        )
        self.assertEqual(response.data['results'][0]['record_count'], 1)

    def test_delete_day_removes_all_records_for_date(self):
        self._auth(self.super_admin)
        today = date.today().strftime('%Y-%m-%d')
        response = self.client.delete(
            self.delete_day_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'date': today,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['deleted_count'], 2)
        self.assertFalse(
            WaterAnalysis.objects.filter(
                water_system=self.water_system,
                analysis_date=date.today(),
            ).exists()
        )
        self.assertTrue(WaterAnalysis.objects.filter(id=self.a3.id).exists())

    def test_delete_day_requires_super_admin(self):
        self._auth(self.general)
        response = self.client.delete(
            self.delete_day_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'date': date.today().strftime('%Y-%m-%d'),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            WaterAnalysis.objects.filter(
                water_system=self.water_system,
                analysis_date=date.today(),
            ).count(),
            2,
        )

    def test_delete_day_returns_404_when_no_analyses(self):
        self._auth(self.super_admin)
        response = self.client.delete(
            self.delete_day_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'date': '2000-01-01',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_day_rejects_invalid_payload(self):
        self._auth(self.super_admin)
        response = self.client.delete(
            self.delete_day_url,
            {
                'analysis_type': 'cooling',
                'water_system': self.water_system.id,
                'date': 'not-a-date',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        missing_fields = self.client.delete(
            self.delete_day_url,
            {'analysis_type': 'cooling'},
            format='json',
        )
        self.assertEqual(missing_fields.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recalculates_and_blocks_immutable_fields(self):
        self._auth(self.super_admin)
        url = reverse('water_analysis_detail', kwargs={'pk': self.a1.id})
        response = self.client.patch(
            url,
            {
                'ph': '7.80',
                'analysis_type': 'boiler',
                'water_system': 9999,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.a1.refresh_from_db()
        self.assertEqual(self.a1.ph, Decimal('7.80'))
        self.assertEqual(self.a1.analysis_type, 'cooling')
        self.assertEqual(self.a1.water_system_id, self.water_system.id)
