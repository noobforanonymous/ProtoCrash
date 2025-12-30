"""Coverage comparison utilities"""


class CoverageComparator:
    """Compare coverage maps to detect new coverage"""

    @staticmethod
    def has_new_bits(virgin_map: bytearray, trace_bits: bytearray) -> bool:
        """
        Fast coverage comparison using 64-bit chunks

        Args:
            virgin_map: Bitmap of unseen edges
            trace_bits: Current execution coverage

        Returns:
            True if new coverage found
        """
        if len(virgin_map) != len(trace_bits):
            return False

        # Process 8 bytes at a time for speed
        chunk_size = 8

        for i in range(0, len(virgin_map), chunk_size):
            # Get 8-byte chunks
            virgin_chunk = int.from_bytes(
                virgin_map[i:i+chunk_size], 'little', signed=False
            ) if i + chunk_size <= len(virgin_map) else 0

            trace_chunk = int.from_bytes(
                trace_bits[i:i+chunk_size], 'little', signed=False
            ) if i + chunk_size <= len(trace_bits) else 0

            # Check if any new bits
            if trace_chunk and (trace_chunk & virgin_chunk):
                return True

        return False

    @staticmethod
    def count_new_bits(virgin_map: bytearray, trace_bits: bytearray) -> int:
        """
        Count how many new bits were discovered

        Args:
            virgin_map: Bitmap of unseen edges
            trace_bits: Current execution coverage

        Returns:
            Number of new bits
        """
        new_bits = 0

        for i in range(len(virgin_map)):
            if i < len(trace_bits) and trace_bits[i]:
                # Count set bits that are also set in virgin map
                new_bits += bin(trace_bits[i] & virgin_map[i]).count('1')

        return new_bits

    @staticmethod
    def compare_bitmaps(bitmap1: bytearray, bitmap2: bytearray) -> float:
        """
        Calculate similarity between two bitmaps

        Args:
            bitmap1: First bitmap
            bitmap2: Second bitmap

        Returns:
            Similarity score 0.0 (different) to 1.0 (identical)
        """
        if len(bitmap1) != len(bitmap2):
            return 0.0

        matches = 0
        total = len(bitmap1)

        for i in range(total):
            if bitmap1[i] == bitmap2[i]:
                matches += 1

        return matches / total if total > 0 else 0.0
