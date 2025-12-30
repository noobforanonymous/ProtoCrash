"""Main mutation engine coordinator"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from protocrash.mutators.deterministic import DeterministicMutator
from protocrash.mutators.havoc import HavocMutator
from protocrash.mutators.dictionary import DictionaryManager
from protocrash.mutators.splice import SpliceMutator


@dataclass
class MutationConfig:
    """Configuration for mutation engine"""

    deterministic_enabled: bool = True
    havoc_enabled: bool = True
    dictionary_enabled: bool = True
    splice_enabled: bool = True

    # Mutation budgets
    deterministic_iterations: int = 1000
    havoc_iterations: int = 200
    splice_attempts: int = 10

    # Weights for mutation selection
    mutation_weights: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.mutation_weights is None:
            self.mutation_weights = {
                "bit_flip": 0.2,
                "byte_flip": 0.15,
                "arithmetic": 0.15,
                "interesting": 0.1,
                "havoc": 0.25,
                "dictionary": 0.1,
                "splice": 0.05,
            }


class MutationEngine:
    """Main mutation engine coordinator"""

    def __init__(self, config: Optional[MutationConfig] = None):
        self.config = config or MutationConfig()

        # Initialize mutators
        self.deterministic = DeterministicMutator()
        self.havoc = HavocMutator()
        self.dictionary = DictionaryManager()
        self.splice = SpliceMutator()

        # Track mutation effectiveness
        self.mutation_stats: Dict[str, Dict[str, int]] = {}

        # Corpus for splice mutations
        self.corpus: List[bytes] = []

    def mutate(self, input_data: bytes, strategy: str = "auto") -> bytes:
        """
        Main mutation entry point

        Args:
            input_data: Input to mutate
            strategy: Mutation strategy (auto, deterministic, havoc, etc.)

        Returns:
            Mutated input
        """
        if len(input_data) == 0:
            return input_data

        if strategy == "auto":
            strategy = self._select_strategy()

        if strategy == "deterministic":
            return self._mutate_deterministic(input_data)
        elif strategy == "bit_flip":
            mutations = self.deterministic.bit_flips(input_data)
            return random.choice(mutations) if mutations else input_data
        elif strategy == "byte_flip":
            mutations = self.deterministic.byte_flips(input_data)
            return random.choice(mutations) if mutations else input_data
        elif strategy == "arithmetic":
            mutations = self.deterministic.arithmetic(input_data)
            return random.choice(mutations) if mutations else input_data
        elif strategy == "interesting":
            mutations = self.deterministic.interesting_values(input_data)
            return random.choice(mutations) if mutations else input_data
        elif strategy == "havoc":
            return self.havoc.mutate(input_data, self.config.havoc_iterations)
        elif strategy == "dictionary":
            return self.dictionary.inject(input_data)
        elif strategy == "splice":
            if self.corpus:
                partner = random.choice(self.corpus)
                return self.splice.crossover(input_data, partner)
            return input_data
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def mutate_batch(self, input_data: bytes, count: int) -> List[bytes]:
        """
        Generate multiple mutations

        Args:
            input_data: Input to mutate
            count: Number of mutations to generate

        Returns:
            List of mutated inputs
        """
        mutations = []
        for _ in range(count):
            mutations.append(self.mutate(input_data))
        return mutations

    def _select_strategy(self) -> str:
        """Select mutation strategy based on weights"""
        strategies = list(self.config.mutation_weights.keys())
        weights = list(self.config.mutation_weights.values())

        return random.choices(strategies, weights=weights)[0]

    def _mutate_deterministic(self, data: bytes) -> bytes:
        """Run deterministic mutation stage"""
        # Randomly select one deterministic strategy
        strategies = ["bit_flip", "byte_flip", "arithmetic", "interesting"]
        strategy = random.choice(strategies)

        if strategy == "bit_flip":
            mutations = self.deterministic.bit_flips(data)
        elif strategy == "byte_flip":
            mutations = self.deterministic.byte_flips(data)
        elif strategy == "arithmetic":
            mutations = self.deterministic.arithmetic(data)
        else:  # interesting
            mutations = self.deterministic.interesting_values(data)

        return random.choice(mutations) if mutations else data

    def update_effectiveness(self, strategy: str, found_coverage: bool) -> None:
        """
        Update mutation effectiveness tracking

        Args:
            strategy: Mutation strategy used
            found_coverage: Whether new coverage was found
        """
        if strategy not in self.mutation_stats:
            self.mutation_stats[strategy] = {"attempts": 0, "successes": 0}

        self.mutation_stats[strategy]["attempts"] += 1
        if found_coverage:
            self.mutation_stats[strategy]["successes"] += 1

            # Increase weight for successful strategy
            if strategy in self.config.mutation_weights:
                success_rate = (
                    self.mutation_stats[strategy]["successes"]
                    / self.mutation_stats[strategy]["attempts"]
                )
                self.config.mutation_weights[strategy] *= 1 + success_rate * 0.1

    def set_corpus(self, corpus: List[bytes]) -> None:
        """
        Set corpus for splice mutations

        Args:
            corpus: List of inputs in corpus
        """
        self.corpus = corpus

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get mutation statistics"""
        return self.mutation_stats
