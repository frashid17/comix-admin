import stripe
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.conf import settings
from rest_framework import serializers
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from .models import Service, Order, Profile, Product, Feedback, Transaction, ProductReview, SupportMessage
from .serializers import (
    UserRegistrationSerializer, 
    ServiceSerializer, 
    OrderSerializer, 
    ExpoPushTokenSerializer, 
    ProductSerializer, 
    ProfileSerializer,
    FeedbackSerializer,
    TransactionSerializer,
    ProductReviewSerializer,
    SupportMessageSerializer
    )
from rest_framework.response import Response
from .utils import send_push_notification
from .serializers import ProfileSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

class CreateOrderView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        serializer.save(user=self.request.user)
        profile = self.request.user.profile
        if profile.expo_push_token:
            send_push_notification(
                token=profile.expo_push_token,
                title="Booking Confirmed!",
                message=f"Your booking for {order.service.name} at {order.appointment_time.strftime('%I:%M %p, %d %b')} has been confirmed!"
            )

class UserOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class SaveExpoPushTokenView(generics.UpdateAPIView):
    serializer_class = ExpoPushTokenSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        profile = request.user.profile  # Assumes user has a Profile linked
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.expo_push_token = serializer.validated_data['expo_push_token']
        profile.save()
        return Response({"message": "Push token saved successfully."}, status=status.HTTP_200_OK)

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.user != self.request.user:
            raise serializers.ValidationError("You can only review your own bookings.")
        serializer.save()

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        currency = "usd"
        description = request.data.get("description", "")

        if not amount:
            return Response({"error": "Amount is required."}, status=400)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # 1. Create payment intent with Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency=currency,
                description=description,
                metadata={"user_id": request.user.id}
            )

            # 2. Save to local DB as pending
            Transaction.objects.create(
                user=request.user,
                amount=float(amount) / 100,  # convert cents to dollars
                payment_method='stripe',
                status='pending',
                reference=intent.id,
                description=description
            )

            return Response({
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = []  # Public

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # 👈 we'll set this

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)

        # 🔁 Handle the event
        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            self._update_transaction(intent['id'], 'success')

        elif event['type'] == 'payment_intent.payment_failed':
            intent = event['data']['object']
            self._update_transaction(intent['id'], 'failed')

        return HttpResponse(status=200)

    def _update_transaction(self, payment_intent_id, status):
        try:
            txn = Transaction.objects.get(reference=payment_intent_id)
            txn.status = status
            txn.save()
        except Transaction.DoesNotExist:
            pass  

class CreateProductReviewView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SupportMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SupportMessage.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AdminSupportMessageView(generics.CreateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAdminUser]  # Only staff allowed

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        target_user = get_object_or_404(User, id=user_id)

        serializer.save(
            user=target_user,
            is_from_admin=True
        )