# agentic2/modules/versioning.py
import glob
import os
import re

def get_next_versioned_path(base_name: str, folder: str = ".", ext: str = "csv") -> str:
    """Retorna o próximo caminho versionado, ex: cb_rates_001.csv, cb_rates_002.csv..."""
    pattern = os.path.join(folder, f"{base_name}_*.{ext}")
    existing = glob.glob(pattern)

    max_n = 0
    for f in existing:
        match = re.search(rf"{base_name}_(\d+)\.{ext}$", os.path.basename(f))
        if match:
            max_n = max(max_n, int(match.group(1)))

    return os.path.join(folder, f"{base_name}_{max_n + 1:03d}.{ext}")