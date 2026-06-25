import database as db

def test_flow():
    print("Initializing Database...")
    db.init_db()

    print("\n1. Testing Cargo List Fetch...")
    cargo = db.get_cargo_list()
    print(f"Total cargo count: {len(cargo)}")
    for item in cargo[:2]:
        print(f"Booking: {item['booking_no']}, Client: {item['client_name']}, Status: {item['status']}")

    print("\n2. Testing Insert Cargo...")
    success = db.add_cargo("BK-TEST-999", "BL-TEST-999", "테스트화주", "부산", "동경", "TEST VESSEL", "입고완료", 10.0, 500000, 3000000)
    print(f"Add Cargo Success: {success}")

    print("\n3. Testing Duplicate Insert...")
    success_dup = db.add_cargo("BK-TEST-999", "BL-TEST-999", "테스트화주", "부산", "동경", "TEST VESSEL", "입고완료", 10.0, 500000, 3000000)
    print(f"Add Duplicate Cargo Success (Should be False): {success_dup}")

    print("\n4. Testing Update Cargo Status...")
    cargo_updated = db.get_cargo_list()
    test_item = [x for x in cargo_updated if x['booking_no'] == "BK-TEST-999"][0]
    db.update_cargo_status(test_item['id'], "출항")
    cargo_after_update = db.get_cargo_list()
    updated_item = [x for x in cargo_after_update if x['booking_no'] == "BK-TEST-999"][0]
    print(f"Updated status: {updated_item['status']}")

    print("\n5. Testing Delete Cargo...")
    db.delete_cargo(updated_item['id'])
    cargo_deleted = db.get_cargo_list()
    has_item = any(x['booking_no'] == "BK-TEST-999" for x in cargo_deleted)
    print(f"Has test item after deletion: {has_item}")

    print("\n6. Testing Posts Access control...")
    print("Admin view posts:")
    admin_posts = db.get_posts("관리자")
    for p in admin_posts:
        print(f"[{p['department']} / Private={p['is_private']}] Title: {p['title']}")
        
    print("\n영업부 view posts (should hide other depts' private posts):")
    sales_posts = db.get_posts("영업")
    for p in sales_posts:
        print(f"[{p['department']} / Private={p['is_private']}] Title: {p['title']}")

    print("\nDatabase flow test completed successfully!")

if __name__ == "__main__":
    test_flow()
