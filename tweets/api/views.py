from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.models import Tweet
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerWithComments
)
from newsfeeds.services import NewsFeedService
from utils.decorators import required_params


class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializerForCreate

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        return Response(TweetSerializerWithComments(tweet).data)

    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(
            tweets,
            context={'request': request},
            many=True,
        )
        return Response({'tweets': serializer.data})

    # def list(self, request):
    #     if 'user_id' not in request.query_params:
    #         return Response('missing user_id', status=400)
    #     user_id = request.query_params['user_id']
    #     tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
    #     serializer = TweetSerializer(tweets, many=True)
    #     return Response({'tweets': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        serializer = TweetSerializer(tweet, context={'request': request})
        return Response(serializer.data, status=201)