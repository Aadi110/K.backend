import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password

from core.mongo import user_collection


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    """
    Create a new user in MongoDB.
    Expected JSON: { fullname, email, password, role }
    """
    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        required_fields = ["fullname", "email", "password", "role"]
        if not all(field in data and data[field] for field in required_fields):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        email = data["email"].strip().lower()

        existing = user_collection.find_one({"email": email})
        if existing:
            return JsonResponse({"error": "Email already registered."}, status=400)

        user_document = {
            "fullname": data["fullname"].strip(),
            "email": email,
            "password": make_password(data["password"]),
            "role": data["role"],
        }

        user_collection.insert_one(user_document)

        return JsonResponse({"message": "Account created successfully."}, status=201)
    except Exception as e:
        # Log to console for debugging
        print("Signup error:", repr(e))
        return JsonResponse({"error": f"Unexpected error during signup: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    Authenticate user by email + password against MongoDB.
    Expected JSON: { email, password }

    Response on success:
      { "name": "<fullname>", "role": "<farmer|vendor>" }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return JsonResponse({"error": "Email and password are required."}, status=400)

    user = user_collection.find_one({"email": email})
    if not user:
        return JsonResponse({"error": "Invalid credentials."}, status=401)

    if not check_password(password, user.get("password", "")):
        return JsonResponse({"error": "Invalid credentials."}, status=401)

    return JsonResponse(
        {
            "name": user.get("fullname", ""),
            "role": user.get("role", ""),
        }
    )
