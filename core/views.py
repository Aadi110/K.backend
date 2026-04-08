from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .mongo import db 
from bson import ObjectId  # Crucial for MongoDB deletion/updates
import hmac
import hashlib
import base64
import uuid
import os
from datetime import datetime

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

# --- eSewa Payment Integration ---

@csrf_exempt
def initiate_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount_float = float(data.get("amount", 0))
            if amount_float <= 0:
                return JsonResponse({"error": "Invalid amount"}, status=400)
                
            # eSewa requires exact string matching. "50.0" in Python but "50" in JS form causes signature failure
            amount_str = str(int(amount_float)) if amount_float.is_integer() else str(amount_float)
            
            transaction_uuid = str(uuid.uuid4())
            product_code = os.getenv("ESEWA_MERCHANT_CODE", "EPAYTEST")
            secret_key = os.getenv("ESEWA_SECRET_KEY", "8gBm/:&EnhH.1/q") 
            
            # CRITICAL: eSewa signature requires key=value format for the signed string!
            message = f"total_amount={amount_str},transaction_uuid={transaction_uuid},product_code={product_code}"
            
            signature = base64.b64encode(
                hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            return JsonResponse({
                "signature": signature,
                "signed_field_names": "total_amount,transaction_uuid,product_code",
                "transaction_uuid": transaction_uuid,
                "product_code": product_code,
                "amount": amount_str,
                "tax_amount": "0",
                "total_amount": amount_str,
                "product_delivery_charge": "0",
                "product_service_charge": "0"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Example payload expected: farmer_id, vendor_id, crop_name, amount, status
            
            transaction_data = {
                "farmer_id": data.get("farmer_id"),
                "vendor_id": data.get("vendor_id"),
                "crop_name": data.get("crop_name"),
                "amount": data.get("amount"),
                "status": data.get("status", "Completed"),
                "timestamp": datetime.now().isoformat(),
                "transaction_uuid": data.get("transaction_uuid", str(uuid.uuid4()))
            }
            db.transactions.insert_one(transaction_data)
            return JsonResponse({"status": "success", "message": "Transaction verified and saved!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_farmer_transactions(request):
    farmer_name = request.GET.get('farmer')
    if not farmer_name:
        return JsonResponse({"error": "Farmer name required"}, status=400)
        
    transactions = list(db.transactions.find({"farmer_id": farmer_name}).sort("timestamp", -1))
    for t in transactions:
        t['id'] = str(t['_id'])
        del t['_id']
    return JsonResponse(transactions, safe=False)