from backend.core.conflict_resolver import ConflictResolver
from backend.utils.types import Change, Operation, Source

resolver = ConflictResolver(timestamp_column='last_modified')

print("=" * 60)
print("CONFLICT RESOLVER COMPREHENSIVE TEST")
print("=" * 60)

# Test 1: MySQL wins (newer timestamp)
print("\n1️⃣  Test: MySQL Wins (Newer Timestamp)")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='1',
        source=Source.SHEETS,
        data={'email': 'alice@sheets.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='1',
        source=Source.MYSQL,
        data={'email': 'alice@mysql.com', 'last_modified': '2026-01-14 10:05:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 0)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 1)")
print(f"   ✅ PASS" if len(resolved_sheets) == 0 and len(resolved_mysql) == 1 else "   ❌ FAIL")

# Test 2: Sheets wins (newer timestamp)
print("\n2️⃣  Test: Sheets Wins (Newer Timestamp)")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='2',
        source=Source.SHEETS,
        data={'email': 'bob@sheets.com', 'last_modified': '2026-01-14 10:10:00'}
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='2',
        source=Source.MYSQL,
        data={'email': 'bob@mysql.com', 'last_modified': '2026-01-14 10:05:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 1)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 0)")
print(f"   ✅ PASS" if len(resolved_sheets) == 1 and len(resolved_mysql) == 0 else "   ❌ FAIL")

# Test 3: No conflict (different primary keys)
print("\n3️⃣  Test: No Conflict (Different PKs)")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='3',
        source=Source.SHEETS,
        data={'email': 'charlie@sheets.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='4',
        source=Source.MYSQL,
        data={'email': 'david@mysql.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 1)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 1)")
print(f"   ✅ PASS" if len(resolved_sheets) == 1 and len(resolved_mysql) == 1 else "   ❌ FAIL")

# Test 4: Multiple conflicts
print("\n4️⃣  Test: Multiple Conflicts")
sheets_changes = [
    Change(Operation.UPDATE, '5', Source.SHEETS, 
           {'email': 'user5@sheets.com', 'last_modified': '2026-01-14 10:00:00'}),
    Change(Operation.UPDATE, '6', Source.SHEETS, 
           {'email': 'user6@sheets.com', 'last_modified': '2026-01-14 10:10:00'}),  # Newer
    Change(Operation.UPDATE, '7', Source.SHEETS, 
           {'email': 'user7@sheets.com', 'last_modified': '2026-01-14 10:00:00'}),
]
mysql_changes = [
    Change(Operation.UPDATE, '5', Source.MYSQL, 
           {'email': 'user5@mysql.com', 'last_modified': '2026-01-14 10:05:00'}),  # Newer
    Change(Operation.UPDATE, '6', Source.MYSQL, 
           {'email': 'user6@mysql.com', 'last_modified': '2026-01-14 10:05:00'}),
    Change(Operation.UPDATE, '7', Source.MYSQL, 
           {'email': 'user7@mysql.com', 'last_modified': '2026-01-14 10:05:00'}),  # Newer
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 1, pk=6)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 2, pk=5,7)")
expected = len(resolved_sheets) == 1 and len(resolved_mysql) == 2
if expected and resolved_sheets[0].primary_key_value == '6':
    print(f"   ✅ PASS")
else:
    print(f"   ❌ FAIL")

# Test 5: Missing timestamp
print("\n5️⃣  Test: Missing Timestamp")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='8',
        source=Source.SHEETS,
        data={'email': 'missing@sheets.com'}  # No last_modified
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='8',
        source=Source.MYSQL,
        data={'email': 'missing@mysql.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 0)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 1, defaults to MySQL)")
print(f"   ✅ PASS" if len(resolved_sheets) == 0 and len(resolved_mysql) == 1 else "   ❌ FAIL")

# Test 6: Invalid timestamp format
print("\n6️⃣  Test: Invalid Timestamp Format")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='9',
        source=Source.SHEETS,
        data={'email': 'invalid@sheets.com', 'last_modified': 'not-a-date'}
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='9',
        source=Source.MYSQL,
        data={'email': 'invalid@mysql.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 0)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 1, defaults to MySQL)")
print(f"   ✅ PASS" if len(resolved_sheets) == 0 and len(resolved_mysql) == 1 else "   ❌ FAIL")

# Test 7: Same timestamp (tie - MySQL wins by >=)
print("\n7️⃣  Test: Same Timestamp (Tie)")
sheets_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='10',
        source=Source.SHEETS,
        data={'email': 'tie@sheets.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
mysql_changes = [
    Change(
        operation=Operation.UPDATE,
        primary_key_value='10',
        source=Source.MYSQL,
        data={'email': 'tie@mysql.com', 'last_modified': '2026-01-14 10:00:00'}
    )
]
resolved_sheets, resolved_mysql = resolver.resolve_conflicts(sheets_changes, mysql_changes)
print(f"   Sheets changes: {len(resolved_sheets)} (expected: 0)")
print(f"   MySQL changes: {len(resolved_mysql)} (expected: 1, MySQL wins on tie)")
print(f"   ✅ PASS" if len(resolved_sheets) == 0 and len(resolved_mysql) == 1 else "   ❌ FAIL")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)