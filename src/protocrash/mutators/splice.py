"""Splice (crossover) mutations"""

import random


class SpliceMutator:
    """Splice/crossover mutations between inputs"""

    def crossover(self, input1: bytes, input2: bytes) -> bytes:
        """
        Combine two inputs via crossover

        Args:
            input1: First input
            input2: Second input

        Returns:
            Combined input
        """
        if len(input1) < 2 or len(input2) < 2:
            return input1

        # Random split points
        split1 = random.randint(1, len(input1) - 1)
        split2 = random.randint(1, len(input2) - 1)

        return input1[:split1] + input2[split2:]

    def multi_crossover(self, inputs: list[bytes], count: int = 3) -> bytes:
        """
        Combine multiple inputs

        Args:
            inputs: List of inputs
            count: Number of inputs to combine

        Returns:
            Combined input
        """
        if not inputs:
            return b""

        if len(inputs) == 1:
            return inputs[0]

        # Select random inputs to combine
        selected = random.sample(inputs, min(count, len(inputs)))

        if len(selected) == 1:
            return selected[0]

        # Progressively crossover
        result = selected[0]
        for inp in selected[1:]:
            result = self.crossover(result, inp)

        return result
