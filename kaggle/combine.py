#!/usr/bin/env python3
"""
Combine multiple probability CSV files, keeping only one entry per game ID.
Warns if conflicting probabilities are found for the same game ID.

To use: Modify the FILES list below with the paths to your CSV files.
"""

import csv
import sys
import os
from collections import defaultdict

# ============================================================
# CONFIGURATION - Modify this list with your file paths
# ============================================================
FILES = [
    "predictions/men/probabilities_2026.csv",
    "predictions/women/probabilities_2026_1.csv",
    "predictions/women/probabilities_2026_2.csv",
    "predictions/women/probabilities_2026_3.csv",
    "predictions/women/probabilities_2026_4.csv",
    # Add more files as needed
]

OUTPUT_FILE = "predictions/all/probabilities_2026.csv"  # Set to None to print to stdout
# ============================================================

def combine_probability_files(file_paths, output_file=None):
    """
    Combine multiple probability CSV files.
    
    Args:
        file_paths: List of paths to CSV files to combine
        output_file: Optional output file path (if None, prints to stdout)
    
    Returns:
        Dictionary of combined games (ID -> probability)
    """
    combined_games = {}  # ID -> probability
    conflicts = defaultdict(list)  # ID -> list of (file, probability)
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            continue
            
        print(f"Processing: {file_path}", file=sys.stderr)
        
        try:
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Verify header
                if reader.fieldnames != ['ID', 'Pred']:
                    print(f"Warning: {file_path} has unexpected headers: {reader.fieldnames}", file=sys.stderr)
                
                line_num = 1  # Start at 1 for header
                for row in reader:
                    line_num += 1
                    game_id = row.get('ID', '').strip()
                    
                    # Skip empty IDs
                    if not game_id:
                        continue
                    
                    try:
                        prob = float(row.get('Pred', 0))
                    except (ValueError, TypeError):
                        print(f"Warning: {file_path}:{line_num} - Invalid probability value: {row.get('Pred')}", file=sys.stderr)
                        continue
                    
                    # Check for conflicts
                    if game_id in combined_games:
                        existing_prob = combined_games[game_id]
                        if abs(existing_prob - prob) > 0.0001:  # Small tolerance for floating point
                            conflicts[game_id].append((file_path, prob))
                    else:
                        combined_games[game_id] = prob
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            continue
    
    # Log conflicts
    if conflicts:
        print("\n" + "="*60, file=sys.stderr)
        print("WARNING: Found conflicting probabilities for the same game ID:", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        for game_id, conflict_list in conflicts.items():
            print(f"\nGame ID: {game_id}", file=sys.stderr)
            print(f"  Original: {combined_games[game_id]:.4f}", file=sys.stderr)
            for file_path, prob in conflict_list:
                print(f"  {file_path}: {prob:.4f}", file=sys.stderr)
        
        print("\n" + "="*60, file=sys.stderr)
        print(f"Total conflicts: {len(conflicts)}", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
    
    # Write output
    if output_file:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Pred'])
            
            # Sort by game ID for consistent output
            for game_id in sorted(combined_games.keys()):
                writer.writerow([game_id, f"{combined_games[game_id]:.4f}"])
        
        print(f"\nCombined {len(combined_games)} unique games to: {output_file}", file=sys.stderr)
    else:
        # Print to stdout
        writer = csv.writer(sys.stdout)
        writer.writerow(['ID', 'Pred'])
        for game_id in sorted(combined_games.keys()):
            writer.writerow([game_id, f"{combined_games[game_id]:.4f}"])
    
    return combined_games

# Run the combination
if __name__ == "__main__":
    combine_probability_files(FILES, OUTPUT_FILE)