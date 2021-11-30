from testing.testcases import TestCase
from datetime import timedelta

from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from utils.time_helpers import utc_now


class TweetTests(TestCase):
    def setUp(self):
        self.jesse = self.create_user('jesse')
        self.tweet = self.create_tweet(self.jesse, content='Happy Thanksgiving!')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.jesse, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.jesse, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        eliza = self.create_user('eliza')
        self.create_like(eliza, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_create_photo(self):
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.jesse,
        )
        self.assertEqual(photo.user, self.jesse)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)