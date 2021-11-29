from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        super(NotificationServiceTests, self).setUp()
        self.yuzuki = self.create_user('yuzuki')
        self.chiaki = self.create_user('chiaki')
        self.yuzuki_tweet = self.create_tweet(self.yuzuki)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet user == comment user
        comment = self.create_comment(self.yuzuki, self.yuzuki_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        comment = self.create_comment(self.chiaki, self.yuzuki_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notification if tweet user == like user
        like = self.create_like(self.yuzuki, self.yuzuki_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != like user
        like = self.create_like(self.chiaki, self.yuzuki_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)
