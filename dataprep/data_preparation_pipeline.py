# data_preparation_pipeline.py

import os
import re
import io
import time
import random
import requests
import pandas as pd
from Bio import SeqIO
from typing import Tuple, Optional, List, Dict
import logging
# zipfile is no longer strictly needed for API logic but is kept for general robustness

# Import configurations
from config import (
    IEDB_CSV_FILE, UNIPROT_CSV_FILE, IEDB_FASTA_FILE, UNIPROT_FASTA_FILE, 
    TARGET_SAMPLE_SIZE, IEDB_EPITOPE_BASE_URL,
    UNIPROT_URL, UNIPROT_PARAMS, MIN_PEPTIDE_LENGTH, MAX_PEPTIDE_LENGTH,
    LOG_CONFIG, DEFAULT_REQUEST_HEADERS, IEDB_QUERY_URL, IEDB_PAGINATION_LIMIT,
    IEDB_BASE_PARAMS_LIST, IEDB_SEQUENCE_CANDIDATES, IEDB_ORGANISM_CANDIDATES,
    IEDB_PROTEIN_CANDIDATES
)

# ------------------------------------------------------------------------------
# Initialize Logging
# ------------------------------------------------------------------------------
logging.basicConfig(**LOG_CONFIG)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# 2. HELPER FUNCTIONS (UTILITIES)
# ------------------------------------------------------------------------------

def create_accession_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures a sequential 'Accession_ID' column exists. Prefers IEDB's Epitope ID 
    if available for the FASTA header construction.

    Args:
        df: The input DataFrame.

    Returns:
        The DataFrame with the 'Accession_ID' column.
    """
    if 'Accession_ID' not in df.columns:
        # Check for IEDB Epitope ID candidates for stable ID and FASTA header
        id_candidates = ['epitope_id', 'bcell_epitope_id']
        found_id_col = next((col for col in id_candidates if col in df.columns), None)

        if found_id_col: 
            # Use IEDB's own ID as base and clean up float/spaces
            df['Epitope_ID'] = df[found_id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            # Filter out any non-numeric IDs that might remain if cleaning failed
            df = df[df['Epitope_ID'].str.isnumeric()]
            df['Accession_ID'] = 'IEDB_EPI_' + df['Epitope_ID']
        else: 
            # Fallback to sequential ID
            df.reset_index(drop=True, inplace=True)
            df['Accession_ID'] = df.index.map(lambda x: f"IEDB_EPI_{x + 1:06d}")
            df['Epitope_ID'] = df['Accession_ID'].str.replace('IEDB_EPI_', '') # Use the number part for FASTA header

    return df


def clean_iedb_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the 'Sequence' column by removing PTM strings and applying standard filters 
    (length, uniqueness, and invalid amino acids/characters).

    Args:
        df: The IEDB DataFrame containing a 'Sequence' column.

    Returns:
        The cleaned and filtered DataFrame.
    """
    if 'Sequence' in df.columns:
        df["Sequence"] = df["Sequence"].astype(str).str.upper()
        
        # 1. Remove PTM notations (e.g., +CITR(R1))
        df["Sequence"] = df["Sequence"].str.replace(r'\s*\+.*', '', regex=True)
        # 2. Remove trailing spaces and extra text
        df["Sequence"] = df["Sequence"].str.replace(r'\s+.*', '', regex=True)
        
        # 3. Apply standard quality filters
        df = df.dropna(subset=["Sequence", "Organism"])
        df = df[df["Sequence"].str.len().between(MIN_PEPTIDE_LENGTH, MAX_PEPTIDE_LENGTH)]
        
        # 4. Remove sequences with invalid amino acids (B, J, O, U, X, Z) and MPT characters
        df = df[~df['Sequence'].str.contains(r'[BJOUXZ\+\(\)]', regex=True)]
        
        # 5. Keep only unique sequences
        df = df.drop_duplicates(subset=["Sequence"])
    
    return df


def sample_and_export_fasta(
    df: pd.DataFrame, 
    output_fasta_name: str, 
    step_label: str, 
    sample_size: int, 
    dataset_type: str
) -> bool:
    """
    Performs random sampling and exports the data to a FASTA file using the 
    expanded header template for IEDB.
    
    Args:
        df: The input DataFrame.
        output_fasta_name: The name of the output FASTA file.
        step_label: Label for console output.
        sample_size: The target number of sequences to sample.
        dataset_type: 'IEDB' or 'UNIPROT' to determine header format.

    Returns:
        True if export was successful, False otherwise.
    """
    if os.path.exists(output_fasta_name):
        logger.info(f"--- Skipping {step_label}: File '{output_fasta_name}' already exists.")
        return True

    logger.info(f"\n--- Starting {step_label} ---")
    
    if len(df) > sample_size:
        logger.info(f"  - Randomly sampling {sample_size} records from {len(df)} total.")
        df_sampled = df.sample(n=sample_size, random_state=42, replace=False) 
    else:
        df_sampled = df.copy()
        if len(df) < sample_size:
             logger.warning(f"  - DF has fewer than {sample_size} records. Using all {len(df)}.")

    # Prepare columns for FASTA header
    if dataset_type == 'IEDB':
        # Ensure required columns exist and are strings
        df_sampled['Organism'] = df_sampled['Organism'].astype(str).fillna('unknown_organism')
        df_sampled['Protein_Name'] = df_sampled['Protein_Name'].astype(str).fillna('unknown_protein')
        # Epitope_ID must be the clean ID number for the header/link
        df_sampled['Epitope_ID'] = df_sampled['Epitope_ID'].astype(str).fillna('0').str.replace('IEDB_EPI_', '') 
    elif dataset_type == 'UNIPROT':
        df_sampled['Original_Header'] = df_sampled['Original_Header'].astype(str).fillna('unknown_header')

    logger.info(f"  - Writing {len(df_sampled)} records to {output_fasta_name}...")

    try:
        with open(output_fasta_name, 'w') as f:
            for _, row in df_sampled.iterrows():

                if dataset_type == 'UNIPROT':
                    fasta_header = f">{row['Original_Header']}"

                elif dataset_type == 'IEDB':
                    # Desired format: >infectious-34 | B13 antigen | Trypanosoma cruzi | http://www.iedb.org/epitope/34
                    
                    epitope_id_val = row['Epitope_ID']
                    iedb_link = f"{IEDB_EPITOPE_BASE_URL}{epitope_id_val}"
                    
                    fasta_header = (
                        f">infectious-{epitope_id_val} | "
                        f"{row['Protein_Name']} | "
                        f"{row['Organism']} | "
                        f"{iedb_link}"
                    )
                    
                else:
                     raise ValueError(f"Unrecognized dataset type: {dataset_type}.")

                f.write(fasta_header + '\n')
                f.write(row['Sequence'] + '\n')

        logger.info(f"✅ FASTA file generated: {output_fasta_name} (Final size: {len(df_sampled)})")
        return True
    except Exception as e:
        logger.error(f"❌ Error exporting FASTA file {output_fasta_name}: {e}")
        return False


# ------------------------------------------------------------------------------
# 3. USE CASE FUNCTIONS (BUSINESS LOGIC)
# ------------------------------------------------------------------------------

def download_positive_data(output_filename: str = IEDB_CSV_FILE) -> Tuple[Optional[pd.DataFrame], int]:
    """
    Downloads IEDB B-cell epitope data using the paginated IEDB Query API, 
    cleans, filters, and exports the data.

    Args:
        output_filename: The path for the output CSV file.

    Returns:
        A tuple containing the cleaned DataFrame and the final count of records.
    """
    logger.info("--- 1. Processing IEDB Positive Data ---")

    if os.path.exists(output_filename):
        logger.info(f"  - Skipping API Download: File '{output_filename}' exists. Reading from disk...")
        # Lógica de leitura de disco
        try:
            df_raw_export = pd.read_csv(output_filename)
            required_fasta_cols = ['Accession_ID', 'Sequence', 'Group', 'Organism', 'Protein_Name', 'Epitope_ID']
            for col in required_fasta_cols:
                if col not in df_raw_export.columns:
                    logger.warning(f"  - Missing column '{col}' in existing IEDB CSV. Filling with 'unknown'.")
                    df_raw_export[col] = 'unknown'

            df_raw_export = clean_iedb_sequence(df_raw_export) 
            df_raw_export = create_accession_id(df_raw_export) 
            
            final_count = len(df_raw_export)
            logger.info(f"✅ Valid and Unique Positives (IEDB_All): {final_count} records read and cleaned.")
            return df_raw_export, final_count
        except Exception as e:
            logger.error(f"❌ Error reading {output_filename}: {e}. Attempting API download.")
            
    # --- API Paginada Download Logic ---
    url = IEDB_QUERY_URL
    limit = IEDB_PAGINATION_LIMIT
    offset = 0
    all_chunks = []
    
    # 1. Probe the API to ensure connection is valid
    try:
        probe = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, 
                             params=IEDB_BASE_PARAMS_LIST + [("limit", 1), ("offset", 0)], 
                             timeout=60)
        probe.raise_for_status()
        logger.info("  - IEDB API probe successful. Starting pagination.")
    except Exception as e:
        logger.error(f"❌ IEDB API Probe failed (Connection/Auth error): {e}")
        return None, 0
    
    # 2. Paginated Download Loop
    batch = 1
    while True:
        params_list = list(IEDB_BASE_PARAMS_LIST)
        params_list.extend([("limit", limit), ("offset", offset)])
        
        try:
            logger.info(f"  - Downloading batch {batch} (Offset: {offset})...")
            r = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, params=params_list, timeout=600)
            r.raise_for_status()
            text = r.text.strip()
            
            if not text: 
                logger.info(f"  - Batch {batch} returned empty data. Ending download.")
                break
                
            df_chunk = pd.read_csv(io.StringIO(text), low_memory=False)
            
            if df_chunk.empty: 
                logger.info(f"  - Batch {batch} returned empty DataFrame. Ending download.")
                break
                
            all_chunks.append(df_chunk)
            
            if len(df_chunk) < limit: 
                logger.info(f"  - Batch {batch} was partial ({len(df_chunk)} records). Download complete.")
                break
                
            offset += limit
            batch += 1
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ API Connection/Read Error in batch {batch}: {e}")
            break

    if not all_chunks:
        logger.error("\n❌ No data downloaded from IEDB API.")
        return None, 0

    df_raw = pd.concat(all_chunks, ignore_index=True)
    logger.info(f"  - Total raw records downloaded: {len(df_raw)}")
    
    # --- Cleaning, Standardization, and Column Mapping ---
    
    df_raw.columns = [col.lower().replace("__", "_").replace(" ", "_") for col in df_raw.columns]
    
    # 1. Rename 'Sequence' column
    found_seq = next((c for c in IEDB_SEQUENCE_CANDIDATES if c in df_raw.columns), None)
    if found_seq: df_raw = df_raw.rename(columns={found_seq: "Sequence"})
    
    # 2. Rename 'Organism' column
    found_org = next((c for c in IEDB_ORGANISM_CANDIDATES if c in df_raw.columns), None)
    if found_org: df_raw = df_raw.rename(columns={found_org: "Organism"})
    
    # 3. Rename 'Protein_Name' column (for FASTA header)
    found_protein = next((c for c in IEDB_PROTEIN_CANDIDATES if c in df_raw.columns), None)
    if found_protein: 
        df_raw = df_raw.rename(columns={found_protein: "Protein_Name"})
    else:
        df_raw['Protein_Name'] = 'Unknown Antigen'
        
    # --- Check and Apply Filters ---
    
    if "Sequence" not in df_raw.columns: 
        logger.error("❌ Critical: 'Sequence' column not found after mapping.")
        return None, 0
    
    # Ensure all required columns for FASTA header exist, filling missing ones
    required_cols_for_fasta = ['Organism', 'Protein_Name', 'epitope_id'] 
    for col in required_cols_for_fasta:
        if col not in df_raw.columns:
            logger.warning(f"  - Required FASTA column '{col}' not found. Filling with placeholder.")
            df_raw[col] = f'Unknown {col.replace("_", " ").title()}'
    
    # Apply cleaning and filters (removes MPT, filters length/uniqueness)
    df_raw = clean_iedb_sequence(df_raw) 
    df_raw['Group'] = 'IEDB_All'
    
    # Create Accession_ID and Epitope_ID (Crucial for the expanded FASTA header)
    df_raw = create_accession_id(df_raw) 

    final_count = len(df_raw)
    
    if final_count > 0:
        logger.info(f"✅ Valid and Unique Positives (IEDB_All): {final_count} records after cleaning.")

        # Export only necessary columns for the final CSV and FASTA header metadata
        df_raw_export = df_raw[['Accession_ID', 'Sequence', 'Group', 'Organism', 'Protein_Name', 'Epitope_ID']].copy()
        df_raw_export.to_csv(output_filename, sep=',', index=False)
        return df_raw_export, final_count
    else:
        logger.error("\n❌ Failed to obtain valid IEDB positive data after cleaning.")
        return None, 0


def generate_negative_data(target_count: int, output_filename: str = UNIPROT_CSV_FILE) -> pd.DataFrame:
    """
    Downloads UniProt sequences and generates non-overlapping random peptide 
    fragments (negatives) of length 10-30, matching the target count.

    Args:
        target_count: The number of negative sequences to generate.
        output_filename: The path for the output CSV file.

    Returns:
        The DataFrame containing the generated negative sequences.
    """
    logger.info(f"\n--- 2. Generating Negative Data (UniProt Random Peptides) ---")

    if os.path.exists(output_filename):
        logger.info(f"  - Skipping Generation: File '{output_filename}' exists. Reading from disk...")
        try:
            df_synth = pd.read_csv(output_filename)
            required_cols = ['Source_Protein', 'Original_Header']
            if all(col in df_synth.columns for col in required_cols):
                logger.info(f"✅ Valid and Balanced Negatives: {len(df_synth)} records read.")
                return df_synth
            else:
                logger.warning(f"⚠️ Warning: Existing file incomplete. Forcing regeneration.")
        except Exception as e:
            logger.error(f"❌ Error reading {output_filename}: {e}. Attempting to generate again.")
            
    logger.info(f"  - Target count for negative sequences: {target_count}")
    logger.info("  - Downloading reviewed sequences (Swiss-Prot) from UniProt...")
    
    try:
        req = requests.get(UNIPROT_URL, params=UNIPROT_PARAMS, stream=True, timeout=600)
        req.raise_for_status()
        
        fasta_content = req.text
        background_seqs = list(SeqIO.parse(io.StringIO(fasta_content), "fasta"))
    except Exception as e:
        logger.error(f"❌ Error downloading UniProt data: {e}")
        return pd.DataFrame()

    synthetic_data = []
    seen_peptides = set()
    sample_pool = list(range(len(background_seqs)))

    logger.info(f"  - Total proteins downloaded for sampling: {len(background_seqs)}")
    logger.info("  - Sampling random peptides...")
    
    MIN_LEN, MAX_LEN = MIN_PEPTIDE_LENGTH, MAX_PEPTIDE_LENGTH 
    
    while len(synthetic_data) < target_count and sample_pool:
        if not sample_pool:
             break 

        idx_to_sample = random.choice(sample_pool)
        prot = background_seqs[idx_to_sample]
        s_str = str(prot.seq).upper()
        
        if len(s_str) < MIN_LEN:
            sample_pool.remove(idx_to_sample)
            continue
        
        size = random.randint(MIN_LEN, min(MAX_LEN, len(s_str)))
        start = random.randint(0, len(s_str) - size)
        pep = s_str[start : start + size]

        if pep not in seen_peptides and not set(pep).intersection(set("BJOUXZ")):
            seen_peptides.add(pep)
            
            protein_id = prot.id.split('|')[1] if '|' in prot.id else prot.id
            original_header = prot.description.strip()
            
            synthetic_data.append({
                'Sequence': pep, 
                'Group': 'UNIPROT_RANDOM', 
                'Organism': 'UniProt_Random', 
                'Source_Protein': protein_id,
                'Original_Header': original_header
            })


    df_synth = pd.DataFrame(synthetic_data)

    if len(df_synth) < target_count:
        logger.warning(f"⚠️ Warning: Could not generate the full target count. Generated: {len(df_synth)}")

    df_synth.to_csv(output_filename, sep=',', index=False)
    logger.info(f"✅ Negative dataset CSV generated: {output_filename} (Size: {len(df_synth)})")
    return df_synth


# ------------------------------------------------------------------------------
# 4. MAIN EXECUTION (ENTRY POINT)
# ------------------------------------------------------------------------------

def run_data_pipeline():
    """
    The main orchestration function for the B-cell epitope dataset preparation pipeline.
    """

    logger.info("\n=======================================================")
    logger.info("--- Starting Bioinformatics Dataset Preparation Pipeline ---")
    logger.info("=======================================================\n")
    
    start_time = time.time()

    # STEP 1: Process Positive Data (IEDB_All)
    df_positives, positive_count = download_positive_data(output_filename=IEDB_CSV_FILE)

    if df_positives is None or df_positives.empty:
        logger.error("\n❌ Failure: Could not obtain positive data. Aborting.")
        return

    # STEP 2: Generate Negative Data (UNIPROT_RANDOM)
    df_negatives = generate_negative_data(positive_count, output_filename=UNIPROT_CSV_FILE)

    if df_negatives.empty:
        logger.error("\n❌ Failure: Could not generate negative data. Aborting.")
        return

    # STEP 3: Export Positives to FASTA (Sampled)
    sample_and_export_fasta(
        df=df_positives,
        output_fasta_name=IEDB_FASTA_FILE,
        step_label=f'FASTA Export IEDB (Sample of {TARGET_SAMPLE_SIZE})',
        sample_size=TARGET_SAMPLE_SIZE,
        dataset_type='IEDB'
    )

    # STEP 4: Export Negatives to FASTA (Sampled)
    sample_and_export_fasta(
        df=df_negatives,
        output_fasta_name=UNIPROT_FASTA_FILE,
        step_label=f'FASTA Export UniProt Random (Sample of {TARGET_SAMPLE_SIZE})',
        sample_size=TARGET_SAMPLE_SIZE,
        dataset_type='UNIPROT'
    )
    
    end_time = time.time()
    logger.info("\n🎉 Pipeline Complete! Reduced FASTA files are ready.")
    logger.info(f"Total execution time: {end_time - start_time:.2f} seconds.")


if __name__ == '__main__':
    run_data_pipeline()