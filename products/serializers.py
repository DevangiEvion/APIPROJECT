from rest_framework import serializers 
from .models import*
from django.db import transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category_id', 'category_name', 'category']

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            errors = exc.detail

            if 'category_id' in errors:
                errors['category_id'] = ["The selected category does not exist. Please choose a valid category."]
            raise serializers.ValidationError(errors)
        

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'product_name', 'quantity', 'price', 'order_id']
        read_only_fields = ['user', 'price', 'order_id']


# Add to cart
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price']


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_description = serializers.CharField(source='product.description', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'product_id', 'product_name', 'product_description', 'product_price', 'quantity', 'price']




# class OrderSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(source='user.username',read_only=True)
#     cart_items = CartItemSerializer(many=True, read_only=True) 

#     class Meta:
#         model = Order
#         fields = ['id', 'user', 'total', 'discount', 'status', 'payment_status', 'created_at', 'cart_items']
#         read_only_fields = ['id', 'user', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
 
    class Meta:
        model = Order
        fields = ['id', 'user', 'total', 'discount', 'status', 'payment_status', 'created_at', 'items']


# Purchase
class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']
        read_only_fields = ['price', 'product_name']


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = Purchase
        fields = ['id', 'user', 'total_amount', 'items']
        read_only_fields = ['user', 'total_amount']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not items_data:
            raise serializers.ValidationError({"items": "At least one item is required."})

        user = self.context['request'].user
        purchase = Purchase.objects.create(user=user, total_amount=0)
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            price = product.price * quantity
            total_amount += price

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                price=price
            )

        purchase.total_amount = total_amount
        purchase.save()
        return purchase

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        instance.items.all().delete()
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            price = product.price * quantity
            total_amount += price

            PurchaseItem.objects.create(
                purchase=instance,
                product=product,
                quantity=quantity,
                price=price
            )

        instance.total_amount = total_amount
        instance.save()
        return instance
    
# Return product
class ProductReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductReturnItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']
        read_only_fields = ['price', 'product_name']


class ProductReturnSerializer(serializers.ModelSerializer):
    items = ProductReturnItemSerializer(many=True)

    class Meta:
        model = ProductReturn
        fields = ['id', 'user', 'total_amount', 'created_at', 'updated_at', 'items']
        read_only_fields = ['user', 'total_amount', 'created_at', 'updated_at']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not items_data:
            raise serializers.ValidationError({"items": "At least one item is required."})

        user = self.context['request'].user
        product_return = ProductReturn.objects.create(user=user, total_amount=0)
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            if quantity > product.stock:
                raise serializers.ValidationError(
                    {"items": f"Not enough stock for {product.name}. Only {product.stock} left."}
                )

            # Decrease stock when returning
            product.stock -= quantity
            product.save()

            price = product.price * quantity
            total_amount += price

            ProductReturnItem.objects.create(
                productreturn=product_return,
                product=product,
                quantity=quantity,
                price=price
            )

        product_return.total_amount = total_amount
        product_return.save()
        return product_return

    @transaction.atomic
    def update(self, instance, validated_data):
        # Reverse old stock changes
        for old_item in instance.items.all():
            old_item.product.stock += old_item.quantity
            old_item.product.save()

        instance.items.all().delete()
        items_data = validated_data.pop('items', [])
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            if quantity > product.stock:
                raise serializers.ValidationError(
                    {"items": f"Not enough stock for {product.name}. Only {product.stock} left."}
                )

            # Decrease stock for updated return
            product.stock -= quantity
            product.save()

            price = product.price * quantity
            total_amount += price

            ProductReturnItem.objects.create(
                productreturn=instance,
                product=product,
                quantity=quantity,
                price=price
            )

        instance.total_amount = total_amount
        instance.save()
        return instance


# PurchaseSerializer (Increase Stock)
class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = Purchase
        fields = ['id', 'user', 'total_amount', 'items']
        read_only_fields = ['user', 'total_amount']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        if not items_data:
            raise serializers.ValidationError({"items": "At least one item is required."})

        user = self.context['request'].user
        purchase = Purchase.objects.create(user=user, total_amount=0)
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            # Increase stock when purchasing
            product.stock += quantity
            product.save()

            price = product.price * quantity
            total_amount += price

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                price=price
            )

        purchase.total_amount = total_amount
        purchase.save()
        return purchase

    @transaction.atomic
    def update(self, instance, validated_data):
        # Reverse stock from old purchase
        for old_item in instance.items.all():
            old_item.product.stock -= old_item.quantity
            old_item.product.save()

        instance.items.all().delete()
        items_data = validated_data.pop('items', [])
        total_amount = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            # Increase stock for updated purchase
            product.stock += quantity
            product.save()

            price = product.price * quantity
            total_amount += price

            PurchaseItem.objects.create(
                purchase=instance,
                product=product,
                quantity=quantity,
                price=price
            )

        instance.total_amount = total_amount
        instance.save()
        return instance


