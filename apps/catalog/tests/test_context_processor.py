from django.contrib.auth.models import Group, User, AnonymousUser
from django.test import TestCase, RequestFactory
from apps.catalog.context_processors import global_user_context, global_host_context
from apps.hosts.models import DockerHost


class ContextProcessorTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(username="normalo")
        self.admin = User.objects.create_superuser(username="boss", password="pw")

    def test_global_user_context_anonymous(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        result = global_user_context(request)

        self.assertFalse(result["is_admin"])
        self.assertFalse(result["is_editor"])
        self.assertFalse(result["is_user"])
        self.assertEqual(result["user_instances_count"], 0)

    def test_global_user_context_admin(self):
        request = self.factory.get("/")
        request.user = self.admin
        result = global_user_context(request)

        self.assertTrue(result["is_admin"])
        self.assertTrue(result["is_editor"])
        self.assertTrue(result["is_user"])
        self.assertEqual(result["user_instances_count"], 0)

    def test_global_user_context_editor(self):
        request = self.factory.get("/")
        user_group = Group.objects.get(name="user")
        editor_group = Group.objects.get(name="editor")
        self.user.groups.add(user_group, editor_group)
        request.user = self.user
        result = global_user_context(request)

        self.assertFalse(result["is_admin"])
        self.assertTrue(result["is_editor"])
        self.assertTrue(result["is_user"])
        self.assertEqual(result["user_instances_count"], 0)

    def test_global_host_context(self):
        result = global_host_context()
        self.assertIsNone(result["active_host"])

        host = DockerHost.objects.create(name="Server1", active=True)
        result = global_host_context()
        self.assertEqual(result["active_host"], host)
