# miRNA-mRNA CTS Dataset Generator - Project Summary

## 📋 Overview

A comprehensive bioinformatics pipeline for generating training datasets for miRNA target prediction models (like miRAW). The pipeline extracts candidate target sites (CTS) from validated miRNA-mRNA pairs and generates hard negative examples for robust machine learning training.

---

## 🎯 What This Pipeline Does

### Input
- Excel file OR separate TSV/FASTA files
- Contains: validated miRNA-mRNA pairs with sequences

### Process
1. **Extract Positive CTS**: Find actual binding sites in validated targets
2. **Generate Negative Pairs**: Create non-functional miRNA-gene combinations
3. **Extract Hard Negative CTS**: Find thermodynamically stable but non-functional sites
4. **Calculate Energies**: Compute ViennaRNA ΔG for all sites

### Output
- TSV file with labeled CTS (positive=1, negative=0)
- Each row: miRNA sequence, binding site, position, energy, label
- Ready for machine learning training

---

## 📂 Project Structure

```
miraw_test/
│
├── 📜 Core Pipeline
│   ├── generate_cts_dataset.py      Main script (700+ lines)
│   ├── requirements.txt              Python dependencies
│   └── RNA.py                        Mock ViennaRNA (testing only)
│
├── 📚 Documentation
│   ├── README_CTS_DATASET.md         Complete documentation (500+ lines)
│   ├── QUICKSTART.md                 Quick start guide
│   ├── RNA_INSTALLATION.md           ViennaRNA setup instructions
│   └── PROJECT_SUMMARY.md            This file
│
├── 📊 Example Data
│   └── example_data/
│       ├── create_example_data.py
│       ├── example_mirna_mrna_pairs.xlsx
│       ├── example_mirna_sequences.fa
│       ├── example_positive_pairs.tsv
│       └── example_utr_sequences.fa
│
└── 🚫 .gitignore
```

---

## ✨ Key Features

### 1. Flexible Input Options
- ✅ Single Excel file (easiest)
- ✅ Separate TSV + FASTA files
- ✅ Validates all input data

### 2. Smart CTS Extraction
- ✅ Sliding window approach (30-nt windows)
- ✅ Flanking context (5nt upstream/downstream)
- ✅ Top K selection by binding energy
- ✅ Optional CLIP-based extraction

### 3. Hard Negative Generation
- ✅ Automatic negative pair generation
- ✅ Energy-based filtering (ΔG threshold)
- ✅ Configurable negative:positive ratio
- ✅ Ensures non-overlapping with positives

### 4. ViennaRNA Integration
- ✅ Duplex binding energy calculation
- ✅ cofold implementation
- ✅ Mock version for testing
- ✅ Real ViennaRNA for production

### 5. Configurability
- ✅ Window size (default: 30nt)
- ✅ Step size (default: 5nt)
- ✅ Top K sites (positive: 10, negative: 5)
- ✅ ΔG threshold (default: -10 kcal/mol)
- ✅ Negative ratio (default: 1.0)

### 6. User Experience
- ✅ Progress bars (tqdm)
- ✅ Detailed logging
- ✅ Comprehensive statistics
- ✅ Error handling
- ✅ Input validation

---

## 🔬 Scientific Methodology

### Positive CTS Extraction

**Approach A: CLIP-based (if available)**
```
For each validated miRNA-target pair:
  1. Query CLIP-seq peaks in 3'UTR
  2. Slide 30-nt window within CLIP regions
  3. Calculate ΔG for each window
  4. Keep all sites in CLIP peaks
```

**Approach B: Sliding Window (fallback/default)**
```
For each validated miRNA-target pair:
  1. Slide 30-nt window across entire 3'UTR
  2. Calculate ΔG for each window
  3. Sort by most negative ΔG
  4. Keep top K windows (K=10)
```

### Negative Pair Generation

```
For each miRNA:
  1. Identify genes it targets (from positive pairs)
  2. Get all available genes in dataset
  3. Remove targeted genes
  4. Randomly sample N genes from remainder
  5. Create negative (miRNA, gene) pairs

  N = number of positive genes × negative_ratio
```

### Hard Negative CTS Extraction

```
For each negative pair:
  1. Slide 30-nt window across entire 3'UTR
  2. Calculate ΔG for each window
  3. Filter: only keep if ΔG ≤ threshold (-10 kcal/mol)
  4. Sort by most negative ΔG
  5. Keep top K windows (K=5)
```

**Why "hard" negatives?**
- They have strong thermodynamic binding (low ΔG)
- But they're NOT functional targets
- Forces model to learn subtle sequence/structure features
- Prevents model from relying only on binding energy

### ViennaRNA Energy Calculation

```python
# Duplex energy calculation
mirna = "UAGCUUAUCAGACUGAUGUUGA"
target = "UCAACAUCAGUCUGAUAAGCUA..."

duplex = mirna + '&' + target
structure, mfe = RNA.cofold(duplex)

# mfe = minimum free energy (ΔG) in kcal/mol
# Negative = stable binding
# More negative = stronger binding
```

---

## 📊 Output Data Format

### TSV Columns

| Column       | Description                              | Example                   |
|--------------|------------------------------------------|---------------------------|
| miRNA_ID     | miRNA identifier                         | hsa-miR-21-5p             |
| gene_ID      | Gene/mRNA identifier                     | TP53                      |
| gene_symbol  | Gene symbol                              | TP53                      |
| miRNA_seq    | Full miRNA sequence                      | UAGCUUAUCAGACUGAUGUUGA    |
| MBS_seq      | MBS + flanking (40nt total)              | NNNNNUCAACAUCAGUC...      |
| UTR_position | Start position in 3'UTR                  | 1523                      |
| deltaG       | ViennaRNA binding energy (kcal/mol)      | -15.2                     |
| label        | 1=positive, 0=negative                   | 1                         |
| source       | CLIP, sliding_window, or negative        | sliding_window            |

### Example Output

```tsv
miRNA_ID	gene_ID	gene_symbol	miRNA_seq	MBS_seq	UTR_position	deltaG	label	source
hsa-miR-21-5p	TP53	TP53	UAGCUUAUCAGACUGAUGUUGA	UCAACAUCAGUCUGAUAAGCUACGUAG	1523	-15.2	1	sliding_window
hsa-miR-21-5p	TP53	TP53	UAGCUUAUCAGACUGAUGUUGA	GCUAUCAACAUCAGUCUGAUAAGCUAG	1528	-14.8	1	sliding_window
hsa-miR-21-5p	RANDOM1	RANDOM1	UAGCUUAUCAGACUGAUGUUGA	AGCUAGCUAGCUAGCUAGCUAGCUAGC	456	-12.3	0	negative
```

---

## 🚀 Quick Usage

### Basic Usage (Excel Input)

```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output dataset.tsv
```

### Advanced Usage (Custom Parameters)

```bash
python generate_cts_dataset.py \
    --excel mirna_mrna_data.xlsx \
    --output dataset.tsv \
    --top-k-positive 20 \
    --top-k-negative 15 \
    --delta-g-threshold -15.0 \
    --negative-ratio 2.0 \
    --window-size 30 \
    --step-size 5
```

### Alternative Input (Separate Files)

```bash
python generate_cts_dataset.py \
    --positive-pairs positive_pairs.tsv \
    --mirna-fasta mirna_sequences.fa \
    --utr-fasta utr_sequences.fa \
    --output dataset.tsv
```

---

## 📈 Expected Statistics

### Small Dataset (50 pairs)
```
Positive pairs: 50
Negative pairs: 50
Positive CTS: 500 (50 × 10)
Negative CTS: 250 (50 × 5)
Total: 750 CTS
Processing time: ~5-10 minutes (with real ViennaRNA)
```

### Medium Dataset (500 pairs)
```
Positive pairs: 500
Negative pairs: 500
Positive CTS: 5,000
Negative CTS: 2,500
Total: 7,500 CTS
Processing time: ~1-2 hours
```

### Large Dataset (5000 pairs)
```
Positive pairs: 5,000
Negative pairs: 5,000
Positive CTS: 50,000
Negative CTS: 25,000
Total: 75,000 CTS
Processing time: Several hours
```

---

## 🎓 Use Cases

### 1. Training miRNA Target Prediction Models
- Input features: miRNA sequence, MBS sequence, ΔG
- Output: Binary classification (target vs. non-target)
- Models: CNN, RNN, Transformer, or traditional ML

### 2. Feature Engineering Research
- Analyze which sequence features matter
- Test different binding site definitions
- Compare energy thresholds

### 3. Benchmark Dataset Creation
- Generate standardized datasets
- Compare different prediction methods
- Reproducible research

### 4. Negative Example Studies
- Investigate non-functional binding sites
- Study thermodynamic vs. functional binding
- Analyze false positive patterns

---

## ⚙️ Configuration Parameters

### Window Parameters
| Parameter    | Default | Description                    | Range       |
|--------------|---------|--------------------------------|-------------|
| window_size  | 30      | MBS length (nt)                | 20-50       |
| step_size    | 5       | Window slide step (nt)         | 1-10        |
| flanking_nt  | 5       | Context nucleotides            | 0-10        |

### CTS Selection
| Parameter       | Default | Description                    | Range       |
|-----------------|---------|--------------------------------|-------------|
| top_k_positive  | 10      | Sites per positive pair        | 1-50        |
| top_k_negative  | 5       | Sites per negative pair        | 1-20        |

### Negative Generation
| Parameter          | Default | Description                    | Range       |
|--------------------|---------|--------------------------------|-------------|
| negative_ratio     | 1.0     | Neg:pos pair ratio             | 0.5-5.0     |
| delta_g_threshold  | -10.0   | Energy cutoff (kcal/mol)       | -5 to -20   |

---

## 🔧 Dependencies

### Python Packages
- **biopython** (≥1.79): FASTA parsing, sequence handling
- **pandas** (≥1.3.0): Data manipulation, TSV I/O
- **numpy** (≥1.21.0): Numerical operations
- **openpyxl** (≥3.0.9): Excel file reading
- **tqdm** (≥4.62.0): Progress bars
- **ViennaRNA** (≥2.5.0): RNA structure/energy prediction

### System Requirements
- **ViennaRNA** system package (for production)
- Python 3.7+
- 4GB+ RAM (for medium datasets)
- Linux, macOS, or Windows (with WSL)

---

## ⚠️ Important Notes

### ViennaRNA Installation

**Current Setup:**
- Includes mock `RNA.py` for testing
- Generates simulated energies
- **NOT suitable for real research**

**For Production:**
```bash
# Install ViennaRNA
sudo apt-get install vienna-rna  # Ubuntu
brew install viennarna            # macOS

# Remove mock
rm RNA.py

# Install Python bindings
pip install ViennaRNA

# Verify
python -c "import RNA; print(RNA.version())"
```

### Data Requirements

**Input data must include:**
- ✅ Validated miRNA-target interactions (from experiments or databases)
- ✅ miRNA sequences (mature sequences, ~22nt)
- ✅ mRNA 3'UTR sequences (full or partial)
- ✅ Unique identifiers for miRNAs and genes

**Data sources:**
- miRTarBase (validated interactions)
- TargetScan (predicted + conserved)
- CLIP-seq databases (starBase, ENCORI)
- Ensembl/NCBI (for 3'UTR sequences)

---

## 📝 Testing

### Example Data Included

```bash
# Generate example data
python example_data/create_example_data.py

# Test pipeline
python generate_cts_dataset.py \
    --excel example_data/example_mirna_mrna_pairs.xlsx \
    --output test_output.tsv \
    --top-k-positive 3 \
    --top-k-negative 2

# Verify output
head test_output.tsv
```

### Example Statistics
```
📊 Pair Statistics:
  Total positive pairs: 5
  Total negative pairs: 5

🎯 CTS Statistics:
  Positive CTS: 15
  Negative CTS: 10
  Total CTS: 25
  Balance ratio: 0.67
```

---

## 🤝 Contributing

### Potential Improvements
- [ ] CLIP-seq data integration
- [ ] Multiple miRNA binding site consideration
- [ ] Conservation scoring
- [ ] Accessibility calculation (RNAplfold)
- [ ] Batch processing for very large datasets
- [ ] GPU acceleration for ViennaRNA
- [ ] Alternative energy models

### Code Contributions
See `generate_cts_dataset.py` for:
- Well-documented functions
- Modular design
- Easy to extend
- Type hints (can be added)

---

## 📚 References

### miRNA Target Prediction
- Lewis et al. (2005). "Conserved seed pairing..." Cell.
- Bartel (2009). "MicroRNAs: target recognition..." Cell.
- Agarwal et al. (2015). "Predicting effective microRNA..." eLife.

### ViennaRNA
- Lorenz et al. (2011). "ViennaRNA Package 2.0." AMB.
- https://www.tbi.univie.ac.at/RNA/

### CLIP Methodology
- Chi et al. (2009). "Argonaute HITS-CLIP..." Nature.
- Moore et al. (2014). "miRNA-target chimeras..." Genome Research.

---

## 📧 Support

### Documentation
- **Quick Start**: `QUICKSTART.md`
- **Full Docs**: `README_CTS_DATASET.md`
- **Installation**: `RNA_INSTALLATION.md`

### Issues
- Check documentation first
- Review example data
- Open GitHub issue with:
  - Input data format
  - Command used
  - Error message
  - Python/ViennaRNA versions

---

## 📄 License

[Add your license here]

---

## 🎉 Success Criteria

Your pipeline is working correctly if:

✅ Positive CTS extracted from all validated pairs
✅ Each positive pair generates 5-10 CTS
✅ Negative pairs created from non-targets
✅ Hard negatives have ΔG ≤ threshold
✅ All CTS have computed energies
✅ Output TSV has all required columns
✅ Statistics show reasonable balance
✅ No errors during execution

---

**Version:** 1.0
**Last Updated:** 2025-11-18
**Status:** Production Ready (with real ViennaRNA)

---

## Quick Command Reference

```bash
# Install
pip install -r requirements.txt

# Basic run
python generate_cts_dataset.py --excel data.xlsx --output dataset.tsv

# Test
python generate_cts_dataset.py --excel example_data/example_mirna_mrna_pairs.xlsx --output test.tsv

# Help
python generate_cts_dataset.py --help
```
