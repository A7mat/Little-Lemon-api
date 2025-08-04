from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # path('menu-items/', views.MenuItem.as_view()),
    # path('menu-items/<int:pk>', views.SingleMenuItemsView.as_view()),
    path('groups/manager/users/', views.manager_view),
    path('groups/manager/users/<int:user_id>', views.remove_manager),
    path('groups/delivery-crew/users/', views.delivery_crew_view),
    path('groups/delivery-crew/users/<int:user_id>', views.remove_delivery_crew),
    path('menu-items/', views.menu_items),
    path('menu-items/<int:id>', views.single_item),
    path('cart/menu-items/', views.cart_menu_items),
    path('orders/', views.orders),
    path('orders/<int:order_id>', views.order_items),
    path('api-token-auth/', obtain_auth_token),
    path('throttle-check/', views.throttle_check),
    path('throttle-check-auth/', views.throttle_check_auth),
]