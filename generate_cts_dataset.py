#!/usr/bin/env python3
"""
miRNA-mRNA Candidate Target Sites (CTS) Dataset Generator

This script generates a training dataset for miRNA target prediction by:
1. Extracting positive CTS from validated miRNA-mRNA pairs
2. Generating negative pairs (non-functional interactions)
3. Extracting hard negative CTS (thermodynamically stable but non-functional)
4. Computing ViennaRNA duplex binding energy (ΔG) for all sites

Author: Generated for miRAW training
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from Bio import SeqIO
from collections import defaultdict
from tqdm import tqdm
import RNA  # ViennaRNA package

# Configuration
CONFIG = {
    'window_size': 30,          # MBS length (nucleotides)
    'step_size': 5,             # Window sliding step
    'flanking_nt': 5,           # Upstream/downstream context
    'delta_g_threshold': -10.0, # For negative selection (kcal/mol)
    'top_k_positive': 10,       # Max CTS per positive pair
    'top_k_negative': 5,        # Max CTS per negative pair
    'negative_ratio': 1.0,      # Negative:positive ratio
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CTSDatasetGenerator:
    """Main class for generating CTS dataset"""

    def __init__(self, config: Dict):
        self.config = config
        self.mirna_sequences = {}
        self.utr_sequences = {}
        self.positive_pairs = []
        self.statistics = defaultdict(int)

    def load_positive_pairs_from_excel(self, excel_file: str) -> List[Tuple[str, str, str, str]]:
        """
        Load positive miRNA-mRNA pairs from Excel file

        Args:
            excel_file: Path to Excel file with columns:
                       miRNA_name, miRNA_sequence, mRNA_name, mRNA_sequence

        Returns:
            List of tuples: (miRNA_name, miRNA_seq, mRNA_name, mRNA_seq)
        """
        logger.info(f"Loading positive pairs from {excel_file}")

        try:
            df = pd.read_excel(excel_file)
            required_columns = ['miRNA_name', 'miRNA_sequence', 'mRNA_name', 'mRNA_sequence']

            # Check for required columns
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            pairs = []
            for _, row in df.iterrows():
                mirna_name = str(row['miRNA_name']).strip()
                mirna_seq = str(row['miRNA_sequence']).strip().upper().replace('T', 'U')
                mrna_name = str(row['mRNA_name']).strip()
                mrna_seq = str(row['mRNA_sequence']).strip().upper().replace('T', 'U')

                # Validate sequences
                if mirna_seq and mrna_seq and mirna_seq != 'NAN' and mrna_seq != 'NAN':
                    pairs.append((mirna_name, mirna_seq, mrna_name, mrna_seq))

                    # Store in dictionaries
                    self.mirna_sequences[mirna_name] = mirna_seq
                    self.utr_sequences[mrna_name] = mrna_seq

            logger.info(f"Loaded {len(pairs)} positive pairs")
            self.statistics['total_positive_pairs'] = len(pairs)
            return pairs

        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise

    def load_positive_pairs(self, tsv_file: str) -> List[Tuple[str, str]]:
        """
        Load positive miRNA-mRNA pairs from TSV file

        Args:
            tsv_file: Path to TSV file with columns: miRNA_ID, gene_ID (or mRNA_name)

        Returns:
            List of tuples: (miRNA_ID, gene_ID)
        """
        logger.info(f"Loading positive pairs from {tsv_file}")

        df = pd.read_csv(tsv_file, sep='\t')

        # Try different column name variations
        mirna_col = None
        gene_col = None

        for col in df.columns:
            col_lower = col.lower()
            if 'mirna' in col_lower and not mirna_col:
                mirna_col = col
            elif any(x in col_lower for x in ['gene', 'mrna', 'target']) and not gene_col:
                gene_col = col

        if not mirna_col or not gene_col:
            raise ValueError(f"Could not find miRNA and gene columns in {tsv_file}")

        pairs = [(row[mirna_col], row[gene_col]) for _, row in df.iterrows()]

        logger.info(f"Loaded {len(pairs)} positive pairs")
        self.statistics['total_positive_pairs'] = len(pairs)
        return pairs

    def load_fasta(self, fasta_file: str) -> Dict[str, str]:
        """
        Load sequences from FASTA file

        Args:
            fasta_file: Path to FASTA file

        Returns:
            Dictionary mapping sequence IDs to sequences
        """
        logger.info(f"Loading sequences from {fasta_file}")

        sequences = {}
        try:
            for record in SeqIO.parse(fasta_file, "fasta"):
                seq = str(record.seq).upper().replace('T', 'U')
                sequences[record.id] = seq

            logger.info(f"Loaded {len(sequences)} sequences")
            return sequences

        except Exception as e:
            logger.error(f"Error loading FASTA file: {e}")
            raise

    def query_clip_data(self, mirna_id: str, gene_id: str) -> Optional[List[Tuple[int, int]]]:
        """
        Query CLIP data for binding sites (OPTIONAL - currently returns None)

        This function can be extended to query databases like starBase/ENCORI
        if you have access to CLIP-seq data.

        Args:
            mirna_id: miRNA identifier
            gene_id: Gene identifier

        Returns:
            List of (start, end) positions or None if no CLIP data available
        """
        # Placeholder - implement if you have access to CLIP data
        return None

    def compute_duplex_energy(self, mirna_seq: str, mbs_seq: str) -> float:
        """
        Compute miRNA:MBS duplex binding energy using ViennaRNA

        Args:
            mirna_seq: miRNA sequence (RNA, with U not T)
            mbs_seq: MBS (target site) sequence (RNA, with U not T)

        Returns:
            ΔG in kcal/mol (negative = stable binding)
        """
        try:
            # Ensure RNA format
            mirna_rna = mirna_seq.replace('T', 'U').upper()
            mbs_rna = mbs_seq.replace('T', 'U').upper()

            # Remove any invalid characters
            valid_chars = set('AUCG')
            if not all(c in valid_chars for c in mirna_rna):
                return 0.0
            if not all(c in valid_chars for c in mbs_rna):
                return 0.0

            # Concatenate with '&' separator for cofold
            duplex_string = mirna_rna + '&' + mbs_rna

            # Compute MFE structure and energy
            structure, mfe = RNA.cofold(duplex_string)

            return mfe  # ΔG in kcal/mol

        except Exception as e:
            logger.warning(f"Error computing duplex energy: {e}")
            return 0.0

    def extract_mbs_with_context(self, utr_sequence: str, start: int, end: int) -> Tuple[str, int, int]:
        """
        Extract MBS with flanking nucleotides

        Args:
            utr_sequence: Full UTR sequence
            start: Start position of 30-nt window
            end: End position of 30-nt window

        Returns:
            Tuple of (mbs_with_context, actual_start, actual_end)
        """
        flanking = self.config['flanking_nt']

        # Calculate positions with flanking
        mbs_start = max(0, start - flanking)
        mbs_end = min(len(utr_sequence), end + flanking)

        mbs_with_context = utr_sequence[mbs_start:mbs_end]

        # Pad if at boundaries
        if mbs_start == 0 and start > 0:
            # Pad at beginning
            padding = 'N' * (start - mbs_start)
            mbs_with_context = padding + mbs_with_context

        if mbs_end == len(utr_sequence) and end < len(utr_sequence):
            # Pad at end
            padding = 'N' * (mbs_end + flanking - len(utr_sequence))
            mbs_with_context = mbs_with_context + padding

        return mbs_with_context, mbs_start, mbs_end

    def extract_cts_from_clip(self, mirna_id: str, gene_id: str,
                              clip_sites: List[Tuple[int, int]],
                              mirna_seqs: Dict[str, str],
                              utr_seqs: Dict[str, str]) -> List[Dict]:
        """
        Extract CTS from CLIP peak regions

        Args:
            mirna_id: miRNA identifier
            gene_id: Gene identifier
            clip_sites: List of (start, end) CLIP peak positions
            mirna_seqs: Dictionary of miRNA sequences
            utr_seqs: Dictionary of UTR sequences

        Returns:
            List of CTS dictionaries
        """
        cts_list = []

        if mirna_id not in mirna_seqs or gene_id not in utr_seqs:
            return cts_list

        mirna_seq = mirna_seqs[mirna_id]
        utr_seq = utr_seqs[gene_id]

        window_size = self.config['window_size']
        step_size = self.config['step_size']

        for clip_start, clip_end in clip_sites:
            # Slide window within CLIP region
            for pos in range(clip_start, clip_end - window_size + 1, step_size):
                mbs_seq = utr_seq[pos:pos + window_size]

                if len(mbs_seq) < window_size:
                    continue

                # Extract with context
                mbs_with_context, actual_start, actual_end = self.extract_mbs_with_context(
                    utr_seq, pos, pos + window_size
                )

                # Compute binding energy
                delta_g = self.compute_duplex_energy(mirna_seq, mbs_seq)

                cts_list.append({
                    'miRNA_ID': mirna_id,
                    'gene_ID': gene_id,
                    'gene_symbol': gene_id,
                    'miRNA_seq': mirna_seq,
                    'MBS_seq': mbs_with_context,
                    'UTR_position': pos,
                    'deltaG': delta_g,
                    'label': 1,
                    'source': 'CLIP'
                })

        return cts_list

    def extract_cts_sliding_window(self, mirna_id: str, gene_id: str,
                                   mirna_seqs: Dict[str, str],
                                   utr_seqs: Dict[str, str],
                                   top_k: int = 10) -> List[Dict]:
        """
        Extract CTS using sliding window approach (fallback or for positives)

        Args:
            mirna_id: miRNA identifier
            gene_id: Gene identifier
            mirna_seqs: Dictionary of miRNA sequences
            utr_seqs: Dictionary of UTR sequences
            top_k: Number of top sites to keep (by most negative ΔG)

        Returns:
            List of CTS dictionaries
        """
        if mirna_id not in mirna_seqs or gene_id not in utr_seqs:
            return []

        mirna_seq = mirna_seqs[mirna_id]
        utr_seq = utr_seqs[gene_id]

        window_size = self.config['window_size']
        step_size = self.config['step_size']

        candidates = []

        # Slide window across entire UTR
        for pos in range(0, len(utr_seq) - window_size + 1, step_size):
            mbs_seq = utr_seq[pos:pos + window_size]

            if len(mbs_seq) < window_size:
                continue

            # Extract with context
            mbs_with_context, actual_start, actual_end = self.extract_mbs_with_context(
                utr_seq, pos, pos + window_size
            )

            # Compute binding energy
            delta_g = self.compute_duplex_energy(mirna_seq, mbs_seq)

            candidates.append({
                'miRNA_ID': mirna_id,
                'gene_ID': gene_id,
                'gene_symbol': gene_id,
                'miRNA_seq': mirna_seq,
                'MBS_seq': mbs_with_context,
                'UTR_position': pos,
                'deltaG': delta_g,
                'label': 1,
                'source': 'sliding_window'
            })

        # Sort by ΔG (most negative first) and keep top K
        candidates.sort(key=lambda x: x['deltaG'])
        return candidates[:top_k]

    def generate_negative_pairs(self, positive_pairs: List[Tuple[str, str, str, str]],
                               utr_seqs: Dict[str, str]) -> List[Tuple[str, str]]:
        """
        Generate negative miRNA-gene pairs

        Args:
            positive_pairs: List of positive (miRNA, miRNA_seq, gene, gene_seq) tuples
            utr_seqs: Dictionary of all available UTR sequences

        Returns:
            List of negative (miRNA_ID, gene_ID) pairs
        """
        logger.info("Generating negative pairs...")

        # Group positive genes by miRNA
        mirna_to_genes = defaultdict(set)
        all_mirnas = set()

        for mirna_id, mirna_seq, gene_id, gene_seq in positive_pairs:
            mirna_to_genes[mirna_id].add(gene_id)
            all_mirnas.add(mirna_id)

        # Get all available genes
        all_genes = set(utr_seqs.keys())

        negative_pairs = []
        negative_ratio = self.config['negative_ratio']

        for mirna_id in all_mirnas:
            positive_genes = mirna_to_genes[mirna_id]

            # Get genes not targeted by this miRNA
            negative_genes = all_genes - positive_genes

            # Sample negative genes
            n_negative = int(len(positive_genes) * negative_ratio)

            if len(negative_genes) < n_negative:
                sampled_genes = list(negative_genes)
            else:
                sampled_genes = np.random.choice(
                    list(negative_genes),
                    size=n_negative,
                    replace=False
                )

            for gene_id in sampled_genes:
                negative_pairs.append((mirna_id, gene_id))

        logger.info(f"Generated {len(negative_pairs)} negative pairs")
        self.statistics['total_negative_pairs'] = len(negative_pairs)
        return negative_pairs

    def extract_negative_cts(self, mirna_id: str, gene_id: str,
                            mirna_seqs: Dict[str, str],
                            utr_seqs: Dict[str, str],
                            delta_g_threshold: float = -10.0,
                            top_k: int = 5) -> List[Dict]:
        """
        Extract hard negative CTS (thermodynamically stable but non-functional)

        Args:
            mirna_id: miRNA identifier
            gene_id: Gene identifier
            mirna_seqs: Dictionary of miRNA sequences
            utr_seqs: Dictionary of UTR sequences
            delta_g_threshold: Only keep sites with ΔG ≤ this threshold
            top_k: Number of top sites to keep

        Returns:
            List of negative CTS dictionaries
        """
        if mirna_id not in mirna_seqs or gene_id not in utr_seqs:
            return []

        mirna_seq = mirna_seqs[mirna_id]
        utr_seq = utr_seqs[gene_id]

        window_size = self.config['window_size']
        step_size = self.config['step_size']

        candidates = []

        # Slide window across entire UTR
        for pos in range(0, len(utr_seq) - window_size + 1, step_size):
            mbs_seq = utr_seq[pos:pos + window_size]

            if len(mbs_seq) < window_size:
                continue

            # Extract with context
            mbs_with_context, actual_start, actual_end = self.extract_mbs_with_context(
                utr_seq, pos, pos + window_size
            )

            # Compute binding energy
            delta_g = self.compute_duplex_energy(mirna_seq, mbs_seq)

            # Only keep stable duplexes (hard negatives)
            if delta_g <= delta_g_threshold:
                candidates.append({
                    'miRNA_ID': mirna_id,
                    'gene_ID': gene_id,
                    'gene_symbol': gene_id,
                    'miRNA_seq': mirna_seq,
                    'MBS_seq': mbs_with_context,
                    'UTR_position': pos,
                    'deltaG': delta_g,
                    'label': 0,
                    'source': 'negative'
                })

        # Sort by ΔG (most negative first) and keep top K
        candidates.sort(key=lambda x: x['deltaG'])
        return candidates[:top_k]

    def save_dataset(self, cts_list: List[Dict], output_file: str):
        """
        Save CTS dataset to TSV file

        Args:
            cts_list: List of CTS dictionaries
            output_file: Path to output TSV file
        """
        logger.info(f"Saving dataset to {output_file}")

        df = pd.DataFrame(cts_list)

        # Reorder columns
        column_order = [
            'miRNA_ID', 'gene_ID', 'gene_symbol', 'miRNA_seq', 'MBS_seq',
            'UTR_position', 'deltaG', 'label', 'source'
        ]

        df = df[column_order]
        df.to_csv(output_file, sep='\t', index=False)

        logger.info(f"Saved {len(df)} CTS entries")

    def print_statistics(self, positive_cts: List[Dict], negative_cts: List[Dict]):
        """
        Print dataset statistics

        Args:
            positive_cts: List of positive CTS
            negative_cts: List of negative CTS
        """
        print("\n" + "="*60)
        print("DATASET STATISTICS")
        print("="*60)

        print(f"\n📊 Pair Statistics:")
        print(f"  Total positive pairs: {self.statistics['total_positive_pairs']}")
        print(f"  Total negative pairs: {self.statistics['total_negative_pairs']}")

        print(f"\n🎯 CTS Statistics:")
        print(f"  Positive CTS: {len(positive_cts)}")
        print(f"  Negative CTS: {len(negative_cts)}")
        print(f"  Total CTS: {len(positive_cts) + len(negative_cts)}")
        print(f"  Balance ratio: {len(negative_cts) / len(positive_cts):.2f}")

        # Energy statistics
        if positive_cts:
            pos_energies = [cts['deltaG'] for cts in positive_cts]
            print(f"\n⚡ Positive CTS Energy (ΔG):")
            print(f"  Mean: {np.mean(pos_energies):.2f} kcal/mol")
            print(f"  Median: {np.median(pos_energies):.2f} kcal/mol")
            print(f"  Min: {np.min(pos_energies):.2f} kcal/mol")
            print(f"  Max: {np.max(pos_energies):.2f} kcal/mol")

        if negative_cts:
            neg_energies = [cts['deltaG'] for cts in negative_cts]
            print(f"\n⚡ Negative CTS Energy (ΔG):")
            print(f"  Mean: {np.mean(neg_energies):.2f} kcal/mol")
            print(f"  Median: {np.median(neg_energies):.2f} kcal/mol")
            print(f"  Min: {np.min(neg_energies):.2f} kcal/mol")
            print(f"  Max: {np.max(neg_energies):.2f} kcal/mol")

        # Source distribution
        if positive_cts:
            sources = defaultdict(int)
            for cts in positive_cts:
                sources[cts['source']] += 1

            print(f"\n📍 Positive CTS Sources:")
            for source, count in sources.items():
                print(f"  {source}: {count}")

        print("\n" + "="*60)

    def run(self, excel_file: Optional[str] = None,
            positive_pairs_file: Optional[str] = None,
            mirna_fasta: Optional[str] = None,
            utr_fasta: Optional[str] = None,
            output_file: str = 'miraw_dataset.tsv',
            use_clip: bool = False):
        """
        Main pipeline execution

        Args:
            excel_file: Path to Excel file with positive pairs and sequences
            positive_pairs_file: Path to TSV file with positive pairs (alternative to Excel)
            mirna_fasta: Path to miRNA FASTA file (if not using Excel)
            utr_fasta: Path to UTR FASTA file (if not using Excel)
            output_file: Path to output TSV file
            use_clip: Whether to attempt using CLIP data
        """
        logger.info("Starting CTS dataset generation pipeline")

        # Step 1: Load data
        if excel_file:
            logger.info("Loading data from Excel file")
            positive_pairs = self.load_positive_pairs_from_excel(excel_file)
            # Sequences are already loaded into self.mirna_sequences and self.utr_sequences
            mirna_seqs = self.mirna_sequences
            utr_seqs = self.utr_sequences
        else:
            if not all([positive_pairs_file, mirna_fasta, utr_fasta]):
                raise ValueError("Must provide either excel_file or all of: positive_pairs_file, mirna_fasta, utr_fasta")

            logger.info("Loading data from separate files")
            pair_tuples = self.load_positive_pairs(positive_pairs_file)
            mirna_seqs = self.load_fasta(mirna_fasta)
            utr_seqs = self.load_fasta(utr_fasta)

            # Convert to full tuples
            positive_pairs = []
            for mirna_id, gene_id in pair_tuples:
                if mirna_id in mirna_seqs and gene_id in utr_seqs:
                    positive_pairs.append((
                        mirna_id, mirna_seqs[mirna_id],
                        gene_id, utr_seqs[gene_id]
                    ))

            self.mirna_sequences = mirna_seqs
            self.utr_sequences = utr_seqs

        logger.info(f"Loaded {len(mirna_seqs)} miRNA sequences")
        logger.info(f"Loaded {len(utr_seqs)} UTR sequences")
        logger.info(f"Processing {len(positive_pairs)} valid positive pairs")

        # Step 2: Generate positive CTS
        logger.info("\nExtracting positive CTS...")
        positive_cts = []

        for mirna_id, mirna_seq, gene_id, gene_seq in tqdm(positive_pairs, desc="Positive CTS"):
            if use_clip:
                # Try CLIP approach first
                clip_sites = self.query_clip_data(mirna_id, gene_id)

                if clip_sites:
                    cts = self.extract_cts_from_clip(
                        mirna_id, gene_id, clip_sites,
                        mirna_seqs, utr_seqs
                    )
                else:
                    cts = self.extract_cts_sliding_window(
                        mirna_id, gene_id,
                        mirna_seqs, utr_seqs,
                        top_k=self.config['top_k_positive']
                    )
            else:
                # Use sliding window approach
                cts = self.extract_cts_sliding_window(
                    mirna_id, gene_id,
                    mirna_seqs, utr_seqs,
                    top_k=self.config['top_k_positive']
                )

            positive_cts.extend(cts)

        logger.info(f"Generated {len(positive_cts)} positive CTS")

        # Step 3: Generate negative pairs
        negative_pairs = self.generate_negative_pairs(positive_pairs, utr_seqs)

        # Step 4: Extract negative CTS
        logger.info("\nExtracting negative CTS (hard negatives)...")
        negative_cts = []

        for mirna_id, gene_id in tqdm(negative_pairs, desc="Negative CTS"):
            cts = self.extract_negative_cts(
                mirna_id, gene_id,
                mirna_seqs, utr_seqs,
                delta_g_threshold=self.config['delta_g_threshold'],
                top_k=self.config['top_k_negative']
            )
            negative_cts.extend(cts)

        logger.info(f"Generated {len(negative_cts)} negative CTS")

        # Step 5: Combine and save
        all_cts = positive_cts + negative_cts
        self.save_dataset(all_cts, output_file)

        # Step 6: Print statistics
        self.print_statistics(positive_cts, negative_cts)

        logger.info(f"\n✅ Pipeline completed successfully!")
        logger.info(f"📁 Output saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate miRNA-mRNA CTS training dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using Excel file with all data:
  python generate_cts_dataset.py --excel mirna_mrna_data.xlsx --output dataset.tsv

  # Using separate files:
  python generate_cts_dataset.py \\
      --positive-pairs positive_pairs.tsv \\
      --mirna-fasta mirna_sequences.fa \\
      --utr-fasta utr_sequences.fa \\
      --output dataset.tsv

  # With custom parameters:
  python generate_cts_dataset.py \\
      --excel mirna_mrna_data.xlsx \\
      --output dataset.tsv \\
      --top-k-positive 15 \\
      --top-k-negative 10 \\
      --delta-g-threshold -12.0
        """
    )

    # Input options
    input_group = parser.add_argument_group('Input files')
    input_group.add_argument('--excel', type=str, help='Excel file with positive pairs and sequences')
    input_group.add_argument('--positive-pairs', type=str, help='TSV file with positive pairs')
    input_group.add_argument('--mirna-fasta', type=str, help='FASTA file with miRNA sequences')
    input_group.add_argument('--utr-fasta', type=str, help='FASTA file with UTR sequences')

    # Output
    parser.add_argument('--output', type=str, default='miraw_dataset.tsv',
                       help='Output TSV file (default: miraw_dataset.tsv)')

    # Parameters
    param_group = parser.add_argument_group('Parameters')
    param_group.add_argument('--window-size', type=int, default=30,
                            help='MBS window size (default: 30)')
    param_group.add_argument('--step-size', type=int, default=5,
                            help='Sliding window step (default: 5)')
    param_group.add_argument('--flanking-nt', type=int, default=5,
                            help='Flanking nucleotides (default: 5)')
    param_group.add_argument('--delta-g-threshold', type=float, default=-10.0,
                            help='ΔG threshold for negatives (default: -10.0)')
    param_group.add_argument('--top-k-positive', type=int, default=10,
                            help='Max CTS per positive pair (default: 10)')
    param_group.add_argument('--top-k-negative', type=int, default=5,
                            help='Max CTS per negative pair (default: 5)')
    param_group.add_argument('--negative-ratio', type=float, default=1.0,
                            help='Negative to positive ratio (default: 1.0)')
    param_group.add_argument('--use-clip', action='store_true',
                            help='Attempt to use CLIP data (default: False)')

    args = parser.parse_args()

    # Validate inputs
    if not args.excel and not all([args.positive_pairs, args.mirna_fasta, args.utr_fasta]):
        parser.error("Must provide either --excel OR all of: --positive-pairs, --mirna-fasta, --utr-fasta")

    # Update config
    config = CONFIG.copy()
    config['window_size'] = args.window_size
    config['step_size'] = args.step_size
    config['flanking_nt'] = args.flanking_nt
    config['delta_g_threshold'] = args.delta_g_threshold
    config['top_k_positive'] = args.top_k_positive
    config['top_k_negative'] = args.top_k_negative
    config['negative_ratio'] = args.negative_ratio

    # Create generator
    generator = CTSDatasetGenerator(config)

    # Run pipeline
    try:
        generator.run(
            excel_file=args.excel,
            positive_pairs_file=args.positive_pairs,
            mirna_fasta=args.mirna_fasta,
            utr_fasta=args.utr_fasta,
            output_file=args.output,
            use_clip=args.use_clip
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
