from rest_framework import  serializers

from comments.api.serializers import CommentSerializer
from likes.services import LikeService
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet, UserSerializer


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'created_at', 'content')

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)


class TweetSerializerWithComments(serializers.ModelSerializer):
    user = UserSerializer()
    comments = CommentSerializer(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'comments', 'created_at', 'content')


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet

