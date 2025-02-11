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





def customer_segmentation():
    # Fetch order data from database
    orders = Order.objects.all()
    data = {}

    # Create a dictionary where keys are customers and values are purchased products
    for order in orders:
        if order.customer_id not in data:
            data[order.customer_id] = []
        data[order.customer_id].append(order.product_name)

    # Convert data into a DataFrame
    df = pd.DataFrame(list(data.items()), columns=['CustomerID', 'Products'])
    df['Products'] = df['Products'].apply(lambda x: ', '.join(x))

    # Define customer segments based on common product groups
    segment_map = {
        'Laptop Buyers': ['Laptop', 'Laptop charger', 'Wired headphone'],
        'Smartphone Lovers': ['Smartphone', 'Phone charger', 'Wired headphone'],
       
    }

    # Assign customers to segments
    def assign_segment(products):
        for segment, items in segment_map.items():
            if any(item in products for item in items):
                return segment
        return 'Other'

    df['Segment'] = df['Products'].apply(assign_segment)

    return df.to_dict(orient="records")

def segment_customers(request):
    result = customer_segmentation()
    return JsonResponse(result, safe=False)



def generate_product_recommendations():
    # Fetch order data
    orders = Order.objects.all()
    transactions = {}

    for order in orders:
        if order.customer_id not in transactions:
            transactions[order.customer_id] = []
        transactions[order.customer_id].append(order.product_name)

    # Convert to DataFrame
    transaction_list = list(transactions.values())
    te = TransactionEncoder()
    te_ary = te.fit(transaction_list).transform(transaction_list)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    # Apply Apriori algorithm
    frequent_itemsets = apriori(df, min_support=0.5, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)

    recommendations = {}
    for _, row in rules.iterrows():
        recommendations[row['antecedents']] = {
            "recommend": list(row['consequents']),
            "confidence": row['confidence']
        }

    return recommendations

def recommend_products(request):
    recommendations = generate_product_recommendations()  # Your recommendation logic

    if isinstance(recommendations, dict):
        recommendations = {str(key): value for key, value in recommendations.items()}  # Convert frozenset keys to strings

    return JsonResponse({'recommendations': recommendations}, safe=False)


def get_personalized_recommendation(customer_id):
    orders = Order.objects.filter(customer_id=customer_id)
    purchased_products = [order.product_name for order in orders]

    recommendations = generate_product_recommendations()
    suggested_products = []

    for product in purchased_products:
        product_tuple = (product,)
        if product_tuple in recommendations:
            suggested_products.append(recommendations[product_tuple]['recommend'][0])

    return suggested_products

def personalized_dashboard(request, customer_id):
    recommended_products = get_personalized_recommendation(customer_id)
    
    return JsonResponse({
        "message": f"Recommended Products for Customer {customer_id}",
        "recommendations": recommended_products
    })
