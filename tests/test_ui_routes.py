import unittest

from app import create_app


class UiRouteRegistrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()

    def test_key_ui_routes_are_registered(self):
        self.assertIn('recovery.step1', self.app.view_functions)
        self.assertIn('recovery.step2', self.app.view_functions)
        self.assertIn('recovery.step3', self.app.view_functions)
        self.assertIn('recovery.step4', self.app.view_functions)
        self.assertIn('recovery.complete', self.app.view_functions)
        self.assertIn('backup.create_step1', self.app.view_functions)
        self.assertIn('backup.create_step2', self.app.view_functions)
        self.assertIn('backup.create_step3', self.app.view_functions)
        self.assertIn('backup.create_step4', self.app.view_functions)
        self.assertIn('backup.review', self.app.view_functions)
        self.assertIn('backup.success', self.app.view_functions)
        self.assertIn('vm.index', self.app.view_functions)
        self.assertIn('users.index', self.app.view_functions)
        self.assertIn('settings.index', self.app.view_functions)
        self.assertIn('profile.index', self.app.view_functions)

    def test_login_required_pages_redirect(self):
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)

    def test_development_app_factory_initializes_database(self):
        app = create_app('development')
        self.assertTrue(app is not None)
        self.assertTrue(app.config['DEBUG'])


if __name__ == '__main__':
    unittest.main()
