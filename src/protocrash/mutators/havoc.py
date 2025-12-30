"""Havoc (random) mutation strategies"""
import random
class HavocMutator:
    """Random havoc mutations with stacking"""
    HAVOC_OPERATIONS = [
        "flip_bit",
        "flip_byte",
        "arithmetic",
        "delete_block",
        "clone_block",
        "overwrite_block",
        "insert_random",
    ]
    def mutate(self, data: bytes, iterations: int = 200) -> bytes:
        """
        Apply random sequence of mutations
        Args:
            data: Input data to mutate
            iterations: Number of random mutations to apply
        Returns:
            Mutated data
        """
        if len(data) == 0:
            return data
        result = data
        for _ in range(iterations):
            op = random.choice(self.HAVOC_OPERATIONS)
            result = self._apply_operation(result, op)
            # Don't let it grow too large
            if len(result) > len(data) * 10:
                result = result[: len(data) * 10]
        return result
    def _apply_operation(self, data: bytes, operation: str) -> bytes:
        """Apply single havoc operation"""
        if len(data) == 0:
            return data
        if operation == "flip_bit":
            pos = random.randint(0, len(data) * 8 - 1)
            return self._flip_bit(data, pos)
        elif operation == "flip_byte":
            pos = random.randint(0, len(data) - 1)
            result = bytearray(data)
            result[pos] ^= 0xFF
            return bytes(result)
        elif operation == "arithmetic":
            pos = random.randint(0, len(data) - 1)
            delta = random.randint(-35, 35)
            return self._add_to_byte(data, pos, delta)
        elif operation == "delete_block":
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                end = random.randint(start + 1, len(data))
                return data[:start] + data[end:]
        elif operation == "clone_block":
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                end = random.randint(start + 1, len(data))
                block = data[start:end]
                insert_pos = random.randint(0, len(data))
                return data[:insert_pos] + block + data[insert_pos:]
        elif operation == "overwrite_block":
            if len(data) > 2:
                start = random.randint(0, len(data) - 2)
                length = min(random.randint(1, 10), len(data) - start)
                end = start + length
                random_bytes = bytes([random.randint(0, 255) for _ in range(length)])
                return data[:start] + random_bytes + data[end:]
        elif operation == "insert_random":
            pos = random.randint(0, len(data))
            length = random.randint(1, 10)
            random_bytes = bytes([random.randint(0, 255) for _ in range(length)])
            return data[:pos] + random_bytes + data[pos:]
        return data
    def _flip_bit(self, data: bytes, position: int) -> bytes:
        """Flip single bit at position"""
        result = bytearray(data)
        byte_idx = position // 8
        bit_idx = position % 8
        result[byte_idx] ^= 1 << bit_idx
        return bytes(result)
    def _add_to_byte(self, data: bytes, pos: int, delta: int) -> bytes:
        """Add delta to byte at position"""
        result = bytearray(data)
        result[pos] = (result[pos] + delta) % 256
        return bytes(result)
