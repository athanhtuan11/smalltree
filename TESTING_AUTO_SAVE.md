# Testing Auto-Save Monthly Service Feature

## 🎯 How to Test:

### 1. **Database Setup**
```bash
# Run migration to create MonthlyService table
flask db migrate -m "add MonthlyService table"
flask db upgrade
```

### 2. **Testing Steps**

#### Step 1: Open Invoice Page
- Navigate to `/invoice` 
- Select month (e.g. November 2025)
- Verify checkboxes show default state (both checked)

#### Step 2: Test Auto-Save
1. **Uncheck English checkbox** for a student
   - Should see console log: "✅ Đã lưu dịch vụ cho học sinh X"
   - Total amount should decrease by 250,000đ
   
2. **Uncheck STEAMAX checkbox** for same student  
   - Should see console log: "✅ Đã lưu dịch vụ cho học sinh X"
   - Total amount should decrease by 200,000đ

3. **Refresh page**
   - Checkboxes should retain unchecked state
   - Total amounts should match previous calculation

#### Step 3: Test Persistence Across Months
1. Go to different month (e.g. December 2025)
   - All checkboxes should be checked (default for new month)
   
2. Return to original month
   - Previous selections should be preserved

#### Step 4: Test Word Export  
1. Select students with different service combinations
2. Click "Xuất Word"
3. Verify exported invoices only show selected services

### 3. **Expected Database Records**

```sql
-- Check if records are being created
SELECT * FROM monthly_service;

-- Expected structure:
id | child_id | month   | has_english | has_steamax | created_date | updated_date
1  | 1        | 2025-11 | true        | false       | ...          | ...
2  | 2        | 2025-11 | false       | true        | ...          | ...
```

### 4. **API Testing**

```javascript
// Test API directly in browser console
fetch('/api/save_monthly_service', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        child_id: 1,
        month: '2025-11', 
        has_english: false,
        has_steamax: true
    })
})
.then(r => r.json())
.then(console.log);
```

### 5. **Troubleshooting**

#### Console Errors:
- **404 on API**: Check routes are properly registered
- **500 error**: Check database connection and model imports
- **No auto-save**: Check JavaScript event listeners

#### Database Issues:
- **Table not found**: Run migration command
- **Constraint errors**: Check unique constraint on child_id + month

### 6. **Features to Verify**

✅ **Auto-save on checkbox change**
✅ **Real-time total calculation**  
✅ **Persistence across page refresh**
✅ **Default values for new months**
✅ **Word export uses saved data**
✅ **Quick toggle buttons work**
✅ **Mobile responsive design**

## 🚀 Success Criteria

- [x] Checkbox changes save automatically to database
- [x] Data persists across browser refresh  
- [x] Different months have independent settings
- [x] Word export reflects saved choices
- [x] No manual save button needed
- [x] Console shows success/error messages
- [x] UI updates immediately on change

## 📊 Test Data Example

```
Student: Nguyễn Văn A (ID: 1)
Month: 2025-11
- English: ✅ (250,000đ)
- STEAMAX: ❌ (0đ)
- Total: Base + 250,000đ

Student: Trần Thị B (ID: 2)  
Month: 2025-11
- English: ❌ (0đ)
- STEAMAX: ✅ (200,000đ)
- Total: Base + 200,000đ
```