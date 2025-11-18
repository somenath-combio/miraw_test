# Usage Examples and Recipes

This guide provides practical examples for different use cases of the CTS dataset generator.

---

## 🚀 Basic Usage

### Example 1: Simple Run with Excel File

**Scenario:** You have one Excel file with all your data.

```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output dataset.tsv
```

**Expected:**
- Uses default parameters (window=30, step=5, top-k-pos=10, top-k-neg=5)
- Creates balanced dataset
- Outputs TSV file ready for training

---

### Example 2: Using Separate Files

**Scenario:** You have separate TSV and FASTA files.

**Your files:**
```
positive_pairs.tsv      # miRNA_ID, gene_ID
mirna_sequences.fa      # FASTA with miRNA sequences
utr_sequences.fa        # FASTA with 3'UTR sequences
```

**Command:**
```bash
python generate_cts_dataset.py \
    --positive-pairs positive_pairs.tsv \
    --mirna-fasta mirna_sequences.fa \
    --utr-fasta utr_sequences.fa \
    --output dataset.tsv
```

---

### Example 3: Test Run with Example Data

**Scenario:** You want to test the pipeline before using your real data.

```bash
# First, generate example data (if not done already)
python example_data/create_example_data.py

# Run pipeline on example data
python generate_cts_dataset.py \
    --excel example_data/example_mirna_mrna_pairs.xlsx \
    --output test_output.tsv

# Check the output
head test_output.tsv
wc -l test_output.tsv
```

**Expected output:**
```
26 lines (1 header + 25 CTS)
15 positive CTS
10 negative CTS
```

---

## ⚙️ Parameter Tuning

### Example 4: More Sites Per Pair

**Scenario:** You want more training examples per miRNA-gene pair.

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv \
    --top-k-positive 20 \
    --top-k-negative 20
```

**Result:**
```
Input: 100 positive pairs
Output:
  - 2,000 positive CTS (100 × 20)
  - 2,000 negative CTS (100 × 20)
  - Total: 4,000 CTS
```

**Use when:**
- You have a small number of validated pairs
- You want more training data
- You have sufficient 3'UTR length (>500 nt)

---

### Example 5: Balanced Dataset

**Scenario:** You want exactly equal positive and negative CTS.

**Strategy 1: Match top-k values**
```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output balanced_dataset.tsv \
    --top-k-positive 10 \
    --top-k-negative 10 \
    --negative-ratio 1.0
```

**Strategy 2: Adjust negative ratio**
```bash
# If you know you get 1000 positive CTS
# And you want 1000 negative CTS
# But each negative pair gives 5 sites
# You need 200 negative pairs
# If you have 100 positive pairs: ratio = 200/100 = 2.0

python generate_cts_dataset.py \
    --excel data.xlsx \
    --output balanced_dataset.tsv \
    --top-k-positive 10 \
    --top-k-negative 5 \
    --negative-ratio 2.0
```

---

### Example 6: Strict Hard Negatives

**Scenario:** You want only very stable hard negatives.

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output strict_negatives.tsv \
    --delta-g-threshold -15.0 \
    --top-k-negative 3
```

**Effect:**
- Only sites with ΔG ≤ -15 kcal/mol (very stable)
- Fewer negative CTS (stricter threshold)
- Harder challenge for the model

**Use when:**
- You want to avoid easy negatives
- Your positives have very negative ΔG
- You're building a challenging benchmark

---

### Example 7: Relaxed Negatives

**Scenario:** You're not getting enough negative CTS.

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output relaxed_negatives.tsv \
    --delta-g-threshold -8.0 \
    --top-k-negative 10
```

**Effect:**
- More sites pass threshold (ΔG ≤ -8 kcal/mol)
- More negative CTS generated
- Easier negatives (but still somewhat stable)

**Use when:**
- Getting warning: "Generated 0 negative CTS"
- Your sequences are short
- You need more training data

---

### Example 8: More Negatives Than Positives

**Scenario:** Imbalanced data to test robustness.

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output imbalanced_dataset.tsv \
    --negative-ratio 3.0
```

**Result:**
```
Input: 100 positive pairs
Output:
  - 100 positive pairs
  - 300 negative pairs (100 × 3.0)
```

**Use when:**
- Real-world reflects more negatives
- Testing model robustness to imbalance
- Studying false positive rates

---

### Example 9: Small Window Size

**Scenario:** Focusing on shorter binding sites (e.g., seed region).

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output small_window.tsv \
    --window-size 20 \
    --flanking-nt 5
```

**Effect:**
- 20-nt core binding site (vs. default 30-nt)
- Still has 5-nt flanking (total 30nt)
- Faster processing
- May capture seed-focused binding

---

### Example 10: Fine-Grained Scanning

**Scenario:** More thorough scanning with smaller step size.

```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output fine_scan.tsv \
    --step-size 1 \
    --top-k-positive 5
```

**Effect:**
- Slides window by 1 nt (vs. default 5 nt)
- More candidate sites evaluated
- Longer processing time
- May find more optimal sites

**Warning:** Much slower! Only use if needed.

---

## 🎯 Application-Specific Examples

### Example 11: miRNA Target Prediction Training

**Goal:** Train a binary classifier for target prediction.

```bash
# Generate balanced dataset
python generate_cts_dataset.py \
    --excel validated_targets.xlsx \
    --output training_data.tsv \
    --top-k-positive 10 \
    --top-k-negative 10 \
    --delta-g-threshold -12.0

# Then split in Python:
python << 'EOF'
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv('training_data.tsv', sep='\t')

# Stratified split
train, temp = train_test_split(df, test_size=0.3, stratify=df['label'], random_state=42)
val, test = train_test_split(temp, test_size=0.5, stratify=temp['label'], random_state=42)

print(f"Train: {len(train)} ({sum(train['label'])}/{len(train)-sum(train['label'])})")
print(f"Val: {len(val)} ({sum(val['label'])}/{len(val)-sum(val['label'])})")
print(f"Test: {len(test)} ({sum(test['label'])}/{len(test)-sum(test['label'])})")

train.to_csv('train.tsv', sep='\t', index=False)
val.to_csv('val.tsv', sep='\t', index=False)
test.to_csv('test.tsv', sep='\t', index=False)
EOF
```

---

### Example 12: Benchmark Dataset Creation

**Goal:** Create a standardized benchmark for comparing methods.

```bash
# Strict parameters for reproducibility
python generate_cts_dataset.py \
    --excel benchmark_pairs.xlsx \
    --output benchmark_dataset_v1.tsv \
    --window-size 30 \
    --step-size 5 \
    --flanking-nt 5 \
    --top-k-positive 10 \
    --top-k-negative 10 \
    --delta-g-threshold -12.0 \
    --negative-ratio 1.0

# Document parameters
cat > benchmark_README.txt << 'EOF'
Benchmark Dataset v1.0
Date: 2025-11-18
Generator version: 1.0

Parameters:
- Window size: 30 nt
- Step size: 5 nt
- Flanking: 5 nt
- Top-K positive: 10
- Top-K negative: 10
- ΔG threshold: -12.0 kcal/mol
- Negative ratio: 1.0

Source: [Your source]
Citation: [Your citation]
EOF
```

---

### Example 13: Feature Engineering Dataset

**Goal:** Generate dataset with additional features for analysis.

```bash
# Generate base dataset
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output base_dataset.tsv \
    --top-k-positive 15

# Add features in Python
python << 'EOF'
import pandas as pd

df = pd.read_csv('base_dataset.tsv', sep='\t')

# Add GC content
def gc_content(seq):
    seq = seq.replace('N', '')
    if len(seq) == 0:
        return 0
    gc = seq.count('G') + seq.count('C')
    return gc / len(seq)

df['miRNA_GC'] = df['miRNA_seq'].apply(gc_content)
df['MBS_GC'] = df['MBS_seq'].apply(gc_content)

# Add sequence length (without N's)
df['MBS_length'] = df['MBS_seq'].apply(lambda x: len(x.replace('N', '')))

# Add energy per nucleotide
df['deltaG_per_nt'] = df['deltaG'] / df['miRNA_seq'].str.len()

# Save enhanced dataset
df.to_csv('enhanced_dataset.tsv', sep='\t', index=False)

print("Added features:")
print("  - miRNA_GC: GC content of miRNA")
print("  - MBS_GC: GC content of MBS")
print("  - MBS_length: Effective MBS length")
print("  - deltaG_per_nt: Energy normalized by length")
EOF
```

---

### Example 14: Multi-Species Dataset

**Scenario:** You have data from multiple species.

```bash
# Generate datasets separately
python generate_cts_dataset.py \
    --excel human_data.xlsx \
    --output human_dataset.tsv

python generate_cts_dataset.py \
    --excel mouse_data.xlsx \
    --output mouse_dataset.tsv

# Combine with species labels
python << 'EOF'
import pandas as pd

human = pd.read_csv('human_dataset.tsv', sep='\t')
mouse = pd.read_csv('mouse_dataset.tsv', sep='\t')

human['species'] = 'human'
mouse['species'] = 'mouse'

combined = pd.concat([human, mouse], ignore_index=True)
combined.to_csv('multi_species_dataset.tsv', sep='\t', index=False)

print(f"Combined dataset: {len(combined)} CTS")
print(f"  Human: {len(human)}")
print(f"  Mouse: {len(mouse)}")
EOF
```

---

## 🔍 Debugging and Validation

### Example 15: Dry Run (Check Input Data)

**Scenario:** You want to validate your input before running the full pipeline.

```bash
# Run with minimal sites to check format
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output test_run.tsv \
    --top-k-positive 1 \
    --top-k-negative 1

# Check output
head -20 test_run.tsv
```

**Check for:**
- All columns present?
- Sequences look correct?
- Energies in reasonable range (-5 to -30)?
- Labels are 0 and 1?
- No strange characters?

---

### Example 16: Verbose Output

**Scenario:** Pipeline is failing and you need to debug.

```bash
# Run with Python in verbose mode
python -u generate_cts_dataset.py \
    --excel data.xlsx \
    --output debug_output.tsv \
    2>&1 | tee pipeline.log

# Check log
cat pipeline.log | grep -i "error"
cat pipeline.log | grep -i "warning"
```

---

### Example 17: Performance Testing

**Scenario:** You want to know how long processing will take.

```bash
# Time the pipeline
time python generate_cts_dataset.py \
    --excel data.xlsx \
    --output timed_output.tsv

# Or with more details
/usr/bin/time -v python generate_cts_dataset.py \
    --excel data.xlsx \
    --output timed_output.tsv
```

---

## 📊 Dataset Analysis

### Example 18: Statistics Report

**Scenario:** Generate detailed statistics after dataset creation.

```bash
# Generate dataset
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv

# Analyze in Python
python << 'EOF'
import pandas as pd
import numpy as np

df = pd.read_csv('dataset.tsv', sep='\t')

print("=" * 60)
print("DATASET ANALYSIS")
print("=" * 60)

print("\n1. Basic Statistics:")
print(f"   Total CTS: {len(df)}")
print(f"   Positive: {sum(df['label'] == 1)} ({100*sum(df['label']==1)/len(df):.1f}%)")
print(f"   Negative: {sum(df['label'] == 0)} ({100*sum(df['label']==0)/len(df):.1f}%)")

print("\n2. Unique Entities:")
print(f"   Unique miRNAs: {df['miRNA_ID'].nunique()}")
print(f"   Unique genes: {df['gene_ID'].nunique()}")
print(f"   Unique miRNA-gene pairs: {df.groupby(['miRNA_ID', 'gene_ID']).ngroups}")

print("\n3. Energy Distribution:")
pos = df[df['label'] == 1]['deltaG']
neg = df[df['label'] == 0]['deltaG']
print(f"   Positive ΔG: {pos.mean():.2f} ± {pos.std():.2f} kcal/mol")
print(f"   Negative ΔG: {neg.mean():.2f} ± {neg.std():.2f} kcal/mol")
print(f"   Overlap: {max(pos.min(), neg.min()):.2f} to {min(pos.max(), neg.max()):.2f}")

print("\n4. Sequence Lengths:")
print(f"   miRNA length: {df['miRNA_seq'].str.len().mean():.1f} ± {df['miRNA_seq'].str.len().std():.1f} nt")
print(f"   MBS length: {df['MBS_seq'].str.len().mean():.1f} nt")

print("\n5. Source Distribution:")
print(df['source'].value_counts())

print("\n6. CTS per Pair:")
cts_per_pair = df.groupby(['miRNA_ID', 'gene_ID', 'label']).size()
print(f"   Positive pairs: mean={cts_per_pair[cts_per_pair.index.get_level_values('label')==1].mean():.1f} CTS/pair")
print(f"   Negative pairs: mean={cts_per_pair[cts_per_pair.index.get_level_values('label')==0].mean():.1f} CTS/pair")
EOF
```

---

### Example 19: Quality Control Checks

```python
# Save as: qc_check.py
import pandas as pd
import sys

df = pd.read_csv('dataset.tsv', sep='\t')

errors = []

# Check 1: No missing values (except N in sequences)
if df.drop(columns=['MBS_seq']).isnull().any().any():
    errors.append("ERROR: Missing values detected")

# Check 2: Labels are only 0 or 1
if not df['label'].isin([0, 1]).all():
    errors.append("ERROR: Invalid labels (must be 0 or 1)")

# Check 3: Energy values are negative
if (df['deltaG'] > 0).any():
    errors.append("ERROR: Positive ΔG values detected")

# Check 4: Reasonable energy range
if (df['deltaG'] < -50).any():
    errors.append("WARNING: Very negative ΔG values (< -50)")

# Check 5: Sequence lengths
if not df['MBS_seq'].str.len().between(35, 45).all():
    errors.append("WARNING: Unexpected MBS sequence lengths")

# Check 6: Balance
pos_count = sum(df['label'] == 1)
neg_count = sum(df['label'] == 0)
ratio = neg_count / pos_count if pos_count > 0 else 0

if ratio < 0.3 or ratio > 3.0:
    errors.append(f"WARNING: Imbalanced dataset (neg/pos = {ratio:.2f})")

# Report
if errors:
    print("Quality Control Report:")
    for err in errors:
        print(f"  {err}")
    sys.exit(1)
else:
    print("✅ All quality checks passed!")
    sys.exit(0)
```

```bash
# Run QC
python qc_check.py
```

---

## 🔄 Batch Processing

### Example 20: Processing Multiple Datasets

```bash
#!/bin/bash
# Save as: batch_process.sh

# List of input files
FILES=(
    "dataset1.xlsx"
    "dataset2.xlsx"
    "dataset3.xlsx"
)

# Process each
for file in "${FILES[@]}"; do
    basename=$(basename "$file" .xlsx)
    echo "Processing $basename..."

    python generate_cts_dataset.py \
        --excel "$file" \
        --output "${basename}_output.tsv" \
        --top-k-positive 10 \
        --top-k-negative 10

    echo "Done: ${basename}_output.tsv"
    echo ""
done

echo "All datasets processed!"
```

```bash
chmod +x batch_process.sh
./batch_process.sh
```

---

## 🎨 Advanced Recipes

### Example 21: Custom Configuration File

**Scenario:** You want to save and reuse parameter sets.

```bash
# Create config file
cat > config_high_quality.txt << 'EOF'
--window-size 30
--step-size 5
--flanking-nt 5
--top-k-positive 15
--top-k-negative 15
--delta-g-threshold -15.0
--negative-ratio 1.0
EOF

# Use config
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv \
    $(cat config_high_quality.txt)
```

---

### Example 22: Pipeline Integration

**Scenario:** Integrate with existing workflow.

```bash
#!/bin/bash
# Complete workflow

# 1. Download data (your method)
# wget http://example.com/data.xlsx

# 2. Generate CTS dataset
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output raw_dataset.tsv

# 3. Quality control
python qc_check.py

# 4. Add features
python add_features.py

# 5. Split data
python split_train_test.py

# 6. Train model
python train_model.py --train train.tsv --val val.tsv

# 7. Evaluate
python evaluate_model.py --test test.tsv --model model.pkl

echo "Pipeline complete!"
```

---

## 📌 Quick Reference

### Most Common Commands

```bash
# Basic
python generate_cts_dataset.py --excel data.xlsx --output dataset.tsv

# Balanced
python generate_cts_dataset.py --excel data.xlsx --output dataset.tsv \
    --top-k-positive 10 --top-k-negative 10

# More negatives
python generate_cts_dataset.py --excel data.xlsx --output dataset.tsv \
    --negative-ratio 2.0

# Strict negatives
python generate_cts_dataset.py --excel data.xlsx --output dataset.tsv \
    --delta-g-threshold -15.0

# Quick test
python generate_cts_dataset.py \
    --excel example_data/example_mirna_mrna_pairs.xlsx \
    --output test.tsv
```

---

## 💡 Tips and Tricks

### Tip 1: Start Small
Always test with `--top-k-positive 3 --top-k-negative 2` first!

### Tip 2: Check Statistics
Review the statistics output to ensure your dataset is reasonable.

### Tip 3: Balance Matters
Aim for 0.5 to 2.0 negative/positive ratio for best model performance.

### Tip 4: Energy Threshold
If no negatives: increase threshold (e.g., -8.0)
If too many negatives: decrease threshold (e.g., -15.0)

### Tip 5: Save Commands
Document the exact command used to generate each dataset!

---

**Need more examples?** Check:
- `README_CTS_DATASET.md` - Complete documentation
- `QUICKSTART.md` - Quick start guide
- `example_data/` - Working examples
