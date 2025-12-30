"""Corpus management for fuzzing"""

import hashlib
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import random


@dataclass
class CorpusEntry:
    """Metadata for a corpus entry"""
    input_hash: str
    size: int
    coverage_edges: int
    execution_count: int
    found_new_coverage: bool
    timestamp: float


class CorpusManager:
    """Manage fuzzing corpus (seeds and interesting inputs)"""

    def __init__(self, corpus_dir: str):
        """
        Initialize corpus manager

        Args:
            corpus_dir: Directory to store corpus files
        """
        self.corpus_dir = Path(corpus_dir)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.corpus_dir / "metadata.json"
        self.entries: Dict[str, CorpusEntry] = {}

        # Load existing corpus
        self._load_metadata()

    def add_input(self, input_data: bytes, coverage_edges: int = 0,
                  found_new_coverage: bool = False) -> str:
        """
        Add input to corpus

        Args:
            input_data: Input data to add
            coverage_edges: Number of coverage edges hit
            found_new_coverage: Whether this input found new coverage

        Returns:
            Input hash
        """
        # Calculate hash
        input_hash = hashlib.sha256(input_data).hexdigest()[:16]

        # Skip if duplicate
        if input_hash in self.entries:
            return input_hash

        # Save input file
        input_file = self.corpus_dir / f"{input_hash}.input"
        input_file.write_bytes(input_data)

        # Create metadata entry
        import time
        entry = CorpusEntry(
            input_hash=input_hash,
            size=len(input_data),
            coverage_edges=coverage_edges,
            execution_count=0,
            found_new_coverage=found_new_coverage,
            timestamp=time.time()
        )

        self.entries[input_hash] = entry
        self._save_metadata()

        return input_hash

    def get_input(self, input_hash: str) -> Optional[bytes]:
        """
        Get input data by hash

        Args:
            input_hash: Input hash

        Returns:
            Input data or None if not found
        """
        if input_hash not in self.entries:
            return None

        input_file = self.corpus_dir / f"{input_hash}.input"
        if not input_file.exists():
            return None

        return input_file.read_bytes()

    def get_random_input(self) -> Optional[bytes]:
        """
        Get random input from corpus

        Returns:
            Random input data or None if corpus empty
        """
        if not self.entries:
            return None

        input_hash = random.choice(list(self.entries.keys()))
        return self.get_input(input_hash)

    def get_all_hashes(self) -> List[str]:
        """
        Get all input hashes

        Returns:
            List of input hashes
        """
        return list(self.entries.keys())

    def increment_execution_count(self, input_hash: str) -> None:
        """
        Increment execution count for input

        Args:
            input_hash: Input hash
        """
        if input_hash in self.entries:
            self.entries[input_hash].execution_count += 1
            self._save_metadata()

    def get_size(self) -> int:
        """
        Get corpus size

        Returns:
            Number of inputs in corpus
        """
        return len(self.entries)

    def get_metadata(self, input_hash: str) -> Optional[CorpusEntry]:
        """
        Get metadata for input

        Args:
            input_hash: Input hash

        Returns:
            CorpusEntry or None if not found
        """
        return self.entries.get(input_hash)

    def _load_metadata(self) -> None:
        """Load metadata from disk and scan for seed files"""
        # Load existing metadata
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text())
                for entry_dict in data:
                    entry = CorpusEntry(**entry_dict)
                    self.entries[entry.input_hash] = entry
            except Exception:
                # Corrupt metadata, start fresh
                pass

        # Scan for files not in metadata (seed files)

        for file_path in self.corpus_dir.iterdir():
            if file_path.is_file() and file_path.name != "metadata.json":
                try:
                    data = file_path.read_bytes()
                    if data:
                        input_hash = hashlib.sha256(data).hexdigest()[:16]
                        if input_hash not in self.entries:
                            # Add as new seed
                            self.entries[input_hash] = CorpusEntry(
                                input_hash=input_hash,
                                size=len(data),
                                timestamp=file_path.stat().st_mtime,
                                execution_count=0,
                                coverage_edges=0,
                                found_new_coverage=False
                            )
                            # Copy file to hash-named version with .input extension
                            hash_file = self.corpus_dir / f"{input_hash}.input"
                            if not hash_file.exists():
                                hash_file.write_bytes(data)
                except Exception:
                    continue



    def _save_metadata(self) -> None:
        """Save metadata to disk"""
        data = [asdict(entry) for entry in self.entries.values()]
        self.metadata_file.write_text(json.dumps(data, indent=2))

    def export_stats(self) -> Dict[str, Any]:
        """
        Export corpus statistics

        Returns:
            Dictionary of statistics
        """
        if not self.entries:
            return {
                "corpus_size": 0,
                "total_size_bytes": 0,
                "avg_input_size": 0,
                "new_coverage_inputs": 0
            }

        total_size = sum(entry.size for entry in self.entries.values())
        new_coverage_count = sum(1 for entry in self.entries.values()
                                 if entry.found_new_coverage)

        return {
            "corpus_size": len(self.entries),
            "total_size_bytes": total_size,
            "avg_input_size": total_size / len(self.entries),
            "new_coverage_inputs": new_coverage_count
        }
