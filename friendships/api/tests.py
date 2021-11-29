from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

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

    def test_follow(self):
        url = FOLLOW_URL.format(self.jesse.id)

        # must log in to follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # use get
        response = self.eliza_client.get(url)
        self.assertEqual(response.status_code, 405)
        # follow oneself
        response = self.jesse_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow succeed
        response = self.eliza_client.post(url)
        self.assertEqual(response.status_code, 201)
        # follow twice
        response = self.eliza_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # follow back
        count = Friendship.objects.count()
        response = self.jesse_client.post(FOLLOW_URL.format(self.eliza.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.jesse.id)

        # must logged in to unfollow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # get is not allowed
        response = self.eliza_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow oneself
        response = self.jesse_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow successfully
        Friendship.objects.create(from_user=self.eliza, to_user=self.jesse)
        count = Friendship.objects.count()
        response = self.eliza_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)
        # unfollow a user when not already followed
        count = Friendship.objects.count()
        response = self.eliza_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.eliza.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # ordered by time
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'eliza_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'eliza_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'eliza_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.eliza.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # ordered by time
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'eliza_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'eliza_follower0',
        )
