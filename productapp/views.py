from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer
from django.http import JsonResponse


import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from django.http import JsonResponse
from .models import Order

from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


@api_view(['POST'])
def create_product(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Product added successfully!", "data": serializer.data})
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def create_order(request):
    customer_id = request.data.get("customer_id")
    products = request.data.get("products")  # Expecting a list of product_id and quantity

    if not products:
        return Response({"error": "Products list is required!"}, status=400)

    orders = []
    for item in products:
        product_id = item.get("product_id")
        quantity = item.get("quantity")

        product = get_object_or_404(Product, product_id=product_id)
        order = Order(customer_id=customer_id, product_name=product.product_name, quantity=quantity)
        order.save()
        orders.append(OrderSerializer(order).data)

    return Response({"message": "Order placed successfully!", "orders": orders})
@api_view(['GET'])
def get_orders(request, customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

def get_orders(request):
    orders = list(Order.objects.values())
    return JsonResponse(orders, safe=False)




def customer_segmentation(request):
    orders = Order.objects.all().values()
    df = pd.DataFrame(orders)

    if df.empty:
        return JsonResponse({"message": "No orders found"}, status=400)

    # Aggregate total quantity of products per customer
    customer_data = df.groupby('customer_id')['quantity'].sum().reset_index()

    # Apply K-Means clustering
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    customer_data['cluster'] = kmeans.fit_predict(customer_data[['quantity']])

    # Convert to dictionary
    result = customer_data.to_dict(orient="records")

    return JsonResponse({"customer_segments": result}, safe=False)



def product_recommendations(request):
    orders = Order.objects.all().values()
    df = pd.DataFrame(orders)

    if df.empty:
        return JsonResponse({"message": "No orders found"}, status=400)

    # Convert orders into transaction format (list of purchased products per customer)
    transactions = df.groupby("customer_id")["product_name"].apply(list).tolist()

    # Encode data
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

    # Apply Apriori algorithm
    frequent_itemsets = apriori(df_encoded, min_support=0.1, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)

    recommendations = rules[['antecedents', 'consequents', 'support', 'confidence']].to_dict(orient="records")

    return JsonResponse({"recommendations": recommendations}, safe=False)


def predict_previous_orders(request):
    customer_id = request.GET.get("customer_id")
    if not customer_id:
        return JsonResponse({"error": "customer_id is required"}, status=400)

    # Get past orders of the customer
    past_orders = Order.objects.filter(customer_id=customer_id).values("product_name").distinct()
    past_products = [order["product_name"] for order in past_orders]

    return JsonResponse({"previously_ordered_products": past_products}, safe=False)

def suggest_remaining_products(request):
    customer_id = request.GET.get("customer_id")
    product_name = request.GET.get("product_name")

    if not customer_id or not product_name:
        return JsonResponse({"error": "customer_id and product_name are required"}, status=400)

    # Get all past orders of the customer
    past_orders = Order.objects.filter(customer_id=customer_id).values("product_name").distinct()
    past_products = [order["product_name"] for order in past_orders]

    # Suggest remaining products except the current one
    suggested_products = [p for p in past_products if p != product_name]

    return JsonResponse({"suggested_products": suggested_products}, safe=False)

