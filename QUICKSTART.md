# Quick Start Guide: miRNA-mRNA CTS Dataset Generator

## TL;DR

Generate a miRNA-mRNA training dataset with binding sites and energy calculations:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install ViennaRNA (required for real energy calculations)
# Ubuntu/Debian:
sudo apt-get install vienna-rna

# macOS:
brew install viennarna

# 3. Run the pipeline
python generate_cts_dataset.py --excel your_data.xlsx --output dataset.tsv
```

## What You Get

A TSV file with:
- ✅ Positive binding sites from validated miRNA-target pairs
- ✅ Negative binding sites (hard negatives)
- ✅ ViennaRNA ΔG binding energies for all sites
- ✅ Ready for machine learning training

## Example Output

```tsv
miRNA_ID         gene_ID  miRNA_seq              MBS_seq                    deltaG   label
hsa-miR-21-5p    TP53     UAGCUUAUCAGACUGAUGUUGA UCAACAUCAGUCUGAUAAGCUA...  -15.2    1
hsa-miR-21-5p    RANDOM1  UAGCUUAUCAGACUGAUGUUGA AGCUAGCUAGCUAGCUAGCUAG...  -12.3    0
```

- **label=1**: Positive (validated target)
- **label=0**: Negative (non-functional)
- **deltaG**: More negative = stronger binding

## Your Input Data Format

### Option 1: Excel File (Easiest)

Create an Excel file (`mirna_mrna_data.xlsx`) with columns:

| miRNA_name    | miRNA_sequence         | mRNA_name | mRNA_sequence       |
|---------------|------------------------|-----------|---------------------|
| hsa-miR-21-5p | UAGCUUAUCAGACUGAUGUUGA | TP53      | AUGCUAGCUA...       |
| hsa-miR-155   | UUAAUGCUAA...          | PTGS2     | GCUAGCUAGC...       |

Then run:
```bash
python generate_cts_dataset.py --excel mirna_mrna_data.xlsx --output dataset.tsv
```

### Option 2: Separate Files

If you have separate TSV and FASTA files:

**positive_pairs.tsv:**
```
miRNA_ID         mRNA_name
hsa-miR-21-5p    TP53
hsa-miR-155      PTGS2
```

**mirna_sequences.fa:**
```
>hsa-miR-21-5p
UAGCUUAUCAGACUGAUGUUGA
>hsa-miR-155
UUAAUGCUAAUCGUGAUAGGGGU
```

**utr_sequences.fa:**
```
>TP53
AUGCUAGCUA...
>PTGS2
GCUAGCUAGC...
```

Run:
```bash
python generate_cts_dataset.py \
    --positive-pairs positive_pairs.tsv \
    --mirna-fasta mirna_sequences.fa \
    --utr-fasta utr_sequences.fa \
    --output dataset.tsv
```

## How It Works (Simple Explanation)

### Step 1: Extract Positive Sites
For each validated miRNA-target pair:
- Slide a 30-nucleotide window across the mRNA 3'UTR
- Calculate binding energy (ΔG) for each window
- Keep the top 10 strongest binding sites

### Step 2: Generate Negative Pairs
For each miRNA:
- Find genes it does NOT target
- Sample random non-target genes
- Create negative miRNA-gene pairs

### Step 3: Extract Hard Negative Sites
For each negative pair:
- Slide window across mRNA 3'UTR
- Only keep sites with strong binding energy (ΔG ≤ -10 kcal/mol)
- These are "hard negatives": they look like they should bind but don't

### Why Hard Negatives?
They make the model smarter! Instead of learning "strong binding = target", it learns the subtle differences between functional and non-functional sites.

## Customization

### Want More Sites Per Pair?
```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv \
    --top-k-positive 20 \    # More positive sites
    --top-k-negative 10      # More negative sites
```

### Want Stricter Negatives?
```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv \
    --delta-g-threshold -15.0  # Only very stable duplexes
```

### Want More Negatives Than Positives?
```bash
python generate_cts_dataset.py \
    --excel data.xlsx \
    --output dataset.tsv \
    --negative-ratio 2.0  # 2x more negative pairs than positive
```

## Testing with Example Data

We provide example data to test the pipeline:

```bash
# Generate example data (already done if you cloned the repo)
python example_data/create_example_data.py

# Run pipeline on example data
python generate_cts_dataset.py \
    --excel example_data/example_mirna_mrna_pairs.xlsx \
    --output test_output.tsv

# Check output
head test_output.tsv
```

## Understanding the Statistics

After running, you'll see:

```
📊 Pair Statistics:
  Total positive pairs: 150
  Total negative pairs: 150

🎯 CTS Statistics:
  Positive CTS: 1,500        # 150 pairs × 10 sites each
  Negative CTS: 750          # 150 pairs × 5 sites each
  Balance ratio: 0.50        # Neg/Pos ratio

⚡ Positive CTS Energy (ΔG):
  Mean: -15.3 kcal/mol      # Average binding strength
  Min: -25.2 kcal/mol       # Strongest site
```

### What's Good?
- **Balance ratio** between 0.5-2.0 (not too imbalanced)
- **Positive mean ΔG** around -12 to -18 kcal/mol (strong binding)
- **Negative mean ΔG** less negative than positive (weaker binding)

## Troubleshooting

### "No module named RNA"
Install ViennaRNA system-wide first:
```bash
sudo apt-get install vienna-rna
pip install ViennaRNA
```

### "No negative CTS generated"
Your threshold is too strict. Try:
```bash
--delta-g-threshold -8.0  # Looser threshold
```

### Takes too long
Reduce the number of sites:
```bash
--top-k-positive 5 --top-k-negative 3
```

## Next Steps

Once you have your dataset:

1. **Split into train/val/test:**
   ```python
   from sklearn.model_selection import train_test_split
   train, temp = train_test_split(data, test_size=0.3)
   val, test = train_test_split(temp, test_size=0.5)
   ```

2. **Extract features:**
   - Use miRAW's CNN architecture
   - Or extract custom features (k-mers, structure, etc.)

3. **Train your model:**
   - Binary classification (target vs. non-target)
   - Use deltaG as an additional feature

## Need Help?

- Check `README_CTS_DATASET.md` for detailed documentation
- Review the example data in `example_data/`
- Open an issue on GitHub

## Citation

If you use this tool, please cite:
- [Your paper]
- ViennaRNA: Lorenz et al., 2011
- miRAW methodology: [miRAW paper]
