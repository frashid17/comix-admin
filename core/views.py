from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Service, Order
from .serializers import UserRegistrationSerializer, ServiceSerializer, OrderSerializer, ExpoPushTokenSerializer
from rest_framework.response import Response
from .utils import send_push_notification

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
