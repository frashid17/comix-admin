from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Service, Order,Product, Feedback, Transaction, ProductReview, SupportMessage

class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True, required=True)
    gender = serializers.ChoiceField(write_only=True, choices=Profile.GENDER_CHOICES)

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number', 'gender')

    def create(self, validated_data):
        phone_number = validated_data.pop('phone_number')
        gender = validated_data.pop('gender')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        Profile.objects.create(user=user, phone_number=phone_number, gender=gender)

        return user

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('user', 'status', 'created_at')

class ExpoPushTokenSerializer(serializers.Serializer):
    expo_push_token = serializers.CharField()

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'phone_number',
            'gender',
            'date_of_birth',
            'address',
            'city',
            'country',
            'profile_picture',
            'latitude',
            'longitude',
        ]

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'order', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = '__all__'

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class SupportMessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SupportMessage
        fields = ['id', 'user', 'message', 'is_from_admin', 'response_to', 'created_at']
        read_only_fields = ['id', 'user', 'is_from_admin', 'created_at']

