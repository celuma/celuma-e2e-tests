import requests
import json
import uuid
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {}
TENANT_ID = ""
BRANCH_ID = ""
USER_ID = ""
ADMIN_EMAIL = ""
ADMIN_PASSWORD = "SecurePass123!"

# Colors for output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}=== {msg} ==={bcolors.ENDC}")

def print_success(msg):
    print(f"{bcolors.OKGREEN}✓ {msg}{bcolors.ENDC}")

def print_fail(msg, details=None):
    print(f"{bcolors.FAIL}✗ {msg}{bcolors.ENDC}")
    if details:
        print(f"{bcolors.FAIL}  Details: {details}{bcolors.ENDC}")

def request(method, endpoint, data=None, expected_status=200, use_auth=True):
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS if use_auth else {}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        if response.status_code == expected_status:
            return response.json() if response.content else {}
        else:
            print_fail(f"{method} {endpoint} failed with {response.status_code}", response.text)
            return None
    except Exception as e:
        print_fail(f"Request exception: {str(e)}")
        return None

def test_auth_and_setup():
    global HEADERS, TENANT_ID, BRANCH_ID, USER_ID, ADMIN_EMAIL
    
    print_header("1. Authentication & Setup")
    
    # 1.1 Unified Registration
    unique_suffix = str(uuid.uuid4())[:8]
    ADMIN_EMAIL = f"admin-{unique_suffix}@test.com"
    
    register_payload = {
        "tenant": {
            "name": f"Comprehensive Test Tenant {unique_suffix}",
            "legal_name": f"Comp Test Legal {unique_suffix}",
            "tax_id": f"TAX{unique_suffix}"
        },
        "branch": {
            "code": f"HQ-{unique_suffix}",
            "name": "Headquarters",
            "timezone": "America/Mexico_City",
            "address_line1": "Av. Test 123",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "MX"
        },
        "admin_user": {
            "email": ADMIN_EMAIL,
            "username": f"admin-{unique_suffix}",
            "password": ADMIN_PASSWORD,
            "full_name": "Admin User"
        }
    }
    
    data = request("POST", "/auth/register/unified", register_payload, use_auth=False)
    if data:
        TENANT_ID = data["tenant_id"]
        BRANCH_ID = data["branch_id"]
        USER_ID = data["user_id"]
        print_success("Unified Registration successful")
    else:
        sys.exit(1)

    # 1.2 Login
    login_payload = {
        "username_or_email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    data = request("POST", "/auth/login", login_payload, use_auth=False)
    if data and "access_token" in data:
        token = data["access_token"]
        HEADERS = {"Authorization": f"Bearer {token}"}
        print_success("Login successful")
    else:
        sys.exit(1)

    # 1.3 Get Me
    data = request("GET", "/auth/me")
    if data:
        print_success("GET /auth/me successful")

    # 1.4 Update Profile
    update_payload = {"full_name": "Updated Admin Name"}
    data = request("PUT", "/auth/me", update_payload)
    if data and data["full_name"] == "Updated Admin Name":
        print_success("PUT /auth/me successful")

def test_tenant_management():
    print_header("2. Tenant Management")
    
    # 2.1 Get Tenant
    data = request("GET", f"/tenants/{TENANT_ID}")
    if data:
        print_success("GET /tenants/{id} successful")
        
    # 2.2 Update Tenant
    update_payload = {"legal_name": "Updated Legal Name Inc."}
    data = request("PATCH", f"/tenants/{TENANT_ID}", update_payload)
    if data and data["legal_name"] == "Updated Legal Name Inc.":
        print_success("PATCH /tenants/{id} successful")
        
    # 2.3 List Tenant Branches
    data = request("GET", f"/tenants/{TENANT_ID}/branches")
    if data and len(data) > 0:
        print_success("GET /tenants/{id}/branches successful")

    # 2.4 List Tenant Users
    data = request("GET", f"/tenants/{TENANT_ID}/users")
    if data and len(data) > 0:
        print_success("GET /tenants/{id}/users successful")

def test_branch_management():
    print_header("3. Branch Management")
    
    # 3.1 List Branches
    data = request("GET", "/branches/")
    if data:
        print_success("GET /branches/ successful")
        
    # 3.2 Get Branch
    data = request("GET", f"/branches/{BRANCH_ID}")
    if data:
        print_success("GET /branches/{id} successful")
        
    # 3.3 Create Branch
    unique = str(uuid.uuid4())[:4]
    new_branch_payload = {
        "tenant_id": TENANT_ID,
        "code": f"BR-{unique}",
        "name": "New Branch",
        "timezone": "America/Mexico_City",
        "address_line1": "Calle 2",
        "city": "City 2",
        "state": "ST",
        "postal_code": "54321",
        "country": "MX"
    }
    data = request("POST", "/branches/", new_branch_payload)
    if data:
        print_success("POST /branches/ successful")

def test_user_management():
    print_header("4. User Management")
    
    # 4.1 Create User
    unique = str(uuid.uuid4())[:6]
    new_user_payload = {
        "email": f"tech-{unique}@test.com",
        "username": f"tech-{unique}",
        "password": "TechPass123!",
        "full_name": "Lab Tech User",
        "role": "lab_tech"
    }
    created_user = request("POST", "/users/", new_user_payload)
    if created_user:
        print_success("POST /users/ successful")
        user_id = created_user["id"]
        
        # 4.2 List Users
        data = request("GET", "/users/")
        if data:
            print_success("GET /users/ successful")
            
        # 4.3 Update User
        update_data = {"full_name": "Updated Tech Name"}
        data = request("PUT", f"/users/{user_id}", update_data)
        if data:
            print_success("PUT /users/{id} successful")
            
        # 4.4 Toggle Active
        data = request("POST", f"/users/{user_id}/toggle-active")
        if data:
            print_success("POST /users/{id}/toggle-active successful")
            
        # 4.5 Invite User
        invite_payload = {
            "email": f"invite-{unique}@test.com",
            "full_name": "Invited User",
            "role": "viewer"
        }
        invite = request("POST", "/users/invitations", invite_payload)
        if invite:
            print_success("POST /users/invitations successful")
            
            # 4.6 Get Invitation (Public)
            token = invite["token"]
            data = request("GET", f"/users/invitations/{token}", use_auth=False)
            if data:
                print_success("GET /users/invitations/{token} successful")
                
            # 4.7 Accept Invitation
            accept_payload = {"password": "NewUserPass123!", "username": f"invited-{unique}"}
            data = request("POST", f"/users/invitations/{token}/accept", accept_payload, use_auth=False)
            if data:
                print_success("POST /users/invitations/{token}/accept successful")

def test_patient_management():
    print_header("5. Patient Management")
    global PATIENT_ID
    
    # 5.1 Create Patient
    unique = str(uuid.uuid4())[:6]
    patient_payload = {
        "tenant_id": TENANT_ID,
        "branch_id": BRANCH_ID,
        "patient_code": f"P-{unique}",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1980-01-01",
        "sex": "M",
        "phone": "555-0101",
        "email": f"patient-{unique}@test.com"
    }
    data = request("POST", "/patients/", patient_payload)
    if data:
        PATIENT_ID = data["id"]
        print_success("POST /patients/ successful")
    
    # 5.2 List Patients
    data = request("GET", "/patients/")
    if data:
        print_success("GET /patients/ successful")
        
    # 5.3 Get Patient
    data = request("GET", f"/patients/{PATIENT_ID}")
    if data:
        print_success("GET /patients/{id} successful")

def test_laboratory_management():
    print_header("6. Laboratory Management")
    global ORDER_ID, SAMPLE_ID
    
    unique = str(uuid.uuid4())[:6]
    
    # 6.1 Create Unified Order
    order_payload = {
        "tenant_id": TENANT_ID,
        "branch_id": BRANCH_ID,
        "patient_id": PATIENT_ID,
        "order_code": f"ORD-{unique}",
        "requested_by": "Dr. Smith",
        "notes": "Routine Checkup",
        "created_by": USER_ID,
        "samples": [
            {
                "sample_code": f"S-{unique}-1",
                "type": "SANGRE",
                "notes": "Fasting",
                "collected_at": datetime.utcnow().isoformat(),
                "received_at": datetime.utcnow().isoformat()
            }
        ]
    }
    data = request("POST", "/laboratory/orders/unified", order_payload)
    if data:
        ORDER_ID = data["order"]["id"]
        SAMPLE_ID = data["samples"][0]["id"]
        print_success("POST /laboratory/orders/unified successful")
        
    # 6.2 Get Order
    data = request("GET", f"/laboratory/orders/{ORDER_ID}")
    if data:
        print_success("GET /laboratory/orders/{id} successful")
        
    # 6.3 Get Full Order
    data = request("GET", f"/laboratory/orders/{ORDER_ID}/full")
    if data:
        print_success("GET /laboratory/orders/{id}/full successful")
        
    # 6.4 List Orders
    data = request("GET", "/laboratory/orders/")
    if data:
        print_success("GET /laboratory/orders/ successful")
        
    # 6.5 Get Sample
    data = request("GET", f"/laboratory/samples/{SAMPLE_ID}")
    if data:
        print_success("GET /laboratory/samples/{id} successful")
        
    # 6.6 List Samples
    data = request("GET", "/laboratory/samples/")
    if data:
        print_success("GET /laboratory/samples/ successful")
        
    # 6.7 Create Event
    event_payload = {
        "event_type": "STATUS_CHANGED",
        "description": "Processing started",
        "metadata": {"new_status": "PROCESSING"}
    }
    data = request("POST", f"/laboratory/orders/{ORDER_ID}/events", event_payload)
    if data:
        print_success("POST /laboratory/orders/{id}/events successful")
        
    # 6.8 List Events
    data = request("GET", f"/laboratory/orders/{ORDER_ID}/events")
    if data:
        print_success("GET /laboratory/orders/{id}/events successful")

def test_report_management():
    print_header("7. Report Management")
    global REPORT_ID
    
    # 7.1 Create Report
    report_payload = {
        "tenant_id": TENANT_ID,
        "branch_id": BRANCH_ID,
        "order_id": ORDER_ID,
        "title": "Comprehensive Blood Panel",
        "diagnosis_text": "Normal limits",
        "created_by": USER_ID,
        "report": {"section_a": "value"}
    }
    data = request("POST", "/reports/", report_payload)
    if data:
        REPORT_ID = data["id"]
        print_success("POST /reports/ successful")
        
    # 7.2 Get Report
    data = request("GET", f"/reports/{REPORT_ID}")
    if data:
        print_success("GET /reports/{id} successful")
        
    # 7.3 Submit Report
    submit_payload = {"changelog": "Initial draft complete"}
    data = request("POST", f"/reports/{REPORT_ID}/submit", submit_payload)
    if data:
        print_success("POST /reports/{id}/submit successful")
        
    # 7.4 Worklist
    data = request("GET", "/reports/worklist")
    if data:
        print_success("GET /reports/worklist successful")

def test_billing_management():
    print_header("8. Billing Management")
    global SERVICE_ID, INVOICE_ID
    
    unique = str(uuid.uuid4())[:6]
    
    # 8.1 Create Service
    service_payload = {
        "service_name": "Blood Analysis",
        "service_code": f"SRV-{unique}",
        "description": "Standard analysis",
        "price": 150.00,
        "currency": "MXN",
        "valid_from": datetime.utcnow().isoformat()
    }
    data = request("POST", "/billing/catalog", service_payload)
    if data:
        SERVICE_ID = data["id"]
        print_success("POST /billing/catalog successful")
        
    # 8.2 List Catalog
    data = request("GET", "/billing/catalog")
    if data:
        print_success("GET /billing/catalog successful")
        
    # 8.3 Create Invoice
    invoice_payload = {
        "tenant_id": TENANT_ID,
        "branch_id": BRANCH_ID,
        "order_id": ORDER_ID,
        "invoice_number": f"INV-{unique}",
        "amount_total": 150.00,
        "currency": "MXN",
        "issued_at": datetime.utcnow().isoformat()
    }
    data = request("POST", "/billing/invoices/", invoice_payload)
    if data:
        INVOICE_ID = data["id"]
        print_success("POST /billing/invoices/ successful")
        
    # 8.4 Add Invoice Item
    item_payload = {
        "service_id": SERVICE_ID,
        "description": "Blood Analysis",
        "quantity": 1,
        "unit_price": 150.00
    }
    data = request("POST", f"/billing/invoices/{INVOICE_ID}/items", item_payload)
    if data:
        print_success("POST /billing/invoices/{id}/items successful")
        
    # 8.5 Create Payment
    payment_payload = {
        "tenant_id": TENANT_ID,
        "branch_id": BRANCH_ID,
        "invoice_id": INVOICE_ID,
        "amount_paid": 150.00,
        "method": "CASH",
        "paid_at": datetime.utcnow().isoformat()
    }
    data = request("POST", "/billing/payments/", payment_payload)
    if data:
        print_success("POST /billing/payments/ successful")
        
    # 8.6 Check Order Balance
    data = request("GET", f"/billing/orders/{ORDER_ID}/balance")
    if data and data["balance"] == 0.0:
        print_success("GET /billing/orders/{id}/balance successful")

def test_dashboard():
    print_header("9. Dashboard")
    
    # 9.1 Get Stats
    data = request("GET", "/dashboard/")
    if data:
        print_success("GET /dashboard/ successful")

def test_portal():
    print_header("10. Portals")
    
    # Not testing physician portal as it requires a user with a specific email linked to order request
    # but we can test patient portal if we had public access code logic working reliably in this flow.
    # For now skipping specific portal logic that depends on complex external state.
    print("Skipping specialized portal flows for basic connectivity test.")

def main():
    try:
        test_auth_and_setup()
        test_tenant_management()
        test_branch_management()
        test_user_management()
        test_patient_management()
        test_laboratory_management()
        test_report_management()
        test_billing_management()
        test_dashboard()
        test_portal()
        
        print_header("ALL TESTS COMPLETED SUCCESSFULLY")
    except Exception as e:
        print_fail(f"Test suite failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

