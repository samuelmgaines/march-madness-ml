#!/usr/bin/env python3
"""
Generate a submission file by updating a template with existing predictions.
Uses SampleSubmissionStage2.csv as the source of all possible game IDs.
"""

import csv
import os

# ============================================================
# CONFIGURATION - Modify these paths
# ============================================================
COMBINED_FILE = "predictions/all/probabilities_2026.csv"  # Your combined predictions file
TEMPLATE_FILE = "SampleSubmissionStage2.csv"  # Template with all possible game IDs
OUTPUT_FILE = "predictions/all/submission.csv"  # Output submission file
# ============================================================

def load_template_ids(template_file):
    """Load all game IDs from the template file."""
    template_ids = set()
    
    if not os.path.exists(template_file):
        print(f"Error: Template file not found: {template_file}")
        return template_ids
    
    with open(template_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = row['ID']
            template_ids.add(game_id)
    
    print(f"Loaded {len(template_ids)} game IDs from template")
    return template_ids

def load_predictions(combined_file):
    """Load existing predictions from the combined file."""
    predictions = {}
    
    if not os.path.exists(combined_file):
        print(f"Warning: Combined file not found: {combined_file}")
        return predictions
    
    with open(combined_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = row['ID']
            try:
                pred = float(row['Pred'])
                predictions[game_id] = pred
            except (ValueError, TypeError):
                print(f"Warning: Invalid prediction for {game_id}: {row['Pred']}")
    
    print(f"Loaded {len(predictions)} existing predictions")
    return predictions

def generate_submission(template_file, predictions, output_file):
    """Generate submission file by updating template with predictions."""
    
    # Check for missing games in template
    missing_from_template = []
    for game_id in predictions:
        if game_id not in template_ids:
            missing_from_template.append(game_id)
    
    if missing_from_template:
        print(f"\n⚠️  WARNING: Found {len(missing_from_template)} game IDs in predictions not in template!")
        print("First 10 missing IDs (if any):")
        for game_id in missing_from_template[:10]:
            print(f"  - {game_id}")
        if len(missing_from_template) > 10:
            print(f"  ... and {len(missing_from_template) - 10} more")
    
    # Read template and update with predictions
    updated_count = 0
    kept_template_count = 0
    
    with open(template_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        
        # Write header
        writer.writerow(['ID', 'Pred'])
        
        for row in reader:
            game_id = row['ID']
            
            if game_id in predictions:
                # Use our prediction
                pred = predictions[game_id]
                writer.writerow([game_id, f"{pred:.4f}"])
                updated_count += 1
            else:
                # Keep template's 0.5
                writer.writerow([game_id, row['Pred']])
                kept_template_count += 1
    
    print(f"\nSubmission file generated: {output_file}")
    print(f"Total games in template: {len(template_ids)}")
    print(f"  - Updated with your predictions: {updated_count}")
    print(f"  - Kept template default (0.5): {kept_template_count}")
    print(f"  - Predictions used from combined file: {len(predictions)}")
    print(f"  - Predictions ignored (not in template): {len(missing_from_template)}")

# Run the generation
if __name__ == "__main__":
    # Load template IDs first (to use in warning check)
    template_ids = load_template_ids(TEMPLATE_FILE)
    
    if not template_ids:
        print("Error: No template IDs loaded. Exiting.")
        exit(1)
    
    # Load predictions
    predictions = load_predictions(COMBINED_FILE)
    
    # Generate submission
    generate_submission(TEMPLATE_FILE, predictions, OUTPUT_FILE)