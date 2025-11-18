# miRNA-mRNA CTS Dataset Generator

A comprehensive pipeline for generating miRNA-mRNA Candidate Target Sites (CTS) training datasets with ViennaRNA binding energy calculations.

## Overview

This tool processes validated miRNA-mRNA pairs and generates a complete training dataset including:

- **Positive CTS**: Actual 30-nt binding sites from validated target pairs
- **Negative pairs**: Non-functional miRNA-gene combinations
- **Hard negative CTS**: Thermodynamically stable but non-functional binding sites
- **ViennaRNA ΔG**: Duplex binding energy for all sites

## Features

- ✅ Two approaches for positive CTS extraction:
  - CLIP-based (preferred, if data available)
  - Sliding window (fallback)
- ✅ Automatic hard negative generation
- ✅ ViennaRNA duplex energy calculation
- ✅ Configurable parameters (window size, thresholds, etc.)
- ✅ Progress tracking with tqdm
- ✅ Comprehensive statistics output

## Installation

### 1. Install ViennaRNA (Required)

ViennaRNA must be installed system-wide before installing Python dependencies.

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install vienna-rna
```

#### macOS (with Homebrew):
```bash
brew install viennarna
```

#### From source:
```bash
wget https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_5_x/ViennaRNA-2.5.1.tar.gz
tar -zxvf ViennaRNA-2.5.1.tar.gz
cd ViennaRNA-2.5.1
./configure --with-python3
make
sudo make install
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install biopython pandas numpy openpyxl tqdm
pip install ViennaRNA  # Only after system ViennaRNA is installed
```

### 3. Verify Installation

```bash
python -c "import RNA; print(RNA.version())"
```

## Usage

### Option 1: Using Excel File (Recommended)

If you have a single Excel file with all data:

```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output miraw_dataset.tsv
```

**Excel file format:**
```
miRNA_name     | miRNA_sequence    | mRNA_name | mRNA_sequence
---------------|-------------------|-----------|------------------
hsa-miR-21-5p  | UAGCUUAUCAGAC...  | TP53      | AUGCUAGCUA...
hsa-miR-155    | UUAAUGCUAA...     | PTGS2     | GCUAGCUAGC...
```

### Option 2: Using Separate Files

If you have separate TSV and FASTA files:

```bash
python generate_cts_dataset.py \
    --positive-pairs positive_pairs.tsv \
    --mirna-fasta mirna_sequences.fa \
    --utr-fasta utr_sequences.fa \
    --output miraw_dataset.tsv
```

### Option 3: With Custom Parameters

```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output miraw_dataset.tsv \
    --top-k-positive 15 \
    --top-k-negative 10 \
    --delta-g-threshold -12.0 \
    --negative-ratio 1.5 \
    --window-size 30 \
    --step-size 5
```

## Command-Line Arguments

### Input Files (Required - choose one option):

**Option A: Excel file**
- `--excel FILE`: Excel file with columns: miRNA_name, miRNA_sequence, mRNA_name, mRNA_sequence

**Option B: Separate files**
- `--positive-pairs FILE`: TSV file with columns: miRNA_ID, gene_ID
- `--mirna-fasta FILE`: FASTA file with miRNA sequences
- `--utr-fasta FILE`: FASTA file with 3'UTR sequences

### Output:
- `--output FILE`: Output TSV file (default: miraw_dataset.tsv)

### Parameters:
- `--window-size INT`: MBS window size in nucleotides (default: 30)
- `--step-size INT`: Sliding window step (default: 5)
- `--flanking-nt INT`: Flanking nucleotides for context (default: 5)
- `--delta-g-threshold FLOAT`: ΔG threshold for negative selection (default: -10.0 kcal/mol)
- `--top-k-positive INT`: Max CTS per positive pair (default: 10)
- `--top-k-negative INT`: Max CTS per negative pair (default: 5)
- `--negative-ratio FLOAT`: Negative to positive pair ratio (default: 1.0)
- `--use-clip`: Attempt to use CLIP data (default: False)

## Input File Formats

### Excel File Format
```
miRNA_name     | miRNA_sequence              | mRNA_name | mRNA_sequence
---------------|----------------------------|-----------|------------------
hsa-miR-21-5p  | UAGCUUAUCAGACUGAUGUUGA     | TP53      | AUGCUAGCUA...
hsa-miR-155    | UUAAUGCUAAUCGUGAUAGGGGU   | PTGS2     | GCUAGCUAGC...
```

### Positive Pairs TSV
```
miRNA_ID         gene_ID
hsa-miR-21-5p    TP53
hsa-miR-155      PTGS2
```

### FASTA Files
```
>hsa-miR-21-5p
UAGCUUAUCAGACUGAUGUUGA
>hsa-miR-155
UUAAUGCUAAUCGUGAUAGGGGU
```

## Output Format

The output TSV file contains:

| Column       | Description                                    |
|--------------|------------------------------------------------|
| miRNA_ID     | miRNA identifier                               |
| gene_ID      | Gene/mRNA identifier                           |
| gene_symbol  | Gene symbol (same as gene_ID)                  |
| miRNA_seq    | Full miRNA sequence                            |
| MBS_seq      | MBS sequence with flanking context (40nt)      |
| UTR_position | Start position in UTR                          |
| deltaG       | ViennaRNA binding energy (kcal/mol)            |
| label        | 1 = positive, 0 = negative                     |
| source       | CLIP, sliding_window, or negative              |

### Example Output:
```tsv
miRNA_ID	gene_ID	gene_symbol	miRNA_seq	MBS_seq	UTR_position	deltaG	label	source
hsa-miR-21-5p	TP53	TP53	UAGCUUAUCAGACUGAUGUUGA	UCAACAUCAGUCUGAUAAGCUACGUAG	1523	-15.2	1	sliding_window
hsa-miR-21-5p	TP53	TP53	UAGCUUAUCAGACUGAUGUUGA	GCUAUCAACAUCAGUCUGAUAAGCUAG	1528	-14.8	1	sliding_window
hsa-miR-21-5p	RANDOM1	RANDOM1	UAGCUUAUCAGACUGAUGUUGA	AGCUAGCUAGCUAGCUAGCUAGCUAGC	456	-12.3	0	negative
```

## How It Works

### 1. Positive CTS Extraction

**Approach A (if CLIP data available):**
- Query CLIP peaks for each positive pair
- Slide 30-nt window within CLIP regions (step=5)
- Extract MBS + 5nt flanking context
- Compute ViennaRNA ΔG
- Keep all sites in CLIP regions

**Approach B (fallback or default):**
- Slide 30-nt window across entire 3'UTR (step=5)
- Compute ViennaRNA ΔG for each window
- Keep top K windows with most negative ΔG (default K=10)

### 2. Negative Pair Generation

For each miRNA:
- Identify genes it targets (positive_genes)
- Sample N random genes from non-targets
- Create negative (miRNA, gene) pairs
- Default: N = number of positive genes (1:1 ratio)

### 3. Hard Negative CTS Extraction

For each negative pair:
- Slide 30-nt window across entire 3'UTR (step=5)
- Compute ViennaRNA ΔG
- **Only keep sites with ΔG ≤ threshold** (default: -10 kcal/mol)
- Select top K sites with most negative ΔG (default K=5)

This creates "hard negatives": sequences that look thermodynamically stable but are NOT functional targets.

### 4. ViennaRNA Energy Calculation

Uses ViennaRNA `cofold` to compute RNA duplex minimum free energy:
- Input: `miRNA_sequence&MBS_sequence`
- Output: ΔG in kcal/mol (negative = stable binding)

## Statistics Output

The pipeline prints comprehensive statistics:

```
============================================================
DATASET STATISTICS
============================================================

📊 Pair Statistics:
  Total positive pairs: 150
  Total negative pairs: 150

🎯 CTS Statistics:
  Positive CTS: 1,500
  Negative CTS: 750
  Total CTS: 2,250
  Balance ratio: 0.50

⚡ Positive CTS Energy (ΔG):
  Mean: -15.3 kcal/mol
  Median: -14.8 kcal/mol
  Min: -25.2 kcal/mol
  Max: -8.1 kcal/mol

⚡ Negative CTS Energy (ΔG):
  Mean: -12.1 kcal/mol
  Median: -11.5 kcal/mol
  Min: -18.7 kcal/mol
  Max: -10.0 kcal/mol

📍 Positive CTS Sources:
  sliding_window: 1,500
============================================================
```

## Tips and Best Practices

### 1. Balance Your Dataset
- Aim for roughly equal positive and negative CTS counts
- Adjust `--negative-ratio` and `--top-k-negative` accordingly
- Example: If you get 1,500 positive CTS, target ~1,500 negative CTS

### 2. Hard Negative Threshold
- Default `-10.0 kcal/mol` is a good starting point
- More negative = stricter (harder negatives, fewer sites)
- Less negative = looser (easier negatives, more sites)
- Recommended range: -8.0 to -15.0 kcal/mol

### 3. Window Parameters
- Window size: 30nt is standard for miRNA binding sites
- Step size: 5nt provides good coverage without too much overlap
- Smaller step = more candidates but slower and more redundant

### 4. Handling Missing Data
- The pipeline automatically skips pairs with missing sequences
- Check logs for warnings about skipped pairs
- Ensure your FASTA IDs match your pair file IDs

### 5. Memory and Performance
- For large datasets (>1000 genes), processing may take several hours
- Progress bars show real-time status
- Consider running on a server for very large datasets

## Troubleshooting

### ViennaRNA Import Error
```
ImportError: No module named RNA
```
**Solution**: Install ViennaRNA system-wide first, then `pip install ViennaRNA`

### Missing Sequences
```
WARNING: miRNA hsa-miR-21 not found in sequences
```
**Solution**: Ensure FASTA IDs exactly match the IDs in your pairs file (case-sensitive)

### Memory Issues
```
MemoryError: ...
```
**Solution**:
- Process in batches
- Reduce `--top-k-positive` and `--top-k-negative`
- Use a machine with more RAM

### No Negative CTS Generated
```
Generated 0 negative CTS
```
**Solution**:
- Lower `--delta-g-threshold` (e.g., from -10 to -8)
- Increase `--top-k-negative`
- Check that your UTR sequences are long enough

## Examples

### Example 1: Quick Test Run
```bash
python generate_cts_dataset.py \
    --excel test_data.xlsx \
    --output test_output.tsv \
    --top-k-positive 5 \
    --top-k-negative 3
```

### Example 2: Balanced Dataset
```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output balanced_dataset.tsv \
    --negative-ratio 1.0 \
    --top-k-positive 10 \
    --top-k-negative 10
```

### Example 3: Strict Hard Negatives
```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output strict_dataset.tsv \
    --delta-g-threshold -15.0 \
    --top-k-negative 3
```

## Citation

If you use this tool in your research, please cite:

```
[Your paper citation here]
```

Based on the miRAW methodology:
- miRAW: A deep learning-based approach to predict microRNA targets by analyzing whole microRNA transcripts
- [Add relevant citations]

## License

[Add your license here]

## Contact

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [your email]

## Acknowledgments

- ViennaRNA Package for RNA structure prediction
- miRAW authors for the methodology
- BioPython community
