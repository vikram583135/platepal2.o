"""
Serializers for orders app
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, Review, ItemReview
from apps.restaurants.models import MenuItem
from apps.restaurants.serializers import RestaurantListSerializer, MenuItemSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    menu_item = MenuItemSerializer(read_only=True)
    menu_item_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'menu_item', 'menu_item_id', 'name', 'description', 'quantity',
                  'unit_price', 'total_price', 'selected_modifiers')
        read_only_fields = ('id', 'name', 'description', 'unit_price', 'total_price')


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    restaurant = RestaurantListSerializer(read_only=True)
    restaurant_id = serializers.IntegerField(write_only=True, required=False)
    delivery_address = serializers.SerializerMethodField()
    combined_parent_id = serializers.IntegerField(source='combined_parent.id', read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id',
            'order_number',
            'customer',
            'customer_email',
            'restaurant',
            'restaurant_id',
            'delivery_address',
            'status',
            'order_type',
            'priority_tag',
            'subtotal',
            'tax_amount',
            'delivery_fee',
            'tip_amount',
            'discount_amount',
            'total_amount',
            'promotion',
            'promo_code',
            'special_instructions',
            'kitchen_notes',
            'internal_cooking_notes',
            'is_scheduled',
            'scheduled_for',
            'estimated_preparation_time',
            'prep_time_override_minutes',
            'estimated_delivery_time',
            'sla_breached',
            'sla_breach_reason',
            'combined_parent_id',
            'print_count',
            'items',
            'created_at',
            'accepted_at',
            'preparing_at',
            'ready_at',
            'picked_up_at',
            'delivered_at',
        )
        read_only_fields = ('id', 'order_number', 'customer', 'status', 'subtotal', 'tax_amount',
                           'delivery_fee', 'total_amount', 'created_at', 'accepted_at', 'preparing_at',
                           'ready_at', 'picked_up_at', 'delivered_at', 'combined_parent_id', 'print_count',
                           'sla_breached', 'sla_breach_reason')
    
    def get_delivery_address(self, obj):
        if obj.delivery_address:
            return {
                'id': obj.delivery_address.id,
                'label': obj.delivery_address.label,
                'street': obj.delivery_address.street,
                'city': obj.delivery_address.city,
                'state': obj.delivery_address.state,
                'postal_code': obj.delivery_address.postal_code,
                'latitude': str(obj.delivery_address.latitude) if obj.delivery_address.latitude else None,
                'longitude': str(obj.delivery_address.longitude) if obj.delivery_address.longitude else None,
            }
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        include_internal = self.context.get('include_internal', False)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        is_restaurant_context = include_internal or (user and getattr(user, 'role', None) in ['RESTAURANT', 'ADMIN'])
        if not is_restaurant_context:
            data.pop('kitchen_notes', None)
            data.pop('internal_cooking_notes', None)
        return data


class OrderCreateSerializer(serializers.ModelSerializer):
    """Order creation serializer"""
    restaurant_id = serializers.IntegerField(write_only=True)
    delivery_address_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    items = OrderItemSerializer(many=True, write_only=True)
    contactless_delivery = serializers.BooleanField(required=False, default=False)
    priority_tag = serializers.ChoiceField(choices=Order.PriorityTag.choices, required=False, default=Order.PriorityTag.NORMAL)
    
    class Meta:
        model = Order
        fields = (
            'restaurant_id',
            'delivery_address_id',
            'order_type',
            'priority_tag',
            'items',
            'promo_code',
            'special_instructions',
            'tip_amount',
            'is_scheduled',
            'scheduled_for',
            'contactless_delivery',
        )
    
    def create(self, validated_data):
        from django.db import transaction
        from apps.restaurants.models import Restaurant
        from apps.accounts.models import Address
        from datetime import datetime
        import uuid
        
        items_data = validated_data.pop('items')
        # Get customer from context or from the save() call
        customer = self.context['request'].user
        
        # Extract IDs and convert to ForeignKey objects
        restaurant_id = validated_data.pop('restaurant_id')
        delivery_address_id = validated_data.pop('delivery_address_id', None)
        contactless_delivery = validated_data.pop('contactless_delivery', False)
        
        # Get restaurant object
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError({'restaurant_id': f'Restaurant with id {restaurant_id} does not exist'})
        
        # Get delivery address if provided
        delivery_address = None
        if delivery_address_id:
            try:
                delivery_address = Address.objects.get(id=delivery_address_id, user=customer)
            except Address.DoesNotExist:
                raise serializers.ValidationError({'delivery_address_id': 'Invalid delivery address'})
        
        # Convert tip_amount to Decimal if provided
        tip_amount = validated_data.pop('tip_amount', None)
        if tip_amount is not None:
            try:
                tip_amount = Decimal(str(tip_amount))
            except (ValueError, TypeError):
                tip_amount = Decimal('0.00')
        else:
            tip_amount = Decimal('0.00')
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Create order with temporary order number (will be updated after save)
            temp_order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                delivery_address=delivery_address,
                order_number=temp_order_number,
                contactless_delivery=contactless_delivery,
                tip_amount=tip_amount,
                **validated_data
            )
            
            # Generate proper order number with actual ID
            order.order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order.id:06d}"
            
            # Create order items
            subtotal = Decimal('0.00')
            for item_data in items_data:
                menu_item_id = item_data.pop('menu_item_id', None)
                if not menu_item_id:
                    raise serializers.ValidationError({'items': 'menu_item_id is required for each item'})
                
                try:
                    menu_item = MenuItem.objects.get(id=menu_item_id)
                except MenuItem.DoesNotExist:
                    raise serializers.ValidationError({'items': f'Menu item with id {menu_item_id} does not exist'})
                
                # Create order item (save() method will calculate total_price)
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    name=menu_item.name,
                    description=menu_item.description or '',
                    quantity=item_data.get('quantity', 1),
                    unit_price=menu_item.price,
                    selected_modifiers=item_data.get('selected_modifiers', [])
                )
                # Refresh from DB to get calculated total_price
                order_item.refresh_from_db()
                subtotal += order_item.total_price
            
            # Calculate totals - ensure all are Decimal
            order.subtotal = subtotal
            order.tax_amount = subtotal * Decimal('0.10')  # 10% tax (mock)
            # Handle delivery fee - convert to Decimal if it exists
            if restaurant.delivery_fee is not None:
                try:
                    order.delivery_fee = Decimal(str(restaurant.delivery_fee))
                except (ValueError, TypeError):
                    order.delivery_fee = Decimal('0.00')
            else:
                order.delivery_fee = Decimal('0.00')
            
            # Initialize discount_amount to Decimal('0.00') by default
            order.discount_amount = Decimal('0.00')
            
            # Apply promotion if provided
            promo_code = validated_data.get('promo_code')
            if promo_code:
                try:
                    from apps.restaurants.models import Promotion
                    from django.utils import timezone
                    promotion = Promotion.objects.get(
                        code=promo_code,
                        is_active=True,
                        valid_from__lte=timezone.now(),
                        valid_until__gte=timezone.now()
                    )
                    order.promotion = promotion
                    # Calculate discount - ensure all values are Decimal
                    if promotion.discount_type == 'PERCENTAGE':
                        discount_value = Decimal(str(promotion.discount_value))
                        discount = subtotal * (discount_value / Decimal('100'))
                        if promotion.maximum_discount:
                            max_discount = Decimal(str(promotion.maximum_discount))
                            discount = min(discount, max_discount)
                    else:
                        discount = Decimal(str(promotion.discount_value))
                    order.discount_amount = discount
                except Promotion.DoesNotExist:
                    pass
            
            # Calculate total and save
            order.calculate_total()
            order.save()
        
        return order


class ItemReviewSerializer(serializers.ModelSerializer):
    """Item review serializer"""
    
    class Meta:
        model = ItemReview
        fields = ('id', 'review', 'order_item', 'menu_item', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')


class ReviewSerializer(serializers.ModelSerializer):
    """Review serializer"""
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_photo = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    item_reviews = ItemReviewSerializer(many=True, read_only=True)
    image_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ('id', 'order', 'customer', 'customer_email', 'customer_name', 'customer_photo',
                  'restaurant', 'restaurant_name', 'restaurant_rating', 'food_rating', 'delivery_rating',
                  'comment', 'images', 'image_urls', 'is_approved', 'is_flagged', 'restaurant_reply',
                  'restaurant_replied_at', 'item_reviews', 'created_at')
        read_only_fields = ('id', 'customer', 'restaurant', 'is_approved', 'is_flagged',
                           'restaurant_replied_at', 'created_at')
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.email
    
    def get_customer_photo(self, obj):
        if obj.customer.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.customer.profile_photo.url)
            return obj.customer.profile_photo.url
        return None
    
    def get_image_urls(self, obj):
        if not obj.images:
            return []
        request = self.context.get('request')
        if request:
            return [request.build_absolute_uri(img) if not img.startswith('http') else img for img in obj.images]
        return obj.images
    
    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        validated_data['restaurant'] = validated_data['order'].restaurant
        # Auto-approve reviews (in production, add moderation)
        validated_data['is_approved'] = True
        return super().create(validated_data)

