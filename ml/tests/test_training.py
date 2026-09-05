import os
import csv
import json
import pytest
import tempfile
import sys

# Add ml/training to path to import generate_synthetic_data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../training')))
from generate_synthetic_data import generate_dataset

def test_deterministic_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        out1 = os.path.join(tmpdir, "ds1.csv")
        out2 = os.path.join(tmpdir, "ds2.csv")
        
        generate_dataset(seed=42, num_samples=10, output_path=out1)
        generate_dataset(seed=42, num_samples=10, output_path=out2)
        
        with open(out1, 'r') as f1, open(out2, 'r') as f2:
            assert f1.read() == f2.read()
            
def test_configurable_size():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "ds.csv")
        generate_dataset(seed=1, num_samples=50, output_path=out)
        
        with open(out, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 51 # 50 samples + header
