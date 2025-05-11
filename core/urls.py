from django.urls import path
from .views import (
UserRegistrationView, 
ServiceListView, 
CreateOrderView, 
UserOrderListView, 
SaveExpoPushTokenView,
ProductListView,
UserProfileView,
FeedbackCreateView

)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('services/', ServiceListView.as_view(), name='service_list'),
    path('book/', CreateOrderView.as_view(), name='create_order'),
    path('my-bookings/', UserOrderListView.as_view(), name='user_order_list'),
    path('save-token/', SaveExpoPushTokenView.as_view(), name='save_expo_token'),
    path('products/', ProductListView.as_view(), name='products'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('feedback/', FeedbackCreateView.as_view(), name='submit-feedback'),
]
