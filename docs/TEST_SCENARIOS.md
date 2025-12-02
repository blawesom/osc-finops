# OSC-FinOps Test Scenarios

This document defines comprehensive test scenarios for all functional requirements, API endpoints, frontend interactions, and performance criteria.

## Test Organization

Tests are organized by:
- **Functional Requirements (FR)**: Test cases for each feature
- **Non-Functional Requirements (NFR)**: Performance and security tests
- **API Endpoints**: Integration tests for REST API
- **Frontend Interactions**: User interface and interaction tests
- **Security**: Authentication and authorization tests

## 1. Authentication & Session Management Tests

### TS-1.1: Login with Valid Credentials and Region
**Requirement**: NFR-1.1, FR-1.1 (implicit)

**Test Steps**:
1. Send POST request to `/api/auth/login` with valid access_key, secret_key, and region
2. Verify region is one of: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
3. Verify response contains session_id
4. Verify session is created in backend (in-memory) with region
5. Verify session timeout is set to 30 minutes

**Expected Results**:
- Status code: 200
- Response contains `session_id`
- Session exists in backend storage with region
- Session has 30-minute timeout
- Region stored in session

**Test Data**:
- Valid Outscale Access Key
- Valid Outscale Secret Key
- Valid Region: eu-west-2 (or cloudgouv-eu-west-1, us-west-1, us-east-2)

### TS-1.2: Login with Invalid Credentials
**Requirement**: NFR-1.1

**Test Steps**:
1. Send POST request to `/api/auth/login` with invalid access_key or secret_key and valid region
2. Verify error response

**Expected Results**:
- Status code: 401
- Error message indicates authentication failure
- No session created

**Test Data**:
- Invalid Access Key: "INVALID_KEY"
- Invalid Secret Key: "INVALID_SECRET"
- Valid Region: eu-west-2

### TS-1.2a: Login without Region
**Requirement**: NFR-1.1

**Test Steps**:
1. Send POST request to `/api/auth/login` with access_key and secret_key but no region
2. Verify error response

**Expected Results**:
- Status code: 400
- Error message indicates region is required
- No session created

### TS-1.2b: Login with Invalid Region
**Requirement**: NFR-1.1

**Test Steps**:
1. Send POST request to `/api/auth/login` with valid credentials but invalid region (e.g., "invalid-region")
2. Verify error response

**Expected Results**:
- Status code: 400
- Error message indicates invalid region
- Valid regions are: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2
- No session created

### TS-1.3: Session Expiration
**Requirement**: NFR-1.1

**Test Steps**:
1. Login with valid credentials
2. Wait for session timeout (30 minutes) or simulate timeout
3. Send API request with expired session_id
4. Verify session expiration handling

**Expected Results**:
- Status code: 401
- Error message indicates session expired
- Session removed from backend storage

### TS-1.4: Logout
**Requirement**: NFR-1.1

**Test Steps**:
1. Login with valid credentials
2. Send POST request to `/api/auth/logout` with session_id
3. Verify session is removed
4. Send API request with logged-out session_id

**Expected Results**:
- Logout returns status 200
- Session removed from backend
- Subsequent requests with same session_id return 401

### TS-1.5: Session Check
**Requirement**: NFR-1.1

**Test Steps**:
1. Login with valid credentials
2. Send GET request to `/api/auth/session` with session_id
3. Verify session status

**Expected Results**:
- Status code: 200
- Response indicates valid session
- Session timeout information included

### TS-1.6: Credential Storage (Security)
**Requirement**: NFR-1.1, NFR-1.3

**Test Steps**:
1. Login with valid credentials
2. Check backend logs for credentials
3. Check database/files for credential storage
4. Verify credentials only in memory

**Expected Results**:
- No credentials in logs
- No credentials in database/files
- Credentials only in session object (memory)

### TS-1.7: API Authentication (OSC4-HMAC-SHA256)
**Requirement**: NFR-1.2

**Test Steps**:
1. Login with valid credentials
2. Make API call that triggers Outscale API request
3. Verify request uses OSC4-HMAC-SHA256 signature
4. Verify osc-sdk-python is used for API calls

**Expected Results**:
- API calls use osc-sdk-python SDK
- Authentication headers include OSC4-HMAC-SHA256
- API calls succeed

## 2. Quote Building Tests (FR-1.1, FR-1.2)

### TS-2.1: Catalog Loading - Single Region (Unauthenticated)
**Requirement**: FR-1.2

**Test Steps**:
1. **Do NOT login** (catalog access does not require authentication)
2. Send GET request to `/api/catalog?region=eu-west-2`
3. Verify catalog response

**Expected Results**:
- Status code: 200
- Response contains catalog entries
- Entries have required fields (service, type, operation, price, etc.)
- Catalog cached for 24 hours
- **No authentication required**

**Test Data**:
- Region: eu-west-2 (or cloudgouv-eu-west-1, us-west-1, us-east-2)

### TS-2.1a: Catalog Loading - Authenticated (Also Works)
**Requirement**: FR-1.2

**Test Steps**:
1. Login with valid credentials and region
2. Send GET request to `/api/catalog?region=eu-west-2`
3. Verify catalog response (should work same as unauthenticated)

**Expected Results**:
- Status code: 200
- Response contains catalog entries
- Works with or without authentication
- Catalog cached for 24 hours

**Test Data**:
- Region: eu-west-2

### TS-2.2: Catalog Loading - Multiple Regions (Unauthenticated)
**Requirement**: FR-1.2

**Test Steps**:
1. **Do NOT login** (catalog access does not require authentication)
2. Send GET requests for multiple regions (eu-west-2, cloudgouv-eu-west-1, us-west-1, us-east-2)
3. Verify each region returns correct catalog

**Expected Results**:
- Each region returns its own catalog
- Catalogs are cached separately per region
- No cross-region data mixing
- **All regions accessible without authentication**
- Only supported regions work: cloudgouv-eu-west-1, eu-west-2, us-west-1, us-east-2

### TS-2.3: Catalog Caching
**Requirement**: FR-1.2, NFR-2.3

**Test Steps**:
1. Login and fetch catalog for region
2. Immediately fetch same catalog again
3. Verify cache is used (check response time)
4. Force refresh via POST `/api/catalog/refresh`
5. Verify cache is invalidated

**Expected Results**:
- Second request uses cache (faster response)
- Cache TTL is 24 hours
- Refresh endpoint invalidates cache
- After refresh, new catalog is fetched

### TS-2.4: Catalog Filtering by Category
**Requirement**: FR-1.2

**Test Steps**:
1. Fetch catalog
2. Filter by category (Compute, Storage, Network, Licence)
3. Verify filtered results

**Expected Results**:
- Filtered results only contain specified category
- All categories can be filtered
- "All Categories" returns all entries

### TS-2.5: Quote Creation - Single Resource
**Requirement**: FR-1.1

**Test Steps**:
1. Login with valid credentials
2. Create quote with single resource item
3. Verify quote creation

**Expected Results**:
- Status code: 201
- Quote ID returned
- Quote contains resource item
- Cost calculated correctly

**Test Data**:
- Resource: VM (t2.micro equivalent)
- Quantity: 1
- Duration: 1 month

### TS-2.6: Quote Creation - Multiple Resources
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote with multiple resource items
2. Verify all items included
3. Verify total cost calculation

**Expected Results**:
- All resources included in quote
- Total cost is sum of all items
- Individual item costs correct

### TS-2.7: Cost Calculation - Base Cost
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote item with known price
2. Set quantity and duration
3. Verify cost = quantity × unit_price × duration

**Expected Results**:
- Cost calculation matches formula
- Handles hourly pricing correctly
- Handles monthly pricing correctly

**Test Data**:
- Unit price: 0.10 per hour
- Quantity: 2
- Duration: 100 hours
- Expected cost: 0.10 × 2 × 100 = 20.00

### TS-2.8: Commitment Discount Application
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote with compute resource
2. Apply 1-year commitment discount
3. Verify discount applied correctly

**Expected Results**:
- Discount percentage correct (40% for compute, 1 year)
- Cost after discount = base_cost × (1 - discount_percent/100)
- Different commitment periods have different discounts

**Test Data**:
- Base cost: 100.00
- Commitment: 1 year
- Discount: 40%
- Expected cost: 60.00

### TS-2.9: Global Discount Application
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote with multiple items
2. Apply global discount (e.g., 10%)
3. Verify discount applied to total

**Expected Results**:
- Global discount applied after commitment discounts
- Final cost = (cost_after_commitment) × (1 - global_discount/100)

### TS-2.10: Quote Update
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote
2. Update quote with PUT request
3. Verify quote updated

**Expected Results**:
- Status code: 200
- Quote reflects updates
- Cost recalculated if items changed

### TS-2.11: Quote Deletion
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote
2. Delete quote with DELETE request
3. Verify quote deleted
4. Attempt to retrieve deleted quote

**Expected Results**:
- Status code: 204 or 200
- Quote no longer exists
- Retrieval returns 404

### TS-2.12: Quote Export - CSV
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote with multiple items
2. Export quote as CSV
3. Verify CSV format and content

**Expected Results**:
- Status code: 200
- Content-Type: text/csv
- CSV contains all quote items
- CSV format is valid

### TS-2.13: Quote Export - PDF (Optional)
**Requirement**: FR-1.1

**Test Steps**:
1. Create quote
2. Export quote as PDF
3. Verify PDF generation

**Expected Results**:
- Status code: 200
- Content-Type: application/pdf
- PDF contains quote information
- PDF is readable

### TS-2.14: Quote Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Create quote with 100 items
2. Measure calculation time
3. Verify performance target

**Expected Results**:
- Quote calculation < 1 second
- Response time acceptable for user experience

## 3. Consumption History Tests (FR-2.1, FR-2.2)

### TS-3.1: Consumption Query - Date Range
**Requirement**: FR-2.1

**Test Steps**:
1. Login with valid credentials
2. Query consumption for date range (e.g., last 30 days)
3. Verify consumption data returned

**Expected Results**:
- Status code: 200
- Response contains consumption entries
- Entries have required fields (service, type, operation, value, price, dates)

**Test Data**:
- from_date: 30 days ago
- to_date: today

### TS-3.2: Consumption Granularity - Day
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with granularity=day
2. Verify data aggregated by day
3. Verify each day has separate entry

**Expected Results**:
- Data grouped by day
- Each day entry has date and total cost
- All days in range included

### TS-3.3: Consumption Granularity - Week
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with granularity=week
2. Verify data aggregated by week
3. Verify week boundaries correct

**Expected Results**:
- Data grouped by week
- Week boundaries align with calendar weeks
- Each week entry has date range and total cost

### TS-3.4: Consumption Granularity - Month
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with granularity=month
2. Verify data aggregated by month
3. Verify month boundaries correct

**Expected Results**:
- Data grouped by month
- Month boundaries align with calendar months
- Each month entry has date range and total cost

### TS-3.5: Consumption Filtering - Region
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with region filter
2. Verify only specified region data returned
3. Test multiple regions

**Expected Results**:
- Filtered results only contain specified region
- Multiple regions can be queried separately
- Region filter works correctly

### TS-3.6: Consumption Filtering - Service
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with service filter
2. Verify only specified service data returned

**Expected Results**:
- Filtered results only contain specified service
- Service filter works correctly

### TS-3.7: Consumption Filtering - Resource Type
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption with resource_type filter
2. Verify only specified resource type returned

**Expected Results**:
- Filtered results only contain specified resource type
- Resource type filter works correctly

### TS-3.8: Multi-Account Consumption
**Requirement**: FR-2.1, FR-5.2

**Test Steps**:
1. Login with credentials for account A
2. Query consumption for account A
3. Switch to account B
4. Query consumption for account B
5. Verify accounts are separate

**Expected Results**:
- Each account returns its own consumption data
- No cross-account data mixing
- Account switching works correctly

### TS-3.9: Multi-Region Consumption
**Requirement**: FR-2.1

**Test Steps**:
1. Query consumption for multiple regions
2. Verify data aggregated correctly
3. Verify region separation

**Expected Results**:
- Multi-region queries return combined data
- Region information preserved in results
- Data correctly separated by region

### TS-3.10: Consumption Aggregation
**Requirement**: FR-2.2

**Test Steps**:
1. Query consumption data
2. Aggregate by resource type
3. Verify aggregation correct

**Expected Results**:
- Aggregation groups by resource type
- Total costs calculated correctly
- Aggregation preserves data integrity

### TS-3.11: Top Cost Drivers
**Requirement**: FR-2.2

**Test Steps**:
1. Query consumption data
2. Identify top cost drivers
3. Verify top drivers correct

**Expected Results**:
- Top cost drivers identified
- Sorted by cost (highest first)
- Top N drivers returned (configurable)

### TS-3.12: Consumption Export - CSV
**Requirement**: FR-2.2

**Test Steps**:
1. Query consumption data
2. Export as CSV
3. Verify CSV format

**Expected Results**:
- CSV contains consumption data
- Format is valid
- All fields included

### TS-3.13: Consumption Export - JSON
**Requirement**: FR-2.2

**Test Steps**:
1. Query consumption data
2. Export as JSON
3. Verify JSON format

**Expected Results**:
- JSON contains consumption data
- Format is valid JSON
- Structure matches API response

### TS-3.14: Consumption Caching
**Requirement**: NFR-2.3

**Test Steps**:
1. Query consumption for date range
2. Immediately query same range again
3. Verify cache used
4. Wait for cache TTL (1 hour)
5. Verify cache expired

**Expected Results**:
- Second request uses cache (faster)
- Cache TTL is 1 hour
- After TTL, new data fetched

### TS-3.15: Consumption Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query consumption for 1 month of data
2. Measure response time
3. Verify performance target

**Expected Results**:
- Query completes in < 5 seconds for 1 month
- Response time acceptable

## 4. Current Cost Evaluation Tests (FR-3.1, FR-3.2)

### TS-4.1: Current Cost Evaluation - All Resources
**Requirement**: FR-3.1

**Test Steps**:
1. Login with valid credentials
2. Query current costs for account
3. Verify all resource types included

**Expected Results**:
- Status code: 200
- Response contains costs for all resource types
- Resource types: VMs, Volumes, Snapshots, Public IPs, NAT Services, Load Balancers, VPNs, OOS buckets

### TS-4.2: Cost Calculation - Per Resource Type
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs
2. Verify cost per resource type calculated
3. Verify total cost is sum of all types

**Expected Results**:
- Each resource type has cost breakdown
- Total cost = sum of all resource type costs
- Costs calculated correctly

### TS-4.3: Cost Per Hour/Month/Year
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs
2. Verify cost_per_hour calculated
3. Verify cost_per_month calculated
4. Verify cost_per_year calculated

**Expected Results**:
- cost_per_month = cost_per_hour × HOURS_PER_MONTH
- cost_per_year = cost_per_month × 12
- Calculations accurate

### TS-4.4: Catalog Correlation
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs
2. Verify resources correlated with catalog prices
3. Verify pricing matches catalog

**Expected Results**:
- Resources matched to catalog entries
- Prices from catalog used
- Correlation accurate

### TS-4.5: Tag Filtering
**Requirement**: FR-3.1, FR-5.1

**Test Steps**:
1. Query current costs with tag filter
2. Verify only tagged resources included
3. Test multiple tag keys/values

**Expected Results**:
- Tag filtering works correctly
- Multiple tags can be filtered
- Filtered results accurate

### TS-4.6: Output Format - Human Readable
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs with format=human
2. Verify human-readable format

**Expected Results**:
- Format is human-readable
- Easy to understand
- Includes summary information

### TS-4.7: Output Format - JSON
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs with format=json
2. Verify JSON format

**Expected Results**:
- Valid JSON
- Structure matches specification
- All data included

### TS-4.8: Output Format - CSV
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs with format=csv
2. Verify CSV format

**Expected Results**:
- Valid CSV
- All resources included
- Format correct

### TS-4.9: Output Format - ODS
**Requirement**: FR-3.1

**Test Steps**:
1. Query current costs with format=ods
2. Verify ODS format

**Expected Results**:
- Valid ODS file
- Can be opened in spreadsheet software
- Data correct

### TS-4.10: Resource Cost Details
**Requirement**: FR-3.2

**Test Steps**:
1. Query current costs
2. Verify individual resource costs shown
3. Verify resource specifications included

**Expected Results**:
- Each resource has cost and specifications
- Details include: resource_id, type, region, cost, specs
- Information complete

### TS-4.11: IOPS Cost Calculation
**Requirement**: FR-3.2

**Test Steps**:
1. Query costs for BSU volumes with IOPS
2. Verify IOPS costs calculated
3. Verify total volume cost includes IOPS

**Expected Results**:
- IOPS costs calculated correctly
- Total volume cost = storage cost + IOPS cost
- Calculation matches osc-cost logic

### TS-4.12: Dedicated Instances Handling
**Requirement**: FR-3.2

**Test Steps**:
1. Query costs for account with dedicated instances
2. Verify dedicated instance costs calculated
3. Verify handling correct

**Expected Results**:
- Dedicated instances identified
- Costs calculated correctly
- Handled separately from regular VMs

### TS-4.13: Flexible GPUs Handling
**Requirement**: FR-3.2

**Test Steps**:
1. Query costs for account with flexible GPUs
2. Verify flexible GPU costs calculated
3. Verify handling correct

**Expected Results**:
- Flexible GPUs identified
- Costs calculated correctly
- Handled separately

### TS-4.14: Current Cost Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query current costs for account with < 1000 resources
2. Measure response time
3. Verify performance target

**Expected Results**:
- Query completes in < 10 seconds
- Response time acceptable

## 5. Trend Analysis & Cost Drift Tests (FR-4.1, FR-4.2)

### TS-5.1: Trend Calculation - Daily
**Requirement**: FR-4.1

**Test Steps**:
1. Query trends with granularity=day
2. Verify daily trends calculated
3. Verify trend data structure

**Expected Results**:
- Daily trend data returned
- Each day has cost value
- Trend shows cost changes over time

### TS-5.2: Trend Calculation - Weekly
**Requirement**: FR-4.1

**Test Steps**:
1. Query trends with granularity=week
2. Verify weekly trends calculated

**Expected Results**:
- Weekly trend data returned
- Each week has cost value
- Trend accurate

### TS-5.3: Trend Calculation - Monthly
**Requirement**: FR-4.1

**Test Steps**:
1. Query trends with granularity=month
2. Verify monthly trends calculated

**Expected Results**:
- Monthly trend data returned
- Each month has cost value
- Trend accurate

### TS-5.4: Cost Growth Rate Calculation
**Requirement**: FR-4.1

**Test Steps**:
1. Query trends for date range
2. Verify growth rate calculated
3. Verify calculation correct

**Expected Results**:
- Growth rate calculated
- Formula: ((current - previous) / previous) × 100
- Growth rate accurate

### TS-5.5: Historical Average Calculation
**Requirement**: FR-4.1

**Test Steps**:
1. Query trends for date range
2. Verify historical average calculated
3. Verify average correct

**Expected Results**:
- Historical average calculated
- Average = sum of costs / number of periods
- Average accurate

### TS-5.6: Cost Drift Calculation
**Requirement**: FR-4.2

**Test Steps**:
1. Provide estimated costs (osc-cost format)
2. Query actual consumption for same period
3. Calculate drift
4. Verify drift calculation

**Expected Results**:
- Drift calculated per resource category
- Drift percentage = ((estimated - actual) / actual) × 100
- Drift calculation matches osc-cost logic

### TS-5.7: Significant Variance Identification
**Requirement**: FR-4.2

**Test Steps**:
1. Calculate drift with significant variances
2. Verify significant variances identified
3. Verify threshold correct

**Expected Results**:
- Significant variances identified (e.g., > 10% drift)
- Variances highlighted in results
- Threshold configurable

### TS-5.8: Trend Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query trends for 12 months
2. Measure response time
3. Verify performance target

**Expected Results**:
- Query completes in < 10 seconds for 12 months
- Response time acceptable

## 6. Budget Management Tests (FR-4.3)

### TS-6.1: Budget Creation - Monthly
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget with period=monthly
2. Verify budget created
3. Verify period correct

**Expected Results**:
- Status code: 201
- Budget ID returned
- Period set to monthly
- Budget stored correctly

### TS-6.2: Budget Creation - Quarterly
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget with period=quarterly
2. Verify budget created
3. Verify period correct

**Expected Results**:
- Budget created successfully
- Period set to quarterly
- Budget boundaries correct (3 months)

### TS-6.3: Budget Creation - Yearly
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget with period=yearly
2. Verify budget created
3. Verify period correct

**Expected Results**:
- Budget created successfully
- Period set to yearly
- Budget boundaries correct (12 months)

### TS-6.4: Budget Alert Thresholds
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget with alert thresholds (50%, 75%, 90%, 100%)
2. Simulate spending at each threshold
3. Verify alerts triggered

**Expected Results**:
- Alerts triggered at correct thresholds
- Alert status tracked
- Alerts can be retrieved

### TS-6.5: Budget vs. Actual Tracking
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget
2. Query budget status
3. Verify budget vs. actual calculated
4. Verify remaining budget calculated

**Expected Results**:
- Budget status shows actual spending
- Remaining budget = budget_amount - actual_spending
- Calculations accurate

### TS-6.6: Budget Utilization Display
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget
2. Query budget status
3. Verify utilization percentage displayed

**Expected Results**:
- Utilization = (actual / budget) × 100
- Utilization displayed correctly
- Percentage accurate

### TS-6.7: Budget Compliance Reports
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget
2. Generate compliance report
3. Verify report content

**Expected Results**:
- Report contains budget information
- Report shows compliance status
- Report format correct

### TS-6.8: Budget Update
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget
2. Update budget with PUT request
3. Verify budget updated

**Expected Results**:
- Status code: 200
- Budget reflects updates
- History preserved (if implemented)

### TS-6.9: Budget Deletion
**Requirement**: FR-4.3

**Test Steps**:
1. Create budget
2. Delete budget
3. Verify budget deleted

**Expected Results**:
- Status code: 204 or 200
- Budget no longer exists
- Retrieval returns 404

## 7. Cost Allocation Tests (FR-5.1)

### TS-7.1: Cost Allocation by Tags
**Requirement**: FR-5.1

**Test Steps**:
1. Query costs with tag filter
2. Verify costs allocated by tags
3. Verify allocation correct

**Expected Results**:
- Costs grouped by tag keys/values
- Allocation accurate
- All tagged resources included

### TS-7.2: Cost Allocation by Projects
**Requirement**: FR-5.1

**Test Steps**:
1. Allocate costs to projects (using tags)
2. Verify project allocation
3. Verify totals correct

**Expected Results**:
- Costs allocated to projects
- Project totals calculated
- Allocation accurate

### TS-7.3: Cost Allocation Reports
**Requirement**: FR-5.1

**Test Steps**:
1. Generate cost allocation report
2. Verify report content
3. Verify format correct

**Expected Results**:
- Report contains allocation data
- Format correct
- Allocations included

## 8. Multi-Account Tests (FR-5.2)

### TS-8.1: Account Switching
**Requirement**: FR-5.2

**Test Steps**:
1. Login with account A credentials
2. Switch to account B
3. Verify account switched
4. Query data for account B

**Expected Results**:
- Account switched successfully
- Data for account B returned
- No data from account A

### TS-8.2: Cross-Account Aggregation
**Requirement**: FR-5.2

**Test Steps**:
1. Login with multiple accounts
2. Aggregate costs across accounts
3. Verify aggregation correct

**Expected Results**:
- Costs aggregated correctly
- All accounts included
- Totals accurate

### TS-8.3: Per-Account Budgets
**Requirement**: FR-5.2

**Test Steps**:
1. Create budget for account A
2. Create budget for account B
3. Verify budgets separate

**Expected Results**:
- Budgets created per account
- Budgets are separate
- No cross-account budget mixing

## 9. Frontend Interaction Tests

### TS-9.1: Login Form
**Test Steps**:
1. Open application
2. Enter credentials in login form
3. Submit form
4. Verify login success

**Expected Results**:
- Login form displays correctly
- Form validation works
- Login successful
- Redirect to main application

### TS-9.2: Tab Navigation
**Test Steps**:
1. Login to application
2. Navigate between tabs (Quotes, Consumption, Cost, Trends, Budgets)
3. Verify tab switching works

**Expected Results**:
- Tabs display correctly
- Tab switching works
- Content loads for each tab
- Active tab highlighted

### TS-9.3: Quote Building UI
**Test Steps**:
1. Navigate to Quotes tab
2. Select region and resource
3. Configure parameters
4. Add to quote
5. Verify quote updated

**Expected Results**:
- Resource selection works
- Parameter inputs functional
- Add to quote works
- Quote list updates
- Cost calculated in real-time

### TS-9.4: Consumption History UI
**Test Steps**:
1. Navigate to Consumption tab
2. Select date range
3. Choose granularity
4. Apply filters
5. View consumption data

**Expected Results**:
- Date picker works
- Granularity selector works
- Filters apply correctly
- Data displays in table/chart
- Export buttons functional

### TS-9.5: Error Handling
**Test Steps**:
1. Trigger various error scenarios
2. Verify error messages display
3. Verify user-friendly messages

**Expected Results**:
- Error messages display
- Messages are user-friendly
- Errors don't crash application
- User can recover from errors

### TS-9.6: Loading Indicators
**Test Steps**:
1. Trigger long-running operations
2. Verify loading indicators display
3. Verify indicators disappear on completion

**Expected Results**:
- Loading indicators show during operations
- Indicators clear on completion
- User experience smooth

## 10. Performance Tests

### TS-10.1: Quote Calculation Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Create quote with 100 items
2. Measure calculation time
3. Verify < 1 second

**Expected Results**:
- Calculation completes in < 1 second
- Performance acceptable

### TS-10.2: Consumption Query Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query consumption for 1 month
2. Measure response time
3. Verify < 5 seconds

**Expected Results**:
- Query completes in < 5 seconds
- Performance acceptable

### TS-10.3: Current Cost Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query current costs for account with < 1000 resources
2. Measure response time
3. Verify < 10 seconds

**Expected Results**:
- Query completes in < 10 seconds
- Performance acceptable

### TS-10.4: Trend Analysis Performance
**Requirement**: NFR-2.1

**Test Steps**:
1. Query trends for 12 months
2. Measure response time
3. Verify < 10 seconds

**Expected Results**:
- Query completes in < 10 seconds
- Performance acceptable

### TS-10.5: Concurrent Sessions
**Requirement**: NFR-2.2

**Test Steps**:
1. Simulate 50 concurrent users
2. Verify all sessions work
3. Verify performance acceptable

**Expected Results**:
- All 50 sessions functional
- Performance acceptable
- No degradation

### TS-10.6: Large Account Handling
**Requirement**: NFR-2.2

**Test Steps**:
1. Query costs for account with 10,000 resources
2. Verify query completes
3. Verify performance acceptable

**Expected Results**:
- Query completes successfully
- Performance acceptable (may exceed 10s for very large accounts)
- Pagination works if implemented

## 11. Security Tests

### TS-11.1: Input Validation
**Requirement**: NFR-1.3

**Test Steps**:
1. Send malicious input (SQL injection, XSS attempts)
2. Verify input rejected
3. Verify no security issues

**Expected Results**:
- Malicious input rejected
- No SQL injection possible
- No XSS vulnerabilities
- Input sanitized

### TS-11.2: CSRF Protection
**Requirement**: NFR-1.3

**Test Steps**:
1. Attempt CSRF attack
2. Verify protection works
3. Verify legitimate requests work

**Expected Results**:
- CSRF attacks blocked
- Legitimate requests work
- Protection effective

### TS-11.3: Session Security
**Requirement**: NFR-1.1

**Test Steps**:
1. Verify session cookies secure
2. Verify HttpOnly flag set
3. Verify SameSite protection

**Expected Results**:
- Cookies secure
- HttpOnly flag set
- SameSite protection enabled

## 12. Integration Tests

### TS-12.1: End-to-End Quote Workflow
**Test Steps**:
1. Login
2. Load catalog
3. Create quote
4. Add items
5. Apply discounts
6. Export quote

**Expected Results**:
- Complete workflow succeeds
- All steps functional
- No errors

### TS-12.2: End-to-End Consumption Workflow
**Test Steps**:
1. Login
2. Query consumption
3. Apply filters
4. View data
5. Export data

**Expected Results**:
- Complete workflow succeeds
- All steps functional
- No errors

### TS-12.3: End-to-End Cost Evaluation Workflow
**Test Steps**:
1. Login
2. Query current costs
3. Apply filters
4. View breakdown
5. Export costs

**Expected Results**:
- Complete workflow succeeds
- All steps functional
- No errors

## Test Data Requirements

### Valid Test Accounts
- Account with various resource types
- Account with multiple regions
- Account with tagged resources
- Account with consumption history

### Test Credentials
- Valid Access Key / Secret Key pairs
- Invalid credentials for negative testing
- Multiple accounts for multi-account testing

### Test Data Sets
- Catalog data for multiple regions
- Consumption data for various date ranges
- Resource data for cost evaluation
- Historical data for trend analysis

## Test Execution Strategy

1. **Unit Tests**: Run on every commit
2. **Integration Tests**: Run on pull requests
3. **End-to-End Tests**: Run before releases
4. **Performance Tests**: Run weekly or on demand
5. **Security Tests**: Run before releases

## Test Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: All API endpoints covered
- **End-to-End Tests**: All major workflows covered
- **Performance Tests**: All NFR targets verified
- **Security Tests**: All security requirements verified

