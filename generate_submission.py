"""
Generate canonical submission.jsonl from expanded/test_pairs.json
Iterates over all 30 test pairs, loads the category, merchant, trigger, and customer contexts,
runs VeraComposer, and outputs submission.jsonl.
"""

import json
from pathlib import Path
import sys
import os

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).parent))
from composer import VeraComposer

def generate_submission(expanded_dir: Path, output_file: Path):
    composer = VeraComposer()
    pairs_file = expanded_dir / "test_pairs.json"
    
    if not pairs_file.exists():
        print(f"Error: {pairs_file} not found. Run generate_dataset.py first.")
        sys.exit(1)
        
    with open(pairs_file, "r", encoding="utf-8") as f:
        test_pairs = json.load(f).get("pairs", [])

    submission_lines = []
    
    for pair in test_pairs:
        test_id = pair["test_id"]
        trg_id = pair["trigger_id"]
        merchant_id = pair["merchant_id"]
        customer_id = pair.get("customer_id")
        
        # Load trigger
        trg_file = expanded_dir / "triggers" / f"{trg_id}.json"
        if not trg_file.exists():
            # Try searching in triggers/
            trg_files = list((expanded_dir / "triggers").glob(f"*{trg_id}*.json"))
            trg_file = trg_files[0] if trg_files else None
            
        trg_data = json.load(open(trg_file, encoding="utf-8")) if (trg_file and trg_file.exists()) else {"id": trg_id, "kind": "generic"}
        
        # Load merchant
        m_file = expanded_dir / "merchants" / f"{merchant_id}.json"
        if not m_file.exists():
            m_files = list((expanded_dir / "merchants").glob(f"*{merchant_id}*.json"))
            m_file = m_files[0] if m_files else None
            
        m_data = json.load(open(m_file, encoding="utf-8")) if (m_file and m_file.exists()) else {"merchant_id": merchant_id, "identity": {"name": merchant_id}}
        
        # Load category
        cat_slug = m_data.get("category_slug", trg_data.get("payload", {}).get("category", "dentists"))
        cat_file = expanded_dir / "categories" / f"{cat_slug}.json"
        cat_data = json.load(open(cat_file, encoding="utf-8")) if cat_file.exists() else {"slug": cat_slug}
        
        # Load customer if present
        cust_data = None
        if customer_id:
            c_file = expanded_dir / "customers" / f"{customer_id}.json"
            if not c_file.exists():
                c_files = list((expanded_dir / "customers").glob(f"*{customer_id}*.json"))
                c_file = c_files[0] if c_files else None
            if c_file and c_file.exists():
                cust_data = json.load(open(c_file, encoding="utf-8"))
                
        # Compose
        composed = composer.compose(cat_data, m_data, trg_data, cust_data)
        
        record = {
            "test_id": test_id,
            "body": composed["body"],
            "cta": composed["cta"],
            "send_as": composed["send_as"],
            "suppression_key": composed["suppression_key"],
            "rationale": composed["rationale"]
        }
        submission_lines.append(json.dumps(record, ensure_ascii=False))
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(submission_lines) + "\n")
        
    print(f"Successfully generated {len(submission_lines)} test pair predictions in {output_file}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    expanded = base_dir / "expanded"
    out_path = Path(__file__).parent / "submission.jsonl"
    generate_submission(expanded, out_path)
