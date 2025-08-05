from rest_framework import generics, permissions, status as drf_status
from rest_framework.response import Response
from .models import*
from .serializers import CategorySerializer,ProductSerializer

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = []  #No authentication required

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": True,
            "message": "Products retrieved successfully",
            "data": serializer.data
        }, status=drf_status.HTTP_200_OK)


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
            print("Saving category:", serializer.validated_data)
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
