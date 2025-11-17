import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from pymongo import MongoClient
from bson import ObjectId
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
# --------------------- MONGO CONNECTION ---------------------
client = MongoClient(settings.MONGO_URI)
db = client['waste_management_system']


# --------------------- USER VIEWS ---------------------

def index(request):
    """Landing page"""
    return render(request, 'user/homepage.html')


def get_signup_page(request):
    return render(request, 'user/signup.html')


@csrf_exempt
def signup_process(request):
    """Handle user signup"""
    if request.method != 'POST':
        return HttpResponse('Only POST method allowed.')

    number = request.POST.get('number')
    email = request.POST.get('email')
    password = request.POST.get('password')

    if not all([number, email, password]):
        return HttpResponse('⚠️ All fields are required.')

    # Check if email or number already exists
    users = db.users
    if users.find_one({'$or': [{'number': number}, {'email': email}]}):
        return HttpResponse('❌ Number or Email already registered.')

    users.insert_one({
        'number': number,
        'email': email,
        'password': password,  # (⚠️ Use hashed password in production)
        'created_at': datetime.utcnow().isoformat()
    })

    return HttpResponse('✅ Signup successful! Please log in.')


def get_login_page(request):
    return render(request, 'user/login.html')


@csrf_exempt
def login_process(request):
    """User login"""
    if request.method != 'POST':
        return HttpResponse('Only POST method allowed.')

    email = request.POST.get('email')
    password = request.POST.get('password')

    print("DEBUG LOGIN INPUT:", email, password)

    user = db.users.find_one({'email': email, 'password': password})
    print("DEBUG USER FOUND:", user)

    if user:
        request.session['user_id'] = str(user['_id'])
        request.session['role'] = 'user'
        return redirect('/home/')

    return HttpResponse('❌ Invalid credentials. Please try again.')

def get_user_dashboard(request):
    """User dashboard"""
    if not request.session.get('user_id'):
        return redirect('/login/')

    user_id = request.session['user_id']
    user = db.users.find_one({'_id': ObjectId(user_id)})

    # Collect request stats for the dashboard
    total_requests = db.requests.count_documents({'userId': user_id})
    total_pending = db.requests.count_documents({'userId': user_id, 'status': 'pending'})
    total_resolved = db.requests.count_documents({'userId': user_id, 'status': 'resolved'})
    total_unassigned = db.requests.count_documents({'userId': user_id, 'assignedDriverId': None})

    total_pickup = db.requests.count_documents({'userId': user_id, 'request_type': 'Pickup'})
    total_complaint = db.requests.count_documents({'userId': user_id, 'request_type': 'Complaint'})
    total_recycling = db.requests.count_documents({'userId': user_id, 'request_type': 'Recycling'})
    total_other = db.requests.count_documents({'userId': user_id, 'request_type': 'Other'})

    result = {
        'total_requests': total_requests,
        'total_pending': total_pending,
        'total_resolved': total_resolved,
        'total_unassigned_driver_requests': total_unassigned,
        'total_pickup_request': total_pickup,
        'total_complaint_request': total_complaint,
        'total_recycling_request': total_recycling,
        'total_other_request': total_other
    }

    return render(request, 'user/userDashboard.html', {'user': user, 'result': result})


def logout_user(request):
    """Logout user"""
    request.session.flush()
    return redirect('/')


def get_raise_request_page(request):
    """Display form to raise a new request"""
    if not request.session.get('user_id'):
        return redirect('/login/')
    return render(request, 'user/request.html')


@csrf_exempt
def submit_request(request):
    """Submit a new waste collection request"""
    if request.method != 'POST':
        return HttpResponse('Only POST method allowed.')

    if not request.session.get('user_id'):
        return redirect('/login/')

    user_id = request.session['user_id']

    data = {
        'userId': user_id,
        'address': request.POST.get('address'),
        'request_type': request.POST.get('request_type'),
        'message': request.POST.get('message'),
        'status': 'pending',
        'assignedDriverId': None,
        'driverName': None,
        'time_stamp': datetime.utcnow().isoformat()
    }

    db.requests.insert_one(data)
    return HttpResponse('✅ Request submitted successfully!')


def get_my_requests(request):
    """User: View my requests"""
    if not request.session.get('user_id'):
        return redirect('/login/')

    reqs = list(db.requests.find({'userId': request.session['user_id']}))
    return render(request, 'user/my-requests.html', {'requests': reqs})


# --------------------- ADMIN VIEWS ---------------------

def admin_root(request):
    """Redirect /admin to login"""
    return redirect('/admin/login/')


def admin_login_page(request):
    """Admin login page"""
    if request.session.get('is_admin'):
        return redirect('/admin/dashboard/')
    return render(request, 'admin/adminLogin.html')


@csrf_exempt
def admin_login_process(request):
    """Admin login"""
    if request.method != 'POST':
        return HttpResponse('Only POST method allowed.')

    email = request.POST.get('email')
    password = request.POST.get('password')
    admin = db.admins.find_one({'email': email, 'password': password})

    if admin:
        request.session['is_admin'] = True
        return redirect('/admin/dashboard/')

    return HttpResponse('❌ Invalid admin credentials.')


def admin_dashboard(request):
    """Admin dashboard"""
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')
    return render(request, 'admin/adminDashboard.html')

def admin_all_requests(request):
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')

    # fetch requests and drivers from mongodb and normalize fields used in templates
    raw_reqs = list(db.requests.find({}))
    reqs = []
    for r in raw_reqs:
        reqs.append({
            'id': str(r.get('_id')),
            'name': r.get('name', ''),
            'email': r.get('email', ''),
            'address': r.get('address', ''),
            # allow either time_stamp or time field
            'time': r.get('time') or r.get('time_stamp') or '',
            'request_type': r.get('request_type', ''),
            'status': r.get('status', ''),
            # driverName is set when assigned
            'assigned_driver': r.get('driverName') or (r.get('assignedDriverId') and r.get('assignedDriverId')) or None,
            'message': r.get('message', '')
        })

    # prepare drivers list with string ids (so template option values are not empty)
    raw_drivers = list(db.drivers.find({}))
    drivers = []
    for d in raw_drivers:
        drivers.append({
            'id': str(d.get('_id')),
            'name': d.get('name', ''),
            'email': d.get('email', ''),
            'phone': d.get('number') or d.get('phone') or '',
            'license': d.get('license', ''),
            'vehicle': d.get('vehicle', ''),
            'vehicle_type': d.get('vehicleType', '') or d.get('vehicle_type', '')
        })

    return render(request, 'admin/all-requests.html', {'requests': reqs, 'drivers': drivers})


@csrf_exempt
def assign_driver(request):
    """
    Accepts:
      - HTML form POST (request_id, driver_id)
      - JSON POST { requestId / request_id, driverId / driver_id }
      - GET fallback (for convenience)
    Returns: JsonResponse({'isOK': bool, 'msg': str, 'driverName': str})
    """
    if not request.session.get('is_admin'):
        return JsonResponse({'msg': 'Not authorized', 'isOK': False}, status=403)

    request_id = None
    driver_id = None

    # 1) form POST data (common when you submit a normal form)
    if request.method == 'POST' and request.POST:
        request_id = request.POST.get('request_id')
        driver_id = request.POST.get('driver_id')

    # 2) JSON body (fetch)
    if not request_id or not driver_id:
        try:
            data = json.loads(request.body.decode() or "{}")
            request_id = request_id or data.get('requestId') or data.get('request_id')
            driver_id = driver_id or data.get('driverId') or data.get('driver_id')
        except Exception:
            pass

    # 3) GET fallback (not preferred)
    if not request_id:
        request_id = request.GET.get('requestId') or request.GET.get('request_id')
    if not driver_id:
        driver_id = request.GET.get('driverId') or request.GET.get('driver_id')

    if not request_id or not driver_id:
        return JsonResponse({'msg': 'Missing parameters', 'isOK': False})

    # validate ObjectId formats where applicable
    try:
        # driver lookup: driver's _id is an ObjectId
        if ObjectId.is_valid(driver_id):
            driver_obj = db.drivers.find_one({'_id': ObjectId(driver_id)})
        else:
            driver_obj = db.drivers.find_one({'_id': driver_id}) or db.drivers.find_one({'number': driver_id})
    except Exception:
        driver_obj = None

    if not driver_obj:
        return JsonResponse({'msg': 'Driver not found', 'isOK': False})

    # update request in DB
    try:
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {
                'assignedDriverId': driver_id,
                'driverName': driver_obj.get('name', ''),
                'status': 'assigned'
            }}
        )
    except Exception as e:
        return JsonResponse({'msg': 'Failed to update request: ' + str(e), 'isOK': False})

    return JsonResponse({'msg': 'Driver assigned successfully', 'isOK': True, 'driverName': driver_obj.get('name', '')})

def unassign_driver(request):
    if not request.session.get('is_admin'):
        return JsonResponse({'isOK': False, 'msg': 'Not authorized'}, status=403)

    req_id = request.GET.get('requestId') or request.GET.get('request_id')
    if not req_id:
        return JsonResponse({"isOK": False, "msg": "Missing requestId"})

    try:
        db.requests.update_one(
            {'_id': ObjectId(req_id)},
            {'$set': {'assignedDriverId': None, 'driverName': None, 'status': 'pending'}}
        )
    except Exception as e:
        return JsonResponse({"isOK": False, "msg": "Failed: " + str(e)})

    return JsonResponse({"isOK": True, "msg": "Driver unassigned successfully"})

def reject_request(request):
    if not request.session.get('is_admin'):
        return JsonResponse({'isOK': False, 'msg': 'Not authorized'}, status=403)

    request_id = request.GET.get("requestId") or request.GET.get("request_id")
    if not request_id:
        return JsonResponse({"isOK": False, "msg": "Missing requestId"})

    try:
        db.requests.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': {'status': 'rejected'}}
        )
    except Exception as e:
        return JsonResponse({"isOK": False, "msg": "Failed: " + str(e)})

    return JsonResponse({"isOK": True, "msg": "Request rejected successfully"})



def admin_create_driver_page(request):
    """Render driver creation page"""
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')
    return render(request, 'admin/create-driver.html')

def admin_create_driver(request):
    """
    Handles adding a new driver.
    - If request is AJAX/XHR -> returns JsonResponse with {isOK, msg, errors?}
    - If regular POST -> uses Django messages and redirects (fallback)
    """
    # require admin session
    if not request.session.get('is_admin'):
        # AJAX -> JSON 403, else redirect to admin login
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'isOK': False, 'msg': 'Not authorized'}, status=403)
        return redirect('/admin/login/')

    if request.method != 'POST':
        # Render page if GET (should be handled by admin_create_driver_page view)
        return HttpResponse('Only POST method allowed.')

    # read form fields (support both name variants)
    name = request.POST.get('name', '').strip()
    phone = request.POST.get('phone', '').strip() or request.POST.get('number', '').strip()
    password = request.POST.get('password', '')
    email = request.POST.get('email', '').strip()
    license_no = request.POST.get('license', '').strip()
    vehicle = request.POST.get('vehicle', '').strip()
    vehicle_type = request.POST.get('vehicle_type', '') or request.POST.get('vehicleType', '')

    # Simple validation
    errors = {}
    if not name:
        errors['name'] = 'Driver name is required.'
    if not phone:
        errors['phone'] = 'Phone number is required.'
    if not password:
        errors['password'] = 'Password is required.'
    # (optional) check if phone/email already exists in db.drivers:
    if phone:
        if db.drivers.find_one({'number': phone}):
            errors['phone'] = 'Phone number already used by another driver.'
    if email:
        if db.drivers.find_one({'email': email}):
            errors['email'] = 'Email already used by another driver.'

    # If validation failed -> return errors
    if errors:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'isOK': False, 'msg': 'Validation failed', 'errors': errors})
        # fallback: show first error as HttpResponse (or you can set messages and redirect)
        first = list(errors.values())[0]
        messages.error(request, first)
        return redirect('/admin/create-driver/')

    # Insert driver record
    db.drivers.insert_one({
        'name': name,
        'number': phone,
        'email': email,
        'license': license_no,
        'vehicle': vehicle,
        'vehicleType': vehicle_type,
        # NOTE: plain password used here — hash for production!
        'password': password,
        'created_at': datetime.utcnow().isoformat()
    })

    # Success response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'isOK': True, 'msg': 'Driver added successfully.'})

    # Normal POST fallback: add django message and redirect back to create page
    messages.success(request, '✅ Driver added successfully.')
    return redirect('/admin/create-driver/')

def admin_all_drivers(request):
    """Admin: List all drivers"""
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')

    drivers_cursor = db.drivers.find({})
    drivers = []

    for d in drivers_cursor:
        d['id'] = str(d['_id'])  # ✅ create safe "id" field
        drivers.append(d)

    return render(request, 'admin/allDrivers.html', {'drivers': drivers})




@csrf_exempt
def admin_delete_driver(request, id):
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')

    if id:
        db.drivers.delete_one({'_id': ObjectId(id)})
        return redirect('/admin/all-drivers/')
    return HttpResponse('Driver ID missing.')


def admin_logout(request):
    """Admin logout"""
    request.session.pop('is_admin', None)
    return redirect('/admin/login/')


# --------------------- DRIVER VIEWS ---------------------

def driver_root(request):
    return redirect('/driver/login/')


def driver_login_page(request):
    """Driver login page"""
    if request.session.get('driver_id'):
        return redirect('/driver/dashboard/')
    return render(request, 'driver/driverLogin.html')


@csrf_exempt
def driver_login_process(request):
    """Driver login"""
    if request.method != 'POST':
        return HttpResponse('Only POST method allowed.')

    number = request.POST.get('number')
    password = request.POST.get('password')

    driver = db.drivers.find_one({'number': number, 'password': password})
    if driver:
        request.session['driver_id'] = str(driver['_id'])
        return redirect('/driver/dashboard/')

    return HttpResponse('❌ Invalid driver credentials.')


def driver_dashboard(request):
    """Driver dashboard"""
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')
    reqs = list(db.requests.find({'assignedDriverId': request.session['driver_id']}))
    return render(request, 'driver/driverDashboard.html', {'requests': reqs})




def driver_pending_requests(request):
    """Driver pending pickup requests"""
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')

    reqs = list(db.requests.find({'assignedDriverId': None, 'status': 'pending'}))

    # Convert MongoDB ObjectIds to string and rename "_id" to "id"
    for r in reqs:
        r['id'] = str(r['_id'])  # ✅ rename _id → id

    return render(request, 'driver/pendingRequests.html', {'requests': reqs})


def driver_resolve_request(request):
    """Driver marks request as resolved"""
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')
    req_id = request.GET.get('id')
    if req_id:
        db.requests.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'resolved', 'resolvedAt': datetime.utcnow().isoformat()}})
    return redirect('/driver/dashboard/')


def driver_reject_request(request):
    """Driver rejects request"""
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')
    req_id = request.GET.get('id')
    if req_id:
        db.requests.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'rejected'}})
    return redirect('/driver/dashboard/')


def driver_history(request):
    """Driver request history"""
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')
    reqs = list(db.requests.find({'assignedDriverId': request.session['driver_id']}))
    return render(request, 'driver/history.html', {'requests': reqs})


def driver_logout(request):
    """Driver logout"""
    request.session.flush()
    return redirect('/driver/login/')

@csrf_exempt
def contact_page(request):
    return render(request, 'common/contact.html')

def contact_submit(request):
    """
    Accepts POST request from contact form.
    - If AJAX: return JSON -> { isOK: True, msg: "..." }
    - If normal POST (no JS): redirect back with Django messages.
    """
    if request.method != 'POST':
        return HttpResponse('Only POST allowed.', status=405)

    # read form fields
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    message_text = request.POST.get('message', '').strip()

    # basic validation
    if not name or not email or not message_text:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'isOK': False, 'msg': 'All fields are required.'})
        messages.error(request, 'All fields are required.')
        return redirect('/contact/')

    # insert into mongo
    try:
        db.contacts.insert_one({
            'name': name,
            'email': email,
            'message': message_text,
            'created_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        # DB failure
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'isOK': False, 'msg': 'Server error: ' + str(e)})
        messages.error(request, 'Server error. Try again later.')
        return redirect('/contact/')

    # success
    success_msg = "Request Submitted! Your message has been successfully submitted. We'll get back soon."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'isOK': True, 'msg': success_msg})
    # fallback for non-JS: use messages & redirect back
    messages.success(request, success_msg)
    return redirect('/contact/')

@csrf_exempt
def report_bug_page(request):
    return render(request, 'common/report-bug.html')

@csrf_exempt
def report_bug_submit(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        issue = request.POST.get('issue')
        db.bugs.insert_one({
            'name': name,
            'email': email,
            'issue': issue,
            'created_at': datetime.utcnow().isoformat()
        })
        return HttpResponse('🐞 Bug reported successfully! Thank you for helping us improve.')
    return HttpResponse('Only POST method allowed.')


def admin_dashboard(request):
    """Admin dashboard with full statistics"""
    if not request.session.get('is_admin'):
        return redirect('/admin/login/')

    # -------- REQUEST STATS --------
    total_requests = db.requests.count_documents({})

    total_pending = db.requests.count_documents({'status': 'pending'})
    total_resolved = db.requests.count_documents({'status': 'resolved'})
    total_unassigned = db.requests.count_documents({'assignedDriverId': None})

    # -------- REQUEST TYPE STATS --------
    total_pickup = db.requests.count_documents({'request_type': 'Pickup'})
    total_complaint = db.requests.count_documents({'request_type': 'Complaint'})
    total_recycling = db.requests.count_documents({'request_type': 'Recycling'})
    total_other = db.requests.count_documents({'request_type': 'Other'})

    # -------- USER & DRIVER STATS --------
    total_users = db.users.count_documents({})
    total_drivers = db.drivers.count_documents({})

    # -------- VEHICLE STATS --------
    total_trucks = db.drivers.count_documents({'vehicleType': {'$regex': 'truck', '$options': 'i'}})
    total_cars = db.drivers.count_documents({'vehicleType': {'$regex': 'car', '$options': 'i'}})
    total_vans = db.drivers.count_documents({'vehicleType': {'$regex': 'van', '$options': 'i'}})
    total_motorcycles = db.drivers.count_documents({'vehicleType': {'$regex': 'motorcycle', '$options': 'i'}})

    # -------- BUILD RESULT DICTIONARY --------
    result = {
        'total_requests': total_requests,
        'total_pending': total_pending,
        'total_resolved': total_resolved,
        'total_unassigned_driver_requests': total_unassigned,

        'total_pickup_request': total_pickup,
        'total_complaint_request': total_complaint,
        'total_recycling_request': total_recycling,
        'total_other_request': total_other,

        'total_users': total_users,
        'total_drivers': total_drivers,

        'total_trucks': total_trucks,
        'total_cars': total_cars,
        'total_van': total_vans,
        'total_motorcycle': total_motorcycles,
    }

    return render(request, 'admin/adminDashboard.html', {'result': result})

def driver_dashboard(request):
    """
    Driver dashboard - assigned requests + stats for that driver.
    This builds the `result` dict keys used by your driverDashboard.html template.
    """
    if not request.session.get('driver_id'):
        return redirect('/driver/login/')

    driver_id = request.session.get('driver_id')

    # -- Requests assigned to this driver (for list display) --
    assigned_reqs_cursor = db.requests.find({'assignedDriverId': driver_id})
    assigned_reqs = []
    for r in assigned_reqs_cursor:
        # convert _id to safe id string for template use
        r['id'] = str(r.get('_id'))
        assigned_reqs.append(r)

    # -- Stats for this driver (counts) --
    # total requests assigned to this driver
    total_requests = db.requests.count_documents({'assignedDriverId': driver_id})

    # status counts for this driver
    total_pending = db.requests.count_documents({'assignedDriverId': driver_id, 'status': 'pending'})
    total_resolved = db.requests.count_documents({'assignedDriverId': driver_id, 'status': 'resolved'})
    total_rejected = db.requests.count_documents({'assignedDriverId': driver_id, 'status': 'rejected'})

    # request type counts for this driver
    total_pickup = db.requests.count_documents({'assignedDriverId': driver_id, 'request_type': 'Pickup'})
    total_complaint = db.requests.count_documents({'assignedDriverId': driver_id, 'request_type': 'Complaint'})
    total_recycling = db.requests.count_documents({'assignedDriverId': driver_id, 'request_type': 'Recycling'})
    total_other = db.requests.count_documents({'assignedDriverId': driver_id, 'request_type': 'Other'})

    result = {
        'total_requests': total_requests,
        'total_pending': total_pending,
        'total_resolved': total_resolved,
        'total_rejected': total_rejected,
        'total_pickup_request': total_pickup,
        'total_complaint_request': total_complaint,
        'total_recycling_request': total_recycling,
        'total_other_request': total_other,
    }

    # optional debug (uncomment while testing)
    # print("Driver dashboard debug -> driver_id:", driver_id, "result:", result)

    return render(request, 'driver/driverDashboard.html', {
        'requests': assigned_reqs,
        'result': result,
        'driver_id': driver_id,
    })
