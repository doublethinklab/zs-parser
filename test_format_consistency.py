# Test script to verify that parsing the same NDJSON input to CSV and JSON formats
# produces the same data count.


import os
import sys
import json
import csv
import subprocess
import tempfile
from pathlib import Path
import io

def count_csv_records(csv_content):
    """Count records in CSV content using proper CSV parsing (excluding header)"""
    csv_file = io.StringIO(csv_content)
    reader = csv.reader(csv_file)
    
    next(reader, None)
    
    count = 0
    for row in reader:
        if row:
            count += 1
    
    return count

def count_json_records(json_content):
    """Count records in JSON content"""
    data = json.loads(json_content)
    if isinstance(data, list):
        return len(data)
    else:
        return 1

def run_parser(input_file, output_file, format_type):
    """Run the zs-parser with specified format"""
    script_path = Path(__file__).parent / 'src' / 'zs_parser' / 'main.py'
    cmd = ['python', str(script_path), str(input_file), '--output', str(output_file), '--format', format_type]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Parser failed: {result.stderr}")
    
    return result

def test_format_consistency(ndjson_file):
    print(f"Testing format consistency for: {ndjson_file}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_output = Path(temp_dir) / 'output.csv'
        json_output = Path(temp_dir) / 'output.json'
        
        try:
            print("Parsing to CSV format...")
            run_parser(ndjson_file, csv_output, 'csv')
            
            print("Parsing to JSON format...")
            run_parser(ndjson_file, json_output, 'json')
            
            with open(csv_output, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            csv_count = count_csv_records(csv_content)
            
            with open(json_output, 'r', encoding='utf-8') as f:
                json_content = f.read()
            json_count = count_json_records(json_content)
            
            print(f"CSV record count: {csv_count}")
            print(f"JSON record count: {json_count}")
            
            if csv_count == json_count:
                print("SUCCESS: Data counts match between CSV and JSON formats")
                return True
            else:
                print(f"FAILED: Data count mismatch - CSV: {csv_count}, JSON: {json_count}")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False

def main():
    print("=" * 60)
    print("ZS Parser Format Consistency Test")
    print("=" * 60)
    
    # Test with available NDJSON files
    test_files = [
        Path('data/zeeschuimer-export-facebook.com-2025-07-28T041835.ndjson'),
        # Path('data/zeeschuimer-export-facebook.com-2025-07-28T092148.ndjson'),
        Path('data/tik1.json'),
        Path('data/newtik.json'),
        # Path('data/自備印泥-search-facebook.ndjson'),
        Path('data/隱形墨水-鬼針草聯隊.ndjson')
    ]
    
    existing_files = [f for f in test_files if f.exists()]
    
    if not existing_files:
        print("ErrorNo test files found. Please ensure test data files are available.")
        return False
    
    all_passed = True
    
    for test_file in existing_files:
        print(f"\n{'='*40}")
        success = test_format_consistency(test_file)
        all_passed = all_passed and success
        print(f"{'='*40}")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("ALL TESTS PASSED: Format consistency verified")
    else:
        print("SOME TESTS FAILED: Format consistency issues detected")
    print(f"{'='*60}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)