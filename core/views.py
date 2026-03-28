from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .mongo import db 
from bson import ObjectId  # Crucial for MongoDB deletion/updates

# 1. Fetch ALL products (for Vendor)
@csrf_exempt
def get_all_market_products(request):
    try:
        products = list(db.market.find({}))
        # Convert ObjectId to string so it can be sent as JSON
        for p in products: p['_id'] = str(p['_id'])
        return JsonResponse(products, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# 2. Manage Vendor Requests (Post and Get)
@csrf_exempt
def manage_requests(request):
    if request.method == "POST":
        data = json.loads(request.body)
        db.requests.insert_one(data)
        return JsonResponse({"status": "success"})
    
    requests = list(db.requests.find({}))
    for r in requests: r['_id'] = str(r['_id'])
    return JsonResponse(requests, safe=False)

# 3. Create Order (When Farmer accepts or Vendor buys)
@csrf_exempt
def create_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        db.orders.insert_one(data)
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Method not allowed"}, status=405)

# 4. Get Farmer's specific products
@csrf_exempt
def get_my_products(request):
    farmer_name = request.GET.get('farmer')
    products = list(db.market.find({"farmer": farmer_name}))
    for p in products: 
        p['id'] = str(p['_id']) # Rename _id to id for React frontend
        del p['_id']
    return JsonResponse(products, safe=False)

# 5. Get Farmer's specific orders
@csrf_exempt
def get_farmer_orders(request):
    farmer_name = request.GET.get('farmer')
    orders = list(db.orders.find({"farmer_name": farmer_name}))
    for o in orders: 
        o['id'] = str(o['_id'])
        del o['_id']
    return JsonResponse(orders, safe=False)

# 6. Get Vendor's specific orders
@csrf_exempt
def get_vendor_orders(request):
    vendor_name = request.GET.get('vendor')
    orders = list(db.orders.find({"vendor_name": vendor_name}))
    for o in orders: 
        o['id'] = str(o['_id'])
        del o['_id']
    return JsonResponse(orders, safe=False)

# 7. Add Product (Farmer Publish)
@csrf_exempt
def add_product(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            db.market.insert_one(data) 
            return JsonResponse({"status": "success", "message": "Product published!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Only POST allowed"}, status=405)

# --- NEW LOGIC ADDED BELOW ---

# 8. Delete Product Logic
@csrf_exempt
def delete_product(request, pk):
    if request.method == "DELETE":
        try:
            # MongoDB uses _id and expects an ObjectId object
            result = db.market.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count > 0:
                return JsonResponse({"status": "success", "message": "Deleted"})
            return JsonResponse({"status": "error", "message": "Not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# 9. Update Order Status (Mark Shipped / Accept)
@csrf_exempt
def update_order_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("order_id")
            new_status = data.get("status")
            
            db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"status": new_status}}
            )
            return JsonResponse({"status": "success", "message": f"Status updated to {new_status}"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

# 10. Delete Order
@csrf_exempt
def delete_order(request, pk):
    if request.method == "DELETE":
        try:
            result = db.orders.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count > 0:
                return JsonResponse({"status": "success", "message": "Order deleted"})
            return JsonResponse({"status": "error", "message": "Order not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

# 11. Delete/Reject Vendor Request
@csrf_exempt
def delete_request(request, pk):
    if request.method == "DELETE":
        try:
            result = db.requests.delete_one({"_id": ObjectId(pk)})
            if result.deleted_count > 0:
                return JsonResponse({"status": "success", "message": "Request rejected"})
            return JsonResponse({"status": "error", "message": "Request not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)