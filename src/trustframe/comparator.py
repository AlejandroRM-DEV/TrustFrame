class VideoComparator:
    """
    Performs advanced comparison and alignment of video frame sequences.

    This class implements algorithms for comparing two sequences of perceptual
    hashes, detecting insertions, deletions, and modifications, and calculating
    similarity metrics.
    """

    def calculate_hamming_distance(self, hash1, hash2):
        """
        Calculate the Hamming distance between two hexadecimal hashes.

        The Hamming distance counts the number of bit positions where two
        hashes differ. This provides a quantitative measure of similarity
        between perceptual hashes.

        Args:
            hash1 (str): First hexadecimal hash
            hash2 (str): Second hexadecimal hash

        Returns:
            dict or None: Dictionary containing:
                - hamming_distance: Number of differing bits
                - max_bits: Maximum possible differing bits
                - similarity_percentage: Similarity as a percentage
            Returns None if hashes are invalid or incompatible.
        """
        if not hash1 or not hash2:
            return None

        if len(hash1) != len(hash2):
            return None

        try:
            # Convert hexadecimal strings to integers
            int1 = int(hash1, 16)
            int2 = int(hash2, 16)

            # XOR to find differing bits
            xor_result = int1 ^ int2

            # Count the number of 1s in the binary representation (differing bits)
            hamming_distance = bin(xor_result).count('1')

            # Calculate maximum possible differing bits (4 bits per hex character)
            max_bits = len(hash1) * 4

            # Calculate similarity percentage
            similarity = ((max_bits - hamming_distance) / max_bits) * 100

            return {
                'hamming_distance': hamming_distance,
                'max_bits': max_bits,
                'similarity_percentage': similarity
            }
        except ValueError:
            return None

    def find_longest_common_subsequence(self, seq1, seq2):
        """
        Find the longest common subsequence between two sequences.

        This algorithm uses dynamic programming to find the length of the
        longest subsequence that appears in both sequences in the same order
        (but not necessarily consecutive).

        Args:
            seq1 (list): First sequence
            seq2 (list): Second sequence

        Returns:
            int: Length of the longest common subsequence
        """
        m, n = len(seq1), len(seq2)

        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Fill the DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def align_sequences(self, ref_hashes, ev_hashes):
        """
        Align two sequences of hashes to detect insertions, deletions, and changes.

        This method implements the Wagner-Fischer algorithm (edit distance) to
        find the optimal alignment between two sequences, identifying all
        operations needed to transform one sequence into another.

        Args:
            ref_hashes (list): Reference video hash sequence
            ev_hashes (list): Evidence video hash sequence

        Returns:
            tuple: (alignment, edit_distance)
                - alignment: List of operation dictionaries describing the alignment
                - edit_distance: Total number of operations needed for transformation
        """
        # Extract hash strings for comparison
        ref_seq = [h['hash'] for h in ref_hashes]
        ev_seq = [h['hash'] for h in ev_hashes]

        m, n = len(ref_seq), len(ev_seq)

        # Initialize DP table for edit distance calculation
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Initialize first row and column (representing insertions/deletions from empty sequence)
        for i in range(m + 1):
            dp[i][0] = i  # Cost of deleting i characters
        for j in range(n + 1):
            dp[0][j] = j  # Cost of inserting j characters

        # Fill the DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_seq[i - 1] == ev_seq[j - 1]:
                    # No operation needed if hashes match
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    # Choose minimum cost operation
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],  # Deletion
                        dp[i][j - 1],  # Insertion
                        dp[i - 1][j - 1]  # Substitution
                    )

        # Reconstruct the alignment by backtracking through the DP table
        alignment = []
        i, j = m, n

        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_seq[i - 1] == ev_seq[j - 1]:
                # Exact match - no operation needed
                alignment.append({
                    'type': 'match',
                    'ref_frame': ref_hashes[i - 1]['frame_number'],
                    'ev_frame': ev_hashes[j - 1]['frame_number'],
                    'ref_hash': ref_seq[i - 1],
                    'ev_hash': ev_seq[j - 1]
                })
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
                # Substitution - different frames at corresponding positions
                alignment.append({
                    'type': 'substitution',
                    'ref_frame': ref_hashes[i - 1]['frame_number'],
                    'ev_frame': ev_hashes[j - 1]['frame_number'],
                    'ref_hash': ref_seq[i - 1],
                    'ev_hash': ev_seq[j - 1]
                })
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                # Deletion - frame exists in reference but not in evidence
                alignment.append({
                    'type': 'deletion',
                    'ref_frame': ref_hashes[i - 1]['frame_number'],
                    'ev_frame': None,
                    'ref_hash': ref_seq[i - 1],
                    'ev_hash': None
                })
                i -= 1
            elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
                # Insertion - frame exists in evidence but not in reference
                alignment.append({
                    'type': 'insertion',
                    'ref_frame': None,
                    'ev_frame': ev_hashes[j - 1]['frame_number'],
                    'ref_hash': None,
                    'ev_hash': ev_seq[j - 1]
                })
                j -= 1

        # Reverse alignment to get chronological order
        alignment.reverse()
        return alignment, dp[m][n]

    def analyze_differences(self, alignment):
        """
        Analyze the types and counts of differences found in the alignment.

        Args:
            alignment (list): List of alignment operations from align_sequences()

        Returns:
            dict: Statistics about the alignment including counts of each operation type
        """
        stats = {
            'matches': 0,
            'substitutions': 0,
            'insertions': 0,
            'deletions': 0,
            'total_operations': len(alignment)
        }

        # Map operation types to their plural forms for statistics
        plural_map = {
            'match': 'matches',
            'substitution': 'substitutions',
            'insertion': 'insertions',
            'deletion': 'deletions'
        }

        # Count each type of operation
        for op in alignment:
            key = plural_map[op['type']]
            stats[key] += 1

        return stats
