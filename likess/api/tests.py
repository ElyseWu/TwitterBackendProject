from testing.testcases import TestCase
from rest_framework.test import APIClient


LIKE_BASE_URL = '/api/likess/'
LIKE_CANCEL_URL = '/api/likess/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class LikeApiTests(TestCase):

    def setUp(self):
        self.jesse, self.jesse_client = self.create_user_and_client('jesse')
        self.eliza, self.eliza_client = self.create_user_and_client('eliza')

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.jesse)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.jesse_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # post success
        response = self.jesse_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicate likess
        self.jesse_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.eliza_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.jesse)
        comment = self.create_comment(self.eliza, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.jesse_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.jesse_client.post(LIKE_BASE_URL, {
            'content_type': 'coment',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.jesse_client.post(LIKE_BASE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id'in response.data['errors'], True)

        # post success
        response = self.jesse_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicate likess
        response = self.jesse_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        self.eliza_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_cancel(self):
        tweet = self.create_tweet(self.jesse)
        comment = self.create_comment(self.eliza, tweet)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}
        self.jesse_client.post(LIKE_BASE_URL, like_comment_data)
        self.eliza_client.post(LIKE_BASE_URL, like_tweet_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # login required
        response = self.anonymous_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.jesse_client.get(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.jesse_client.post(LIKE_CANCEL_URL, {
            'content_type': 'wrong',
            'object_id': 1,
        })
        self.assertEqual(response.status_code, 400)

        # wrong object_id
        response = self.jesse_client.post(LIKE_CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)

        # eliza has not liked before
        response = self.eliza_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # successfully canceled
        response = self.jesse_client.post(LIKE_CANCEL_URL, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # jesse has not liked before
        response = self.jesse_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # eliza's like has been canceled
        response = self.eliza_client.post(LIKE_CANCEL_URL, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.jesse)
        comment = self.create_comment(self.jesse, tweet)

        # test anonymous
        anonymous_client = APIClient()
        response = anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list api
        response = self.eliza_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)
        self.create_like(self.eliza, comment)
        response = self.eliza_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test tweet detail api
        self.create_like(self.jesse, comment)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.eliza_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_in_tweets_api(self):
        tweet = self.create_tweet(self.jesse)

        # test tweet detail api
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.eliza_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        self.create_like(self.eliza, tweet)
        response = self.eliza_client.get(url)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)

        # test tweets list api
        response = self.eliza_client.get(TWEET_LIST_API, {'user_id': self.jesse.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tweets'][0]['has_liked'], True)
        self.assertEqual(response.data['tweets'][0]['likes_count'], 1)

        # test newsfeeds list api
        self.create_like(self.jesse, tweet)
        self.create_newsfeed(self.eliza, tweet)
        response = self.eliza_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['likes_count'], 2)

        # test likess details
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.eliza_client.get(url)
        self.assertEqual(len(response.data['likess']), 2)
        self.assertEqual(response.data['likess'][0]['user']['id'], self.jesse.id)
        self.assertEqual(response.data['likess'][1]['user']['id'], self.eliza.id)
