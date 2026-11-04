"""Verify safe CSRF reason categories and preserve rejection semantics."""
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient, APITestCase

from apps.users.csrf import CsrfRejected
from core.exceptions import api_exception_handler


class CsrfDiagnosticsTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def token(self):
        return self.client.get('/api/v1/auth/csrf/').data['data']['csrf_token']

    def rejected(self, category, **headers):
        with self.assertLogs('apps.users.csrf', level='WARNING') as captured:
            response = self.client.post('/api/v1/auth/login/', {}, format='json', **headers)
        self.assertEqual(response.status_code, 403)
        self.assertIs(response.data['success'], False)
        self.assertEqual(response.data['error_code'], 'CSRF_FAILED')
        self.assertEqual(response.data['csrf_reason'], category)
        self.assertEqual(response.data['message'], 'CSRF verification failed.')
        self.assertEqual(captured.output, [f'WARNING:apps.users.csrf:CSRF rejected: {category}'])
        return response

    def test_missing_cookie(self):
        self.rejected('COOKIE_MISSING')

    def test_missing_token_with_cookie(self):
        self.token()
        self.rejected('TOKEN_MISSING')

    def test_mismatched_token(self):
        token = self.token()
        altered = ('a' if token[0] != 'a' else 'b') + token[1:]
        self.rejected('TOKEN_MISMATCH', HTTP_X_CSRFTOKEN=altered)

    def test_invalid_token_format(self):
        self.token()
        self.rejected('TOKEN_INVALID', HTTP_X_CSRFTOKEN='bad')

    def test_untrusted_origin_is_not_echoed(self):
        response = self.rejected('ORIGIN_REJECTED', HTTP_X_CSRFTOKEN=self.token(),
                                 HTTP_ORIGIN='https://private-origin-marker.invalid')
        self.assertNotIn('private-origin-marker', str(response.data))

    def test_untrusted_referer_is_not_echoed(self):
        response = self.rejected('REFERER_REJECTED', HTTP_X_CSRFTOKEN=self.token(),
                                 secure=True, HTTP_REFERER='https://private-referer-marker.invalid')
        self.assertNotIn('private-referer-marker', str(response.data))

    def test_valid_handshake_reaches_field_validation(self):
        response = self.client.post('/api/v1/auth/login/', {}, format='json',
                                    HTTP_X_CSRFTOKEN=self.token())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error_code'], 'VALIDATION_ERROR')
        self.assertNotIn('csrf_reason', response.data)

    def test_unknown_reason_cannot_leak_raw_details(self):
        with self.assertLogs('apps.users.csrf', level='WARNING') as captured:
            exception = CsrfRejected('private-header-value-marker')
        response = api_exception_handler(exception, {})
        self.assertEqual(response.data['csrf_reason'], 'UNKNOWN')
        self.assertNotIn('private-header-value-marker', str(response.data) + str(captured.output))

    def test_permission_denial_remains_distinct(self):
        response = api_exception_handler(PermissionDenied('Role denied.'), {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error_code'], 'FORBIDDEN')
        self.assertNotIn('csrf_reason', response.data)
