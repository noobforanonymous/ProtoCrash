"""Deterministic mutation strategies"""

from typing import List

# Pre-compute interesting values as bytes for faster mutations
_INTERESTING_8_BYTES = [v.to_bytes(1, 'little', signed=True) if v < 0 else v.to_bytes(1, 'little')
                        for v in [-128, -1, 0, 1, 16, 32, 64, 100, 127]]
_INTERESTING_16_BYTES = [v.to_bytes(2, 'little', signed=True) if v < 0 else v.to_bytes(2, 'little')
                         for v in [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]]
_INTERESTING_32_BYTES = [v.to_bytes(4, 'little', signed=True) if v < 0 else v.to_bytes(4, 'little')
                         for v in [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]]


class DeterministicMutator:
    """Systematic deterministic mutations (AFL-style)"""

    def bit_flips(self, data: bytes, flip_counts: List[int] = None) -> List[bytes]:
        """
        Generate bit flip mutations

        Args:
            data: Input data to mutate
            flip_counts: List of bit counts to flip (default: [1, 2, 4])

        Returns:
            List of mutated inputs
        """
        if flip_counts is None:
            flip_counts = [1, 2, 4]

        mutations = []

        for count in flip_counts:
            for bit_pos in range(len(data) * 8 - count + 1):
                mutated = self._flip_bits(data, bit_pos, count)
                mutations.append(mutated)

        return mutations

    def _flip_bits(self, data: bytes, position: int, count: int) -> bytes:
        """Flip 'count' consecutive bits starting at position (optimized)"""
        result = bytearray(data)

        # Optimized: use divmod and reduce loop iterations
        for i in range(count):
            bit_pos = position + i
            byte_idx, bit_idx = divmod(bit_pos, 8)

            if byte_idx < len(result):
                result[byte_idx] ^= 1 << bit_idx

        return bytes(result)

    def byte_flips(self, data: bytes, flip_sizes: List[int] = None) -> List[bytes]:
        """
        Generate byte flip mutations

        Args:
            data: Input data to mutate
            flip_sizes: List of byte counts to flip (default: [1, 2, 4])

        Returns:
            List of mutated inputs
        """
        if flip_sizes is None:
            flip_sizes = [1, 2, 4]

        mutations = []

        for size in flip_sizes:
            for pos in range(len(data) - size + 1):
                mutated = self._flip_bytes(data, pos, size)
                mutations.append(mutated)

        return mutations

    def _flip_bytes(self, data: bytes, position: int, count: int) -> bytes:
        """Flip 'count' consecutive bytes (XOR with 0xFF)"""
        result = bytearray(data)

        for i in range(count):
            if position + i < len(result):
                result[position + i] ^= 0xFF

        return bytes(result)

    def arithmetic(
        self, data: bytes, deltas: List[int] = None, sizes: List[int] = None
    ) -> List[bytes]:
        """
        Generate arithmetic mutations (add/subtract)

        Args:
            data: Input data to mutate
            deltas: Values to add/subtract (default: [-35, -1, 1, 8, 16, 32])
            sizes: Integer sizes in bytes (default: [1, 2, 4])

        Returns:
            List of mutated inputs
        """
        if deltas is None:
            deltas = [-35, -1, 1, 8, 16, 32]
        if sizes is None:
            sizes = [1, 2, 4]

        mutations = []

        for pos in range(len(data)):
            for delta in deltas:
                for size in sizes:
                    if pos + size <= len(data):
                        mutated = self._arithmetic_mutate(data, pos, delta, size)
                        mutations.append(mutated)

        return mutations

    def _arithmetic_mutate(self, data: bytes, pos: int, delta: int, size: int) -> bytes:
        """Add delta to integer at position (optimized)"""
        result = bytearray(data)

        # Extract value (little-endian)
        value = int.from_bytes(result[pos : pos + size], "little")

        # Apply arithmetic with wrap-around (optimized: use bitwise AND instead of modulo)
        mask = (1 << (size * 8)) - 1
        new_value = (value + delta) & mask

        # Write back
        result[pos : pos + size] = new_value.to_bytes(size, "little")

        return bytes(result)

    def interesting_values(self, data: bytes) -> List[bytes]:
        """
        Replace with AFL interesting values (optimized with pre-computed bytes)

        Returns:
            List of mutated inputs with interesting boundary values
        """
        mutations = []
        data_array = bytearray(data)

        for pos in range(len(data)):
            # 8-bit values (optimized: use pre-computed bytes)
            for val_bytes in _INTERESTING_8_BYTES:
                result = bytearray(data_array)
                result[pos:pos+1] = val_bytes
                mutations.append(bytes(result))

            # 16-bit values
            if pos + 2 <= len(data):
                for val_bytes in _INTERESTING_16_BYTES:
                    result = bytearray(data_array)
                    result[pos:pos+2] = val_bytes
                    mutations.append(bytes(result))

            # 32-bit values
            if pos + 4 <= len(data):
                for val_bytes in _INTERESTING_32_BYTES:
                    result = bytearray(data_array)
                    result[pos:pos+4] = val_bytes
                    mutations.append(bytes(result))

        return mutations

    def _replace_int(self, data: bytes, pos: int, value: int, size: int) -> bytes:
        """Replace integer at position with value"""
        result = bytearray(data)

        # Handle negative values (two's complement)
        if value < 0:
            value = (1 << (size * 8)) + value

        # Clamp to size
        value = value % (256**size)

        result[pos : pos + size] = value.to_bytes(size, "little")

        return bytes(result)
