# ViennaRNA Installation Guide

## IMPORTANT: Mock vs. Real ViennaRNA

This repository includes a **mock RNA module** (`RNA.py`) for testing purposes only. For production use, you **MUST** install the real ViennaRNA package.

### Current Setup

- ✅ `RNA.py` - Mock module (for testing when ViennaRNA unavailable)
- ⚠️ Generates realistic but simulated binding energies
- ❌ NOT suitable for real research or production

### Why Use the Mock?

The mock module allows you to:
- Test the pipeline without ViennaRNA installed
- Develop and debug your workflow
- Understand the data format

However, **the energy values are simulated** and not based on actual thermodynamic calculations.

## Installing Real ViennaRNA

### Ubuntu/Debian

```bash
# Install ViennaRNA system package
sudo apt-get update
sudo apt-get install vienna-rna

# Install Python bindings
pip install ViennaRNA

# Verify installation
python -c "import RNA; print(RNA.version())"
```

### macOS

```bash
# Install via Homebrew
brew install viennarna

# Install Python bindings
pip install ViennaRNA

# Verify installation
python -c "import RNA; print(RNA.version())"
```

### From Source (All Platforms)

```bash
# Download ViennaRNA
wget https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_5_x/ViennaRNA-2.5.1.tar.gz
tar -zxvf ViennaRNA-2.5.1.tar.gz
cd ViennaRNA-2.5.1

# Configure with Python support
./configure --with-python3

# Compile and install
make
sudo make install

# Update library path (Linux)
sudo ldconfig

# Install Python bindings
pip install ViennaRNA

# Verify
python -c "import RNA; print(RNA.version())"
```

### Conda/Mamba

```bash
# Create environment with ViennaRNA
conda create -n miraw python=3.9
conda activate miraw
conda install -c bioconda viennarna

# Or with mamba (faster)
mamba install -c bioconda viennarna

# Verify
python -c "import RNA; print(RNA.version())"
```

## Switching from Mock to Real

Once you have real ViennaRNA installed:

### Option 1: Remove Mock Module
```bash
# Remove or rename the mock module
rm RNA.py
# or
mv RNA.py RNA_mock.py
```

### Option 2: Use Virtual Environment
```bash
# Create a clean environment with real ViennaRNA
python -m venv venv_real
source venv_real/bin/activate  # Linux/Mac
# or
venv_real\Scripts\activate  # Windows

pip install -r requirements.txt
# ViennaRNA should be installed as shown above
```

### Option 3: Modify PYTHONPATH
```bash
# Ensure system ViennaRNA is found first
export PYTHONPATH=/usr/local/lib/python3.x/site-packages:$PYTHONPATH
```

## Verifying Correct Installation

### Test Script

```python
import RNA

print(f"ViennaRNA version: {RNA.version()}")

# Test cofold
mirna = "UAGCUUAUCAGACUGAUGUUGA"
target = "UCAACAUCAGUCUGAUAAGCUACGUAG"
duplex = mirna + '&' + target

structure, mfe = RNA.cofold(duplex)
print(f"Structure: {structure}")
print(f"MFE: {mfe} kcal/mol")

# Check if it's the mock
if "mock" in RNA.version().lower():
    print("⚠️  WARNING: Using MOCK ViennaRNA!")
    print("   Install real ViennaRNA for production use.")
else:
    print("✅ Using real ViennaRNA")
```

Expected output (real ViennaRNA):
```
ViennaRNA version: 2.5.1
Structure: ((((((((((((((((((((((&))))))))))))))))))))))) (example)
MFE: -15.30 kcal/mol
✅ Using real ViennaRNA
```

Expected output (mock):
```
ViennaRNA version: 2.5.0 (mock)
Structure: ......................&...........................
MFE: -14.52 kcal/mol
⚠️  WARNING: Using MOCK ViennaRNA!
```

## Differences: Mock vs. Real

| Feature | Mock RNA.py | Real ViennaRNA |
|---------|-------------|----------------|
| Energy calculation | Simulated (length + GC) | Thermodynamic model |
| Structure prediction | Placeholder dots | Actual dot-bracket |
| Accuracy | Approximation only | Research-grade |
| Speed | Very fast | Slower but accurate |
| Production use | ❌ NO | ✅ YES |

### Mock Energy Formula

The mock uses a simplified formula:
```python
energy = -0.4 * length * 0.5 - 2.0 * gc_content * length * 0.3
```

This gives **plausible** but **not accurate** values.

### Real ViennaRNA

Uses the Turner energy model with:
- Nearest-neighbor parameters
- Loop entropies
- Stacking energies
- Temperature dependence
- Salt concentration effects

## Docker Alternative

If you have trouble installing ViennaRNA, use Docker:

```bash
# Pull image with ViennaRNA pre-installed
docker pull quay.io/biocontainers/viennarna:2.5.1--py39pl5321h6cc9453_1

# Run your pipeline in container
docker run -v $(pwd):/data quay.io/biocontainers/viennarna:2.5.1--py39pl5321h6cc9453_1 \
    python /data/generate_cts_dataset.py --excel /data/your_data.xlsx --output /data/output.tsv
```

## Troubleshooting

### Import Error: "No module named RNA"

**Problem:** Python can't find the RNA module.

**Solution:**
1. Ensure ViennaRNA is installed system-wide
2. Install Python bindings: `pip install ViennaRNA`
3. Check Python version matches ViennaRNA build
4. Try: `python3 -m pip install ViennaRNA`

### Import Error: "... undefined symbol ..."

**Problem:** ViennaRNA library not in system path.

**Solution (Linux):**
```bash
sudo ldconfig
# or
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

**Solution (macOS):**
```bash
export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH
```

### Wrong Version

**Problem:** pip installs wrong ViennaRNA version.

**Solution:**
```bash
# Uninstall pip version
pip uninstall ViennaRNA

# Install from source (as shown above)
# Then install Python bindings from ViennaRNA build directory
cd ViennaRNA-2.5.1/interfaces/Python3
python setup.py install
```

### Still Using Mock

**Problem:** Pipeline uses mock even after installing ViennaRNA.

**Solution:**
```bash
# Check which RNA module is imported
python -c "import RNA; print(RNA.__file__)"

# If it shows ./RNA.py, remove it:
rm RNA.py

# Should now show system ViennaRNA:
python -c "import RNA; print(RNA.__file__)"
# Output: /usr/local/lib/python3.x/site-packages/RNA/...
```

## Performance Notes

Real ViennaRNA is computationally intensive:

- **Small dataset** (50-100 pairs): ~5-10 minutes
- **Medium dataset** (500-1000 pairs): ~1-2 hours
- **Large dataset** (5000+ pairs): Several hours

The mock is ~100x faster but produces simulated values.

## Recommended Workflow

1. **Development:** Use mock to test pipeline logic
2. **Testing:** Use mock with small datasets
3. **Production:** Use real ViennaRNA for final datasets
4. **Publication:** ALWAYS use real ViennaRNA

## Need Help?

- ViennaRNA documentation: https://www.tbi.univie.ac.at/RNA/
- ViennaRNA GitHub: https://github.com/ViennaRNA/ViennaRNA
- Python bindings: https://www.tbi.univie.ac.at/RNA/ViennaRNA/doc/html/api_python.html

## References

Lorenz, R., et al. (2011). "ViennaRNA Package 2.0." Algorithms for Molecular Biology, 6:26.
