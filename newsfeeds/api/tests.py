from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.jesse = self.create_user('jesse')
        self.jesse_client = APIClient()
        self.jesse_client.force_authenticate(self.jesse)

        self.eliza = self.create_user('eliza')
        self.eliza_client = APIClient()
        self.eliza_client.force_authenticate(self.eliza)

        # create followings and followers for eliza
        for i in range(2):
            follower = self.create_user('eliza_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.eliza)
        for i in range(3):
            following = self.create_user('eliza_following{}'.format(i))
            Friendship.objects.create(from_user=self.eliza, to_user=following)

    def test_list(self):
        # must log in
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # cannot use post
        response = self.jesse_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # blank at the begging
        response = self.jesse_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # user can view their own posts
        self.jesse_client.post(POST_TWEETS_URL, {'content': 'Hello World'})
        response = self.jesse_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # user can view posts posted by users they follow
        self.jesse_client.post(FOLLOW_URL.format(self.eliza.id))
        response = self.eliza_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter',
        })
        posted_tweet_id = response.data['id']
        response = self.jesse_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
