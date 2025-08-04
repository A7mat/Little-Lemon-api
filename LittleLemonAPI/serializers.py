from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from decimal import Decimal
from rest_framework.validators import UniqueValidator

# class MenuItemSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField(max_length=255)
#     price = serializers.DecimalField(max_digits=6, decimal_places=2)
#     inventory = serializers.IntegerField()
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
    
class MenuItemSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source='inventory')
    price_after_tax = serializers.SerializerMethodField(method_name= 'calculate_tax')
    category = CategorySerializer(read_only=True)
#     title = serializers.CharField(
#         max_length=255,
#         validators=[UniqueValidator(queryset=MenuItem.objects.all())]
#     )
    # price = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=2)
    # def validate_price(self, value):
    #     if value < 2:
    #         raise serializers.ValidationError('Price should not be less than 2.0')
    #     return value  # Return value if it passes validation

    # def validate_stock(self, value):
    #     if value < 0:
    #         raise serializers.ValidationError('Stock cannot be negative')
    #     return value  # Return value if it passes validation
    def validate(self, attrs):
        if(attrs['price']<2):
            raise serializers.ValidationError('Price should not be less than 2.0')
        if(attrs['inventory']<0):
            raise serializers.ValidationError('Stock cannot be negative')
        return super().validate(attrs)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'stock', 'price_after_tax', 'category']
        # depth = 1
        extra_kwargs = {
            # 'price': {'min_value': 2},
            # 'stock':{'source':'inventory', 'min_value': 0}
            'title': {
                'validators': [
                    UniqueValidator(
                        queryset=MenuItem.objects.all()
                    )
                ]
            }
            }
        
    def calculate_tax(self, product:MenuItem):
        return product.price * Decimal(1.1)
    
    def __str__(self):
        return self.title
    
class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    quantity = serializers.IntegerField()
    user = serializers.CharField(default=serializers.CurrentUserDefault())
    # unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    # price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'price']
        
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']
        # read_only_fields = ['id', 'user', 'total', 'date', 'delivery_crew', 'status']
        
class OrderItemSerializer(serializers.ModelSerializer):
    # menuitem = MenuItemSerializer()
    # quantity = serializers.IntegerField()
    # unit_price = serializers.DecimalField(max_digits=6, decimal_places=2)
    # price = serializers.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = ['order','menuitem', 'quantity', 'unit_price', 'price']
        # depth = 1

        