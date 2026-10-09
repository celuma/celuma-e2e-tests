import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, context=""):
    try:
        data = response.json()
    except:
        data = response.text
    print(f"[{response.status_code}] {context}: {json.dumps(data, indent=2) if isinstance(data, dict) else data}")
    return response

def main():
    # 1. Unified Registration
    print("\n--- 1. Unified Registration ---")
    unique_suffix = str(uuid.uuid4())[:8]
    register_payload = {
        "tenant": {
            "name": f"Test Tenant {unique_suffix}",
            "legal_name": f"Test Tenant Legal {unique_suffix}",
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
            "email": f"admin-{unique_suffix}@test.com",
            "username": f"admin-{unique_suffix}",
            "password": "SecurePass123!",
            "full_name": "Admin User"
        }
    }
    
    resp = requests.post(f"{BASE_URL}/auth/register/unified", json=register_payload)
    if resp.status_code != 200:
        print_response(resp, "Registration Failed")
        return

    reg_data = resp.json()
    print_response(resp, "Registration Success")
    tenant_id = reg_data["tenant_id"]
    branch_id = reg_data["branch_id"]
    user_id = reg_data["user_id"]

    # 2. Login
    print("\n--- 2. Login ---")
    login_payload = {
        "username_or_email": register_payload["admin_user"]["username"],
        "password": register_payload["admin_user"]["password"]
    }
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if resp.status_code != 200:
        print_response(resp, "Login Failed")
        return
    
    token_data = resp.json()
    print_response(resp, "Login Success")
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Patient (needed for order)
    print("\n--- 3. Create Patient ---")
    patient_payload = {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "patient_code": f"P-{unique_suffix}",
        "first_name": "Test",
        "last_name": "Patient",
        "dob": "1990-01-01",
        "sex": "M",
        "phone": "555-0000",
        "email": f"patient-{unique_suffix}@test.com"
    }
    resp = requests.post(f"{BASE_URL}/patients/", json=patient_payload, headers=headers)
    print_response(resp, "Create Patient")
    if resp.status_code != 200: return
    patient_id = resp.json()["id"]

    # 4. Create Service Catalog Item
    print("\n--- 4. Create Service Catalog Item ---")
    service_payload = {
        "service_name": "Test Analysis",
        "service_code": f"SRV-{unique_suffix}",
        "description": "Test Service Description",
        "price": 1000.00,
        "currency": "MXN",
        "is_active": True,
        "valid_from": datetime.utcnow().isoformat()
    }
    resp = requests.post(f"{BASE_URL}/billing/catalog", json=service_payload, headers=headers)
    print_response(resp, "Create Service")
    service_id = resp.json().get("id") if resp.status_code == 200 else None

    # 5. List Catalog
    print("\n--- 5. List Catalog ---")
    resp = requests.get(f"{BASE_URL}/billing/catalog", headers=headers)
    print_response(resp, "List Catalog")

    # 6. Unified Order Creation
    print("\n--- 6. Unified Order Creation ---")
    order_payload = {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "patient_id": patient_id,
        "order_code": f"ORD-{unique_suffix}",
        "requested_by": "Dr. Test",
        "notes": "Test Order Notes",
        "created_by": user_id,
        "samples": [
            {
                "sample_code": f"SMP1-{unique_suffix}",
                "type": "SANGRE",
                "notes": "Sample 1",
                "collected_at": datetime.utcnow().isoformat(),
                "received_at": datetime.utcnow().isoformat()
            }
        ]
    }
    resp = requests.post(f"{BASE_URL}/laboratory/orders/unified", json=order_payload, headers=headers)
    print_response(resp, "Unified Order Creation")
    if resp.status_code != 200: return
    order_data = resp.json()
    order_id = order_data["order"]["id"]

    # 7. Create Event
    print("\n--- 7. Create Timeline Event ---")
    event_payload = {
        "event_type": "STATUS_CHANGED",
        "description": "Order processing started",
        "metadata": {"new_status": "PROCESSING"}
    }
    resp = requests.post(f"{BASE_URL}/laboratory/orders/{order_id}/events", json=event_payload, headers=headers)
    print_response(resp, "Create Event")

    # 8. List Events
    print("\n--- 8. List Events ---")
    resp = requests.get(f"{BASE_URL}/laboratory/orders/{order_id}/events", headers=headers)
    print_response(resp, "List Events")

    # 9. Create Invoice
    print("\n--- 9. Create Invoice ---")
    invoice_payload = {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "order_id": order_id,
        "invoice_number": f"INV-{unique_suffix}",
        "amount_total": 1000.00,
        "currency": "MXN",
        "issued_at": datetime.utcnow().isoformat()
    }
    resp = requests.post(f"{BASE_URL}/billing/invoices/", json=invoice_payload, headers=headers)
    print_response(resp, "Create Invoice")
    if resp.status_code == 200:
        invoice_id = resp.json()["id"]
        # Add item to invoice if service exists
        if service_id:
            item_payload = {
                "service_id": service_id,
                "description": "Test Analysis Item",
                "quantity": 1,
                "unit_price": 1000.00
            }
            requests.post(f"{BASE_URL}/billing/invoices/{invoice_id}/items", json=item_payload, headers=headers)
            
        # Get full invoice
        resp = requests.get(f"{BASE_URL}/billing/invoices/{invoice_id}/full", headers=headers)
        print_response(resp, "Get Full Invoice")

    # 10. Create Report
    print("\n--- 10. Create Report ---")
    report_payload = {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "order_id": order_id,
        "title": "Test Report",
        "diagnosis_text": "Normal",
        "created_by": user_id,
        "report": {"test_field": "test_value"}
    }
    resp = requests.post(f"{BASE_URL}/reports/", json=report_payload, headers=headers)
    print_response(resp, "Create Report")
    if resp.status_code == 200:
        report_id = resp.json()["id"]
        
        # Submit Report
        print("\n--- 11. Submit Report ---")
        submit_payload = {"changelog": "Submitting for review"}
        resp = requests.post(f"{BASE_URL}/reports/{report_id}/submit", json=submit_payload, headers=headers)
        print_response(resp, "Submit Report")

    # 11. Dashboard
    print("\n--- 12. Dashboard Stats ---")
    resp = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    print_response(resp, "Dashboard Stats")

if __name__ == "__main__":
    main()

