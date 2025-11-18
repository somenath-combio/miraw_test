"""
Mock ViennaRNA module for testing when ViennaRNA is not installed

This is a simple mock implementation for testing purposes only.
For production use, please install the real ViennaRNA package.

Install ViennaRNA:
  - Ubuntu/Debian: sudo apt-get install vienna-rna
  - macOS: brew install viennarna
  - Then: pip install ViennaRNA
"""

import random


def version():
    """Return mock version string"""
    return "2.5.0 (mock)"


def cofold(sequence_string):
    """
    Mock implementation of ViennaRNA cofold function

    In real ViennaRNA, this computes the minimum free energy (MFE)
    structure and energy of two RNA molecules bound together.

    Args:
        sequence_string: Two RNA sequences separated by '&'
                        e.g., "AUGCUA&UAGCAU"

    Returns:
        Tuple of (structure, mfe_energy)
        - structure: dot-bracket notation of the MFE structure
        - mfe_energy: free energy in kcal/mol (negative = stable)

    This mock generates realistic-looking energies based on:
    - Sequence length (longer = more negative)
    - GC content (higher GC = more negative)
    - Some randomness to simulate different binding modes
    """
    try:
        if '&' not in sequence_string:
            return ".", 0.0

        seq1, seq2 = sequence_string.split('&')

        # Calculate GC content
        def gc_content(seq):
            gc = seq.count('G') + seq.count('C')
            return gc / len(seq) if len(seq) > 0 else 0

        gc1 = gc_content(seq1)
        gc2 = gc_content(seq2)
        avg_gc = (gc1 + gc2) / 2

        # Estimate energy based on:
        # 1. Length of sequences (longer = more potential bonds)
        # 2. GC content (GC bonds are stronger than AU)
        # 3. Add some randomness

        total_length = len(seq1) + len(seq2)

        # Base energy: roughly -0.3 to -0.5 kcal/mol per base pair
        # Assume ~40-60% of bases form pairs
        base_energy = -0.4 * total_length * 0.5

        # GC bonus: GC pairs are ~1-2 kcal/mol more stable than AU
        gc_bonus = -2.0 * avg_gc * total_length * 0.3

        # Add some controlled randomness (±20%)
        random_factor = 1.0 + (random.random() - 0.5) * 0.4

        # Total energy
        mfe = (base_energy + gc_bonus) * random_factor

        # Clamp to realistic range (-30 to 0 kcal/mol)
        mfe = max(-30.0, min(0.0, mfe))

        # Generate a mock structure (dot-bracket notation)
        # For simplicity, just create a plausible structure
        len1 = len(seq1)
        len2 = len(seq2)

        # Simple structure: some pairing
        structure = '.' * len1 + '&' + '.' * len2

        return structure, round(mfe, 2)

    except Exception as e:
        # If anything goes wrong, return neutral values
        return ".", 0.0


# Aliases for common ViennaRNA functions
fold = cofold  # Alias


def fold_compound(sequence):
    """Mock fold_compound - not fully implemented"""
    class MockFoldCompound:
        def __init__(self, seq):
            self.sequence = seq

        def mfe(self):
            structure, energy = cofold(self.sequence)
            return structure, energy

    return MockFoldCompound(sequence)


if __name__ == '__main__':
    # Test the mock module
    print(f"ViennaRNA version: {version()}")
    print("\nTesting cofold function:")

    # Test sequences
    mirna = "UAGCUUAUCAGACUGAUGUUGA"
    target = "UCAACAUCAGUCUGAUAAGCUACGUAG"

    duplex = mirna + '&' + target
    structure, energy = cofold(duplex)

    print(f"miRNA:  {mirna}")
    print(f"Target: {target}")
    print(f"Structure: {structure}")
    print(f"Energy: {energy} kcal/mol")

    # Test multiple times to show variation
    print("\nMultiple calls (showing randomness):")
    for i in range(5):
        _, energy = cofold(duplex)
        print(f"  Call {i+1}: {energy} kcal/mol")
