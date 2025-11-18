"""Deduplication service for removing duplicate records."""
from typing import Any, Dict, List, Optional
import pandas as pd
import hashlib
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class DeduplicationService:
    """Service for removing duplicate records."""

    def __init__(self):
        self.logger = logger

    def deduplicate(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Remove duplicates from DataFrame.

        Args:
            df: Input DataFrame
            config: Deduplication configuration

        Returns:
            Tuple of (deduplicated DataFrame, deduplication report)
        """
        original_count = len(df)
        strategy = config.get("strategy", "exact")
        subset = config.get("subset", None)  # Columns to consider
        keep = config.get("keep", "first")  # first, last, False

        if strategy == "exact":
            result_df = self._exact_deduplication(df, subset, keep)
        elif strategy == "fuzzy":
            result_df = self._fuzzy_deduplication(df, config)
        elif strategy == "hash":
            result_df = self._hash_deduplication(df, subset, keep)
        else:
            self.logger.warning(f"Unknown deduplication strategy: {strategy}, using exact")
            result_df = self._exact_deduplication(df, subset, keep)

        deduplicated_count = len(result_df)
        duplicates_removed = original_count - deduplicated_count

        report = {
            "original_count": original_count,
            "deduplicated_count": deduplicated_count,
            "duplicates_removed": duplicates_removed,
            "duplicate_percentage": (duplicates_removed / original_count * 100) if original_count > 0 else 0,
            "strategy": strategy,
        }

        self.logger.info(f"Removed {duplicates_removed} duplicates ({report['duplicate_percentage']:.2f}%)")

        return result_df, report

    def _exact_deduplication(
        self, df: pd.DataFrame, subset: Optional[List[str]], keep: str
    ) -> pd.DataFrame:
        """Remove exact duplicates."""
        return df.drop_duplicates(subset=subset, keep=keep)

    def _hash_deduplication(
        self, df: pd.DataFrame, subset: Optional[List[str]], keep: str
    ) -> pd.DataFrame:
        """Remove duplicates using hash comparison."""
        temp_df = df.copy()

        # Create hash column
        if subset:
            temp_df["_hash"] = temp_df[subset].apply(
                lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), axis=1
            )
        else:
            temp_df["_hash"] = temp_df.apply(
                lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), axis=1
            )

        # Remove duplicates based on hash
        result_df = temp_df.drop_duplicates(subset=["_hash"], keep=keep)
        result_df = result_df.drop(columns=["_hash"])

        return result_df

    def _fuzzy_deduplication(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Remove fuzzy duplicates (similar records).
        Note: This is a basic implementation. For production, consider using libraries like dedupe or fuzzywuzzy.
        """
        from difflib import SequenceMatcher

        similarity_threshold = config.get("similarity_threshold", 0.9)
        compare_columns = config.get("subset", df.columns.tolist())

        result_df = df.copy()
        to_remove = set()

        for i in range(len(result_df)):
            if i in to_remove:
                continue

            for j in range(i + 1, len(result_df)):
                if j in to_remove:
                    continue

                # Calculate similarity
                similarity_scores = []
                for col in compare_columns:
                    if col in result_df.columns:
                        val1 = str(result_df.iloc[i][col])
                        val2 = str(result_df.iloc[j][col])
                        similarity = SequenceMatcher(None, val1, val2).ratio()
                        similarity_scores.append(similarity)

                avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0

                if avg_similarity >= similarity_threshold:
                    to_remove.add(j)

        # Remove fuzzy duplicates
        result_df = result_df.drop(index=list(to_remove)).reset_index(drop=True)

        return result_df

    def identify_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Identify and return duplicate records."""
        duplicates = df[df.duplicated(subset=subset, keep=False)]
        return duplicates.sort_values(by=subset if subset else df.columns.tolist())

    def get_duplicate_groups(
        self, df: pd.DataFrame, subset: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """Get groups of duplicate records."""
        duplicates = self.identify_duplicates(df, subset)

        if len(duplicates) == 0:
            return {}

        # Create hash for grouping
        if subset:
            duplicates["_group_hash"] = duplicates[subset].apply(
                lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), axis=1
            )
        else:
            duplicates["_group_hash"] = duplicates.apply(
                lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), axis=1
            )

        # Group by hash
        groups = {}
        for hash_val in duplicates["_group_hash"].unique():
            group_df = duplicates[duplicates["_group_hash"] == hash_val].drop(columns=["_group_hash"])
            groups[hash_val] = group_df

        return groups
