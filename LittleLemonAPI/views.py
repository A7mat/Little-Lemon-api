from django.shortcuts import render
from rest_framework import generics

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from .throttles import TenCallsPerMinute
from django.contrib.auth.models import Group, User

from django.db import transaction
from django.utils.timezone import now


# Create your views here.
# class MenuItemView(generics.ListCreateAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer
#     ordering_fields = ['price', 'inventory']
#     filterset_fields = ['price', 'inventory']
#     search_fields = ['category']
    
# class SingleMenuItemsView(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer

### MENU ITEMS API ###
@api_view(['POST', 'GET'])
def menu_items(request):
    if request.method == 'GET':
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=4)
        page = request.query_params.get('page', default=1)
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__istartswith=search) # 'i' makes it case insensitive
            # items = items.filter(search__contains=search)
        if ordering:
            ordering_fields = ordering.split(",")
            items = items.order_by(*ordering_fields)
            
        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serialized_item = MenuItemSerializer(items, many=True)
        return Response(serialized_item.data)
    if request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists():
            serialized_item = MenuItemSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_201_CREATED)
        else:
            return Response({"message":"You are not authorized for this action"}, status.HTTP_403_FORBIDDEN)
    # if request.method == 'PUT':
    #     if request.user.groups.filter(name='Manager').exists():
    #         pass # TODO something? not specified in assignment
    #     else:
    #         return Response({"message":"You are not authorized for this action"}, status.HTTP_403_FORBIDDEN)
    
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def single_item(request, id):
    item = get_object_or_404(MenuItem, pk=id)
    if request.method == 'GET':
        serialized_item = MenuItemSerializer(item)
        return Response(serialized_item.data)
    elif request.method == 'PUT' or request.method == 'PATCH':
        if request.user.groups.filter(name='Manager').exists():
            serializer = MenuItemSerializer(item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message":"You are not authorized for this action"}, status.HTTP_403_FORBIDDEN)
    elif request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message":"You are not authorized for this action"}, status.HTTP_403_FORBIDDEN)

### CART API ###
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_menu_items(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if request.method == 'GET':
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        menuitem_id = request.data.get('menuitem')
        quantity = request.data.get('quantity')

        if menuitem_id is None or quantity is None:
            return Response({"error": "menuitem and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError()
        except ValueError:
            return Response({"error": "quantity must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the MenuItem instance or return 404
        menuitem_instance = get_object_or_404(MenuItem, pk=menuitem_id)

        # Try to get existing cart item for user and menuitem
        try:
            cart_item = Cart.objects.get(user=user, menuitem=menuitem_instance)
        except Cart.DoesNotExist:
            cart_item = None

        # Prepare data for serializer
        data = request.data.copy()
        data['menuitem'] = menuitem_instance.id  # serializer expects ID here
        data['unit_price'] = menuitem_instance.price
        data['price'] = menuitem_instance.price * quantity

        serializer = CartSerializer(instance=cart_item, data=data, context={'request': request})

        if serializer.is_valid():
            # unit_price = menuitem_instance.price
            # total_price = unit_price * serializer.validated_data['quantity']
            serializer.save(user=user, menuitem=menuitem_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        cart_items.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def orders(request):
    user = request.user
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.filter(user=user)
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=user)
        else:
            orders = Order.objects.filter(user=user)
        to_price = request.query_params.get('to_price')
        order_id = request.query_params.get('id')
        status_param = request.query_params.get('status')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=4)
        page = request.query_params.get('page', default=1)
        if to_price:
            orders = orders.filter(total__lte=to_price)
        if order_id:
            orders = orders.filter(id__istartswith=order_id)
        if status_param:
            orders = orders.filter(status=status_param.lower() in ['true', '1'])
        if ordering:
            ordering_fields = ordering.split(",")
            orders = orders.order_by(*ordering_fields)
        paginator = Paginator(orders, per_page=perpage)
        try:
            orders = paginator.page(number=page)
        except EmptyPage:
            orders = []
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"message": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            total = sum([item.price for item in cart_items])
            order_data = {
                "user": user.id,
                "total": total,
                "date": now().date()
            }
            order_serializer = OrderSerializer(data=order_data)
            if order_serializer.is_valid():
                order = order_serializer.save(user=user, total=total, date=now().date())
            else:
                return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            for item in cart_items:
                order_item_data = {
                    'order': order.id,
                    'menuitem': item.menuitem.id,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'price': item.price
                }
                item_serializer = OrderItemSerializer(data=order_item_data)
                if item_serializer.is_valid():
                    item_serializer.save(order=order)
                else:
                    transaction.set_rollback(True)
                    return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            cart_items.delete()

        return Response({
            "order": OrderSerializer(order).data,
            "items": OrderItemSerializer(OrderItem.objects.filter(order=order), many=True).data
        }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_items(request, order_id):
    order_items = OrderItem.objects.filter(order=order_id)
    if request.method == 'GET':
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data, status.HTTP_200_OK)
    # if request.method == 'PUT' or request.method == 'PATCH':  # TODO last 4 rows of the table
    #     pass
    if request.method == 'DELETE':
        if request.user.groups.filter(name='Manager').exists():
            order = Order.objects.filter(id=order_id)
            order.delete()
            return Response({"message": "This order has been deleted."}, status.HTTP_200_OK)
        
### USER MANAGEMENT API ###
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manager_view(request):
    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'GET':
            manager_group = Group.objects.get(name='Manager')
            managers = manager_group.user_set.all()
            data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in managers]
            return Response(data, status=status.HTTP_200_OK)
        
        if request.method == 'POST':
            user_id = request.data.get("user_id")
            user_instance = get_object_or_404(User, pk=user_id)
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            manager_group.user_set.add(user_instance)
            return Response({"message": f"User '{user_instance.username}' added to Manager group"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"message":"You are not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_manager(request, user_id):
    if request.user.groups.filter(name="Manager").exists():
        if request.method == "DELETE":
            user_instance = get_object_or_404(User, pk=user_id)
            manager_group = Group.objects.get(name='Manager')
            if user_instance in manager_group.user_set.all():
                manager_group.user_set.remove(user_instance)
                return Response({"message":f"User '{user_instance.username} is removed from Manager group'"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "User is not in the Manager group."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"message":"You are not authorized"}, status=status.HTTP_403_FORBIDDEN)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delivery_crew_view(request):
    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'GET':
            manager_group = Group.objects.get(name='Delivery crew')
            managers = manager_group.user_set.all()
            data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in managers]
            return Response(data, status=status.HTTP_200_OK)
        
        if request.method == 'POST':
            user_id = request.data.get("user_id")
            user_instance = get_object_or_404(User, pk=user_id)
            manager_group, _ = Group.objects.get_or_create(name='Delivery crew')
            manager_group.user_set.add(user_instance)
            return Response({"message": f"User '{user_instance.username}' added to Delivery crew group"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"message":"You are not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_delivery_crew(request, user_id):
    if request.user.groups.filter(name="Manager").exists():
        if request.method == "DELETE":
            user_instance = get_object_or_404(User, pk=user_id)
            manager_group = Group.objects.get(name='Delivery crew')
            if user_instance in manager_group.user_set.all():
                manager_group.user_set.remove(user_instance)
                return Response({"message":f"User '{user_instance.username} is removed from Delivery crew group'"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "User is not in the Delivery crew group."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"message":"You are not authorized"}, status=status.HTTP_403_FORBIDDEN)

@api_view()
@throttle_classes([AnonRateThrottle])
def throttle_check(request):
    return Response({"message":"successful"})

@api_view()
@permission_classes([IsAuthenticated])
@throttle_classes([TenCallsPerMinute])
def throttle_check_auth(request):
    return Response({"message":"message for the logged in users only"})
