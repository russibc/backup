# config.py

import logging
import os

# ------------------------------------------------------------------------------
# FILE PATHS AND NAMES
# ------------------------------------------------------------------------------
IEDB_CSV_FILE = "iedb_all_valid.csv"
UNIPROT_CSV_FILE = "uniprot_random.csv"
IEDB_FASTA_FILE = "iedb.fasta"
UNIPROT_FASTA_FILE = "uniprot_random.fasta"
LOG_FILE = "logs/pipeline_execution.log"

# ------------------------------------------------------------------------------
# PIPELINE PARAMETERS
# ------------------------------------------------------------------------------
TARGET_SAMPLE_SIZE = 5000
MIN_PEPTIDE_LENGTH = 10
MAX_PEPTIDE_LENGTH = 30

# ------------------------------------------------------------------------------
# IEDB QUERY API CONFIGURATION (New Robust Method)
# ------------------------------------------------------------------------------
IEDB_QUERY_URL = "https://query-api.iedb.org/bcell_export"
IEDB_EPITOPE_BASE_URL = "http://www.iedb.org/epitope/"
IEDB_PAGINATION_LIMIT = 10000 

# IEDB API filtering parameters (as key-value tuples)
IEDB_BASE_PARAMS_LIST = [
    ("assay__qualitative_measure", "eq.Positive"),
    ("epitope__object_type", "eq.Linear peptide"),
    ("reference__type", "in.(Literature,Dual)"),
    ("order", "assay_id.asc"),
]

# Column names to look for in the raw IEDB export (based on API response)
IEDB_SEQUENCE_CANDIDATES = ["epitope_linear_sequence", "epitope_sequence", "linear_epitope_sequence", "epitope_name", "sequence"]
IEDB_ORGANISM_CANDIDATES = ["epitope_source_organism_name", "organism_name", "epitope_source_organism"]
IEDB_PROTEIN_CANDIDATES = ["source_antigen_full_name", "source_antigen_name", "antigen_name"]

# ------------------------------------------------------------------------------
# UNIPROT CONFIGURATION
# ------------------------------------------------------------------------------
UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/stream"
UNIPROT_PARAMS = {'query': 'reviewed:true', 'format': 'fasta', 'size': 50000}

# ------------------------------------------------------------------------------
# PIPELINE PARAMETERS
# ------------------------------------------------------------------------------
MIN_PEPTIDE_LENGTH = 10
MAX_PEPTIDE_LENGTH = 30

# ------------------------------------------------------------------------------
# GENERAL REQUEST HEADERS
# ------------------------------------------------------------------------------
DEFAULT_REQUEST_HEADERS = {
    'accept': 'text/csv', 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ------------------------------------------------------------------------------
# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
LOG_CONFIG = {
    'level': logging.INFO,
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'handlers': [
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
}

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)