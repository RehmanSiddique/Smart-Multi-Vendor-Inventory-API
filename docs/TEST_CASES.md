# Smart Multi-Vendor Inventory System - Test Cases

## Test Environment Setup

### Prerequisites
- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:3000`
- Database populated with test data
- Test user: `admin@acme.com` / `admin123`

---

## 1. Authentication & Authorization Tests

### Test Case 1.1: User Login
**Objective**: Verify user can login successfully
**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Enter email: `admin@acme.com`
3. Enter password: `admin123`
4. Click "Login" button
**Expected Result**: 
- User redirected to dashboard
- JWT token stored in localStorage
- User menu shows logged-in state

### Test Case 1.2: Invalid Login
**Objective**: Verify invalid credentials are rejected
**Steps**:
1. Navigate to login page
2. Enter email: `wrong@email.com`
3. Enter password: `wrongpass`
4. Click "Login" button
**Expected Result**: 
- Error message displayed
- User remains on login page
- No token stored

### Test Case 1.3: Token Refresh
**Objective**: Verify JWT token refresh works
**Steps**:
1. Login successfully
2. Wait for token to near expiry (or manually expire)
3. Make an API request
**Expected Result**: 
- Token automatically refreshed
- API request succeeds
- New token stored

---

## 2. Dashboard Tests

### Test Case 2.1: Dashboard Data Display
**Objective**: Verify dashboard shows correct data
**Steps**:
1. Login as `admin@acme.com`
2. Navigate to dashboard
**Expected Result**: 
- Today's sales displayed
- Week/Month sales shown
- Inventory stats visible (Total: 20, Low Stock, Out of Stock)
- Recent products list shown
- Charts/graphs render correctly

### Test Case 2.2: Dashboard API Integration
**Objective**: Verify dashboard fetches data from API
**Steps**:
1. Open browser developer tools (Network tab)
2. Login and go to dashboard
3. Check network requests
**Expected Result**: 
- API calls to `/api/v1/inventory/products/`
- API calls to `/api/v1/reports/dashboard/`
- All requests return 200 status
- Data properly displayed

---

## 3. Product Management Tests

### Test Case 3.1: View Products List
**Objective**: Verify products are displayed correctly
**Steps**:
1. Login and navigate to Products page
2. Check products list
**Expected Result**: 
- 20 products displayed
- Product details visible (name, SKU, price, stock)
- Pagination works if applicable
- Search/filter options available

### Test Case 3.2: Create New Product
**Objective**: Verify new product creation
**Steps**:
1. Go to Products page
2. Click "Add Product" button
3. Fill form:
   - Name: "Test Product"
   - SKU: "TEST001"
   - Category: Select any category
   - Cost Price: 10.00
   - Selling Price: 15.00
   - Initial Stock: 100
4. Click "Save"
**Expected Result**: 
- Product created successfully
- Redirected to products list
- New product appears in list
- Success message shown

### Test Case 3.3: Edit Product
**Objective**: Verify product editing works
**Steps**:
1. Go to Products page
2. Click "Edit" on any product
3. Modify name to "Updated Product Name"
4. Change price to 20.00
5. Click "Save"
**Expected Result**: 
- Product updated successfully
- Changes reflected in products list
- Success message shown

### Test Case 3.4: Delete Product
**Objective**: Verify product deletion
**Steps**:
1. Go to Products page
2. Click "Delete" on a product
3. Confirm deletion in popup
**Expected Result**: 
- Product removed from list
- Confirmation dialog shown
- Success message displayed

### Test Case 3.5: Product Search
**Objective**: Verify product search functionality
**Steps**:
1. Go to Products page
2. Enter search term in search box
3. Press Enter or click search
**Expected Result**: 
- Filtered results shown
- Only matching products displayed
- Search term highlighted if applicable

---

## 4. Category Management Tests

### Test Case 4.1: View Categories
**Objective**: Verify categories are displayed
**Steps**:
1. Navigate to Categories page
**Expected Result**: 
- 20 categories displayed
- Hierarchical structure visible
- Parent-child relationships shown

### Test Case 4.2: Create Category
**Objective**: Verify category creation
**Steps**:
1. Go to Categories page
2. Click "Add Category"
3. Fill form:
   - Name: "Test Category"
   - Description: "Test description"
   - Parent: Select existing category (optional)
4. Click "Save"
**Expected Result**: 
- Category created successfully
- Appears in categories list
- Proper hierarchy maintained

---

## 5. Supplier Management Tests

### Test Case 5.1: View Suppliers
**Objective**: Verify suppliers list
**Steps**:
1. Navigate to Suppliers page
**Expected Result**: 
- 16 suppliers displayed
- Contact information visible
- Supplier codes shown

### Test Case 5.2: Create Supplier
**Objective**: Verify supplier creation
**Steps**:
1. Go to Suppliers page
2. Click "Add Supplier"
3. Fill form:
   - Name: "Test Supplier"
   - Code: "SUP001"
   - Contact Person: "John Doe"
   - Email: "john@testsupplier.com"
   - Phone: "123-456-7890"
4. Click "Save"
**Expected Result**: 
- Supplier created successfully
- Appears in suppliers list

---

## 6. Purchase Order Tests

### Test Case 6.1: View Purchase Orders
**Objective**: Verify purchase orders display
**Steps**:
1. Navigate to Purchase Orders page
**Expected Result**: 
- 4 purchase orders displayed
- Order details visible (number, supplier, date, status)
- Proper status indicators

### Test Case 6.2: Create Purchase Order
**Objective**: Verify purchase order creation
**Steps**:
1. Go to Purchase Orders page
2. Click "Create Purchase Order"
3. Fill form:
   - Supplier: Select from dropdown
   - Expected Date: Future date
   - Add products with quantities
4. Click "Save"
**Expected Result**: 
- Purchase order created
- Order number generated
- Status set to "pending"

---

## 7. Sales Management Tests

### Test Case 7.1: View Sales
**Objective**: Verify sales records display
**Steps**:
1. Navigate to Sales page
**Expected Result**: 
- 6 sales records displayed
- Sale details visible (number, date, total, status)
- Customer information shown

### Test Case 7.2: Create Sale
**Objective**: Verify sale creation
**Steps**:
1. Go to Sales page
2. Click "New Sale"
3. Add products to sale
4. Enter customer details
5. Complete sale
**Expected Result**: 
- Sale recorded successfully
- Inventory updated automatically
- Receipt/invoice generated

---

## 8. Inventory Management Tests

### Test Case 8.1: Stock Levels
**Objective**: Verify stock tracking
**Steps**:
1. Check product stock levels
2. Create a sale with products
3. Verify stock decreases
4. Create purchase order and receive
5. Verify stock increases
**Expected Result**: 
- Stock levels update correctly
- Low stock alerts trigger when appropriate
- Inventory movements logged

### Test Case 8.2: Low Stock Alerts
**Objective**: Verify low stock notifications
**Steps**:
1. Set a product's reorder level high
2. Check dashboard
**Expected Result**: 
- Product appears in low stock list
- Alert indicators shown
- Reorder suggestions provided

---

## 9. Reports & Analytics Tests

### Test Case 9.1: Dashboard Reports
**Objective**: Verify dashboard analytics
**Steps**:
1. Go to dashboard
2. Check all report sections
**Expected Result**: 
- Sales charts display data
- Inventory valuation shown
- Top products listed
- Period comparisons available

### Test Case 9.2: Sales Reports
**Objective**: Verify sales reporting
**Steps**:
1. Navigate to Reports section
2. Generate sales report for date range
**Expected Result**: 
- Report generated successfully
- Accurate sales data shown
- Export options available

---

## 10. Multi-Tenancy Tests

### Test Case 10.1: Data Isolation
**Objective**: Verify vendor data isolation
**Steps**:
1. Login as admin@acme.com
2. Note product count (should be 20)
3. Check that only Acme Corporation data is visible
**Expected Result**: 
- Only vendor-specific data shown
- No data from other vendors visible
- Proper tenant context maintained

---

## 11. API Tests

### Test Case 11.1: API Authentication
**Objective**: Verify API requires authentication
**Steps**:
1. Make API request without token: `GET /api/v1/inventory/products/`
2. Make API request with valid token
**Expected Result**: 
- Unauthenticated request returns 401
- Authenticated request returns 200 with data

### Test Case 11.2: API Data Consistency
**Objective**: Verify API returns correct data
**Steps**:
1. Run the test script: `python test_api_data.py`
**Expected Result**: 
- All endpoints return 200 status
- Data counts match expectations:
  - Products: 20 items
  - Categories: 20 items
  - Suppliers: 16 items
  - Purchase Orders: 4 items
  - Sales: 6 items

---

## 12. Performance Tests

### Test Case 12.1: Page Load Times
**Objective**: Verify acceptable performance
**Steps**:
1. Use browser dev tools to measure load times
2. Navigate to different pages
**Expected Result**: 
- Dashboard loads within 2 seconds
- Product list loads within 3 seconds
- API responses under 500ms

### Test Case 12.2: Large Data Sets
**Objective**: Verify system handles large data
**Steps**:
1. Add more test data if needed
2. Test pagination
3. Test search with large results
**Expected Result**: 
- Pagination works smoothly
- Search remains responsive
- No performance degradation

---

## 13. Error Handling Tests

### Test Case 13.1: Network Errors
**Objective**: Verify graceful error handling
**Steps**:
1. Disconnect network
2. Try to perform actions
3. Reconnect network
**Expected Result**: 
- Appropriate error messages shown
- No application crashes
- Recovery when network restored

### Test Case 13.2: Validation Errors
**Objective**: Verify form validation
**Steps**:
1. Try to create product with duplicate SKU
2. Try to create product with invalid data
**Expected Result**: 
- Validation errors displayed
- Form submission prevented
- Clear error messages shown

---

## 14. Security Tests

### Test Case 14.1: SQL Injection Protection
**Objective**: Verify SQL injection protection
**Steps**:
1. Try entering SQL injection strings in search fields
2. Example: `'; DROP TABLE products; --`
**Expected Result**: 
- No SQL injection occurs
- Input properly sanitized
- Application remains stable

### Test Case 14.2: XSS Protection
**Objective**: Verify XSS protection
**Steps**:
1. Try entering script tags in form fields
2. Example: `<script>alert('xss')</script>`
**Expected Result**: 
- Scripts not executed
- Input properly escaped
- No XSS vulnerabilities

---

## Test Execution Checklist

### Before Testing
- [ ] Backend server running
- [ ] Frontend server running
- [ ] Database has test data
- [ ] Test user account exists

### During Testing
- [ ] Document any failures
- [ ] Take screenshots of issues
- [ ] Note browser console errors
- [ ] Check network requests in dev tools

### After Testing
- [ ] Clean up test data if needed
- [ ] Document results
- [ ] Report any bugs found
- [ ] Verify fixes work

---

## Quick Smoke Test (5 minutes)

For a quick verification that everything works:

1. **Login**: `admin@acme.com` / `admin123`
2. **Dashboard**: Check data displays (20 products, sales stats)
3. **Products**: View list, create one product
4. **API Test**: Run `python test_api_data.py`
5. **Logout**: Verify logout works

If all these pass, the system is working correctly.