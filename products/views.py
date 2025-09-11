from rest_framework import viewsets, generics, permissions,status, status as drf_status
from rest_framework.response import Response
from .models import*
from .serializers import CategorySerializer,ProductSerializer, CartSerializer,OrderSerializer, PurchaseSerializer, ProductReturnSerializer,OrderItemSerializer
from rest_framework import filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from django.db import transaction
from rest_framework.views import APIView
from datetime import datetime, time
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum, F, Value, Q
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io
from django.template.loader import get_template



# Product Views

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = []

    def list(self, request, *args, **kwargs):
        category_id = request.query_params.get('category')

        # If category filter is used
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return Response({
                    "status": False,
                    "message": f"Category with ID '{category_id}' does not exist.plz enter valid/exist category id.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get products in that category
            products = Product.objects.filter(category=category)
            product_serializer = self.get_serializer(products, many=True)
            category_serializer = CategorySerializer(category)

            return Response({
                "status": True,
                "message": "Products retrieved successfully." if products else "No products found for this category.",
                "data": {
                    "category": category_serializer.data,
                    "products": product_serializer.data
                }
            }, status=status.HTTP_200_OK)

        # No category filter: return all products
        products = Product.objects.all()
        product_serializer = self.get_serializer(products, many=True)
        return Response({
            "status": True,
            "message": "All products retrieved successfully.",
            "data": product_serializer.data
        }, status=status.HTTP_200_OK)

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can add products",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Product created successfully",
                "data": serializer.data
            }, status=drf_status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error",
            "data": serializer.errors
        }, status=drf_status.HTTP_400_BAD_REQUEST)

class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def put(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can update products",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Product updated successfully",
                "data": serializer.data
            }, status=drf_status.HTTP_200_OK)
        return Response({
            "status": False,
            "message": "Validation error",
            "data": serializer.errors
        }, status=drf_status.HTTP_400_BAD_REQUEST)

class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def delete(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can delete products",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "status": True,
            "message": "Product deleted successfully",
            "data": None
        }, status=drf_status.HTTP_200_OK)

# Category Views

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        categories = self.get_queryset()
        serializer = self.get_serializer(categories, many=True)
        return Response({
            "status": True,
            "message": "Categories retrieved successfully",
            "data": serializer.data
        }, status=drf_status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can add categories",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Category created successfully",
                "data": serializer.data
            }, status=drf_status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error",
            "data": serializer.errors
        }, status=drf_status.HTTP_400_BAD_REQUEST)

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category)
        return Response({
            "status": True,
            "message": "Category retrieved successfully",
            "data": serializer.data
        })

    def put(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can update categories",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({
                "status": False,
                "message": "Only admin can delete categories",
                "data": None
            }, status=drf_status.HTTP_403_FORBIDDEN)

        return super().delete(request, *args, **kwargs)


# Cart Views

class CartListCreateView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user, order__isnull=True)

    def perform_create(self, serializer):
        product = Product.objects.get(id=serializer.validated_data['product'].id)
        quantity = serializer.validated_data['quantity']

        print("stock:", product.stock)           
        print("Quantity:", quantity)


        if quantity > product.stock:
            raise ValidationError({"quantity": "Product out of stock."})

        price = product.price * quantity
        serializer.save(user=self.request.user, price=price)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": True,
            "message": "Cart items retrieved successfully",
            "data": serializer.data
        }, status=drf_status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product')

        if not product_id:
            return Response({
                "status": False,
                "message": "Product ID is required.",
                "data": None
            }, status=drf_status.HTTP_400_BAD_REQUEST)

        existing = Cart.objects.filter(user=request.user, product_id=product_id, order__isnull=True).first()
        if existing:
            return Response({
                "status": False,
                "message": "Product already in cart. You can update quantity instead.",
                "data": None
            }, status=drf_status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": True,
                "message": "Product added to cart",
                "data": serializer.data
            }, status=drf_status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "message": "Validation error",
            "data": serializer.errors
        }, status=drf_status.HTTP_400_BAD_REQUEST)


class CartUpdateView(generics.UpdateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def put(self, request, *args, **kwargs):
        cart_item = self.get_object()
        if cart_item.user != request.user:
            return Response({
                "status": False,
                "message": "You are not allowed to update this item",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        quantity = request.data.get('quantity')
        if not quantity or int(quantity) <= 0:
            return Response({
                "status": False,
                "message": "Quantity must be greater than 0",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = int(quantity)
        cart_item.price = cart_item.product.price * cart_item.quantity
        cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response({
            "status": True,
            "message": "Cart item updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    



class CartDeleteView(generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
    
        if cart_item.user != request.user:
            return Response({
                "status": False,
                "message": "You are not allowed to delete this item",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        if instance.order is None:
            instance.product.stock += instance.quantity
            instance.product.save()

        instance.delete()

        return Response({
            "status": True,
            "message": "Cart item deleted successfully"
        }, status=status.HTTP_200_OK)
    


# Optional
class CartClearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({
            "status": True,
            "message": "All cart items cleared",
            "data": None
        }, status=status.HTTP_200_OK)



# Order views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from products.models import Order, OrderItem, Cart

class OrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create_order(request):
        user = request.user

        # Get all cart items of the user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            return JsonResponse({"error": "Cart is empty"}, status=400)

        # Calculate total price
        total = sum(item.price for item in cart_items)

        # Create the order
        order = Order.objects.create(user=user, total=total)

        # Create OrderItems from Cart
        order_items = []
        for cart_item in cart_items:
            order_items.append(OrderItem(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price
            ))
        OrderItem.objects.bulk_create(order_items)

        # Clear the cart
        cart_items.delete()

        return JsonResponse({
            "message": "Order created successfully",
            "order_id": order.id
        }, status=201)

    def get(self, request, pk=None):
        if pk:
            try:
                order = Order.objects.prefetch_related("items__product").get(pk=pk, user=request.user)
            except Order.DoesNotExist:
                return Response({"status": False, "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"status": True})

        orders = Order.objects.filter(user=request.user).prefetch_related("items__product")
        return Response({"status": True})

    @transaction.atomic
    def post(self, request):
        data = request.data.copy()
        items_data = data.pop("items", [])

        if not items_data:
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return Response({"status": False, "message": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)
            items_data = [{"product": c.product.id, "quantity": c.quantity} for c in cart_items]

        # Calculate total
        total = 0
        for item in items_data:
            try:
                product = Product.objects.get(id=item["product"])
            except Product.DoesNotExist:
                return Response({"status": False, "message": f"Product {item['product']} not found"}, status=status.HTTP_400_BAD_REQUEST)
            if item["quantity"] > product.stock:
                return Response({"status": False, "message": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
            total += product.price * item["quantity"]

        order = Order.objects.create(
            user=request.user,
            total=total,
            discount=data.get("discount", 0),
            status=data.get("status", "pending"),
            payment_status=data.get("payment_status", "unpaid")
        )

        for item in items_data:
            product = Product.objects.get(id=item["product"])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price=product.price * item["quantity"]
            )
            product.stock -= item["quantity"]
            product.save()

        if not request.data.get("items"):
            Cart.objects.filter(user=request.user).delete()

        return Response({"status": True, "message": "Order created", "data": OrderSerializer(order).data}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def put(self, request, pk):
        return self._update_order(pk, request, partial=False)

    @transaction.atomic
    def patch(self, request, pk):
        return self._update_order(pk, request, partial=True)

    def delete(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"status": False, "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        order.delete()
        return Response({"status": True, "message": "Order deleted"})


    def _update_order(self, pk, request, partial):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"status": False, "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        items_data = data.pop("items", None)

        for attr, value in data.items():
            setattr(order, attr, value)
        order.save()

        if items_data is not None:
            order.items.all().delete()
            total = 0
            for item in items_data:
                try:
                    product = Product.objects.get(id=item["product"])
                except Product.DoesNotExist:
                    return Response({"status": False, "message": f"Product {item['product']} not found"}, status=status.HTTP_400_BAD_REQUEST)
                if item["quantity"] > product.stock:
                    return Response({"status": False, "message": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=product.price * item["quantity"]
                )
                product.stock -= item["quantity"]
                product.save()
                total += product.price * item["quantity"]

            order.total = total
            order.save()

        return Response({"status": True, "message": "Order updated", "data": OrderSerializer(order).data})
    


# Purchase
class PurchaseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                purchase = Purchase.objects.prefetch_related('items__product').get(id=pk, user=request.user)
            except Purchase.DoesNotExist:
                return Response({"status": False, "message": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = PurchaseSerializer(purchase)
        else:
            purchases = Purchase.objects.filter(user=request.user).prefetch_related('items__product')
            serializer = PurchaseSerializer(purchases, many=True)

        return Response({
            "status": True,
            "message": "Purchase(s) retrieved successfully."
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data.copy()
        items = data.get('items')

        # Ensure items is a list of dictionaries
        if not isinstance(items, list):
            return Response({
                "status": False,
                "message": "Items must be an array of dictionaries.",
            }, status=status.HTTP_400_BAD_REQUEST)

        data['items'] = items
        serializer = PurchaseSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Purchase created successfully.",
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "message": "Validation error.",
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            purchase = Purchase.objects.get(id=pk, user=request.user)
        except Purchase.DoesNotExist:
            return Response({"status": False, "message": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PurchaseSerializer(purchase, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Purchase updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "message": "Validation error.",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            purchase = Purchase.objects.get(id=pk, user=request.user)
        except Purchase.DoesNotExist:
            return Response({"status": False, "message": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

        purchase.delete()
        return Response({
            "status": True,
            "message": "Purchase deleted successfully."
        }, status=status.HTTP_200_OK)
    


# Return Products
class ProductReturnViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReturnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Product return successfully."
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Validation error."
        }, status=status.HTTP_400_BAD_REQUEST)
    

# Order Report according to start dates and end dates
class OrderReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if getattr(request.user, "role", None) != "admin":
            return Response({
                "status": False,
                "message": "You do not have permission to generate this report."
            }, status=status.HTTP_403_FORBIDDEN)

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({
                "status": False,
                "message": "Both start_date and end_date are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

        if not start_date or not end_date:
            return Response({
                "status": False,
                "message": "Invalid date format. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        start_datetime = timezone.make_aware(datetime.combine(start_date, time.min))
        end_datetime = timezone.make_aware(datetime.combine(end_date, time.max))

        orders = (
            Order.objects.filter(created_at__range=(start_datetime, end_datetime))
            .prefetch_related("items__product")
        )

        serializer = OrderSerializer(orders, many=True)
        total_amount = sum(order.total for order in orders)

        return Response({
            "status": True,
            "message": "Orders retrieved successfully.",
            "start_date": start_date_str,
            "end_date": end_date_str,
            "total_amount": total_amount,
            "orders": serializer.data
        }, status=status.HTTP_200_OK)
    

# User Order Report
class UserOrderReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if getattr(request.user, "role", None) != "admin" and request.user.id != int(user_id):
            return Response({
                "status": False,
                "message": "You do not have permission to view this report."
            }, status=status.HTTP_403_FORBIDDEN)

        orders = (
            Order.objects.filter(user_id=user_id)
            .prefetch_related("items__product")
        )

        serializer = OrderSerializer(orders, many=True)
        total_amount = sum(order.total for order in orders)

        return Response({
            "status": True,
            "message": f"Orders for user {user_id} retrieved successfully.",
            "total_amount": total_amount,
            "orders": serializer.data
        }, status=status.HTTP_200_OK)



# Product Sale Report
class ProductSalesReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if getattr(request.user, "role", None) != "admin":
            return Response({
                "status": False,
                "message": "You do not have permission to view this report."
            }, status=status.HTTP_403_FORBIDDEN)

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({
                'status': False,
                'message': 'Both start_date and end_date are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)

        if not start_date or not end_date:
            return Response({
                'status': False,
                'message': "Invalid date format. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, time.min))
        end_datetime = timezone.make_aware(datetime.combine(end_date, time.max))

        products_data = (
            Product.objects
            .annotate(
                total_sold_quantity=Coalesce(Sum('orderitem__quantity',filter=Q(orderitem__order__created_at__range=(start_datetime, end_datetime))), Value(0)),
                stock_quantity=F('stock') 
            )
            .values(
                product_name=F('name'),
                product_price=F('price'),
                stock_quantity=F('stock_quantity'),
                total_sold_quantity=F('total_sold_quantity')
            )
            .order_by('name')
        )

        return Response({
            "status": True,
            "message": "Products sales report generated successfully.",
            "start_date": start_date_str,
            "end_date": end_date_str,
            "products": list(products_data)
        }, status=status.HTTP_200_OK)
    
    
# Purchase report
class PurchaseReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) != 'admin':
            return Response({
                'status':False, 
                'message': "You do not have permission to view this report."
            }, status=status.HTTP_403_FORBIDDEN)
        
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        user_id = request.query_params.get('user_id')

        if not start_date_str or not end_date_str:
            return Response({
                'status': False,
                'message' : 'Both start_date and end_date are required(YYYY-MM-DD).'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)


        if not start_date or not end_date:
            return Response({
                'status': False,
                'message': "Invalid date format. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, time.min)) 
        end_datetime = timezone.make_aware(datetime.combine(end_date, time.max))

        purchases = Purchase.objects.filter(created_at__range=(start_datetime, end_datetime))

        if user_id:
            purchases = purchases.filter(user_id=user_id)

        serializer = PurchaseSerializer(purchases, many=True)
        total_amount = sum(p.total_amount for p in purchases)

        return Response({
            'status' : True,
            'message' : "Purchase report generated successfully.",
            'start_date' : start_date_str,
            'end_date' : end_date_str,
            'total_amount' : total_amount,
            'purchases' : serializer.data
        }, status=status.HTTP_200_OK)


# # Invoice 
# class InvoiceView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, purchase_id):
#        purchase = get_object_or_404(Purchase, id=purchase_id)

#        if request.user.role != 'admin' and request.user != purchase.user:
#            return HttpResponse("Permission denied", status=403)
       
#        html = render_to_string("invoice.html", {"purchase": purchase})
#        return HttpResponse(html)


# class InvoicePDFView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, purchase_id):
#         purchase = get_object_or_404(Purchase, id=purchase_id)

#         if request.user.role != "admin" and request.user != purchase.user:
#             return HttpResponse("Permission denied", status=403)

#         html = render_to_string("invoice.html", {"purchase": purchase})
#         response = HttpResponse(content_type="application/pdf")
#         response["Content-Disposition"] = f"attachment; filename=invoice_{purchase_id}.pdf"

#         pisa.CreatePDF(io.StringIO(html), dest=response)
#         return response

# def invoice(request):
#     return render(request, "invoice.html")


def invoice_view(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    return render(request, "invoice.html", {"purchase": purchase})


# PDF invoice download
def invoice_pdf(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)

    template_path = "invoice.html"
    context = {"purchase": purchase}
    template = get_template(template_path)
    html = template.render(context)

    # Create PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{purchase.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response



# Order Invoice
# def Order_invoice(request, order_id):
#     order = Order.objects.prefetch_related("items__product").get(pk=order_id)
#     items = Cart.objects.filter(order=order).values_list("product_id", flat=True)
#     product = Product.objects.filter(id__in=items).values()
#     cart_items = Cart.objects.filter(order=order).select_related("product")
#     print(cart_items)
#     return render(request, "Order_invoice.html", {"order": order, "products": product, "cart_items": cart_items})


from django.shortcuts import render, get_object_or_404
from .models import Order, Cart

def Order_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    cart_items = Cart.objects.filter(order=order).select_related("product")
    total = [item.product.price * item.quantity for item in cart_items]
    discount = order.discount

    grand_total = sum(total) - discount

    return render(
        request,
        "Order_invoice.html",
        {
            "order": order,
            "products": cart_items,
            "total": total,
            "grand_total": grand_total
        }
    )

# PDF invoice download
def Order_invoice_pdf(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), id=order_id
    )

    template = get_template("invoice.html")
    html = template.render({"order": order})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response


# from django.db import transaction

# @transaction.atomic
# def create_order_from_cart(user):
#     cart_items = Cart.objects.filter(user=user, order__isnull=True)

#     if not cart_items.exists():
#         raise ValueError("No items in cart")

#     # Calculate total
#     total = sum([item.price * item.quantity for item in cart_items])

#     # Create Order
#     order = Order.objects.create(
#         user=user,
#         total=total,
#         discount=0,
#         status="pending",
#         payment_status="unpaid"
#     )

#     # Create OrderItems from Cart
#     for cart_item in cart_items:
#         OrderItem.objects.create(
#             order=order,
#             product=cart_item.product,
#             quantity=cart_item.quantity,
#             price=cart_item.product.price
#         )
#         # Attach order to cart (optional, if you want to keep track)
#         cart_item.order = order
#         cart_item.save()

#     return order
