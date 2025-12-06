"""
Knowledge Curator for Brian Coder (ACE-inspired)

Manages node lifecycle in the knowledge graph:
- DELETE: Remove harmful nodes (harmful > helpful)
- PRUNE: Remove unused nodes (30+ days without use)
- MERGE: Combine similar nodes (Phase 4)

Inspired by ACE framework's Curator agent that manages playbook evolution.

Zero-dependency (uses only graph_lite.py).
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import config


class KnowledgeCurator:
    """
    ACE-style curator that manages node quality and lifecycle.

    Periodically runs curation to:
    1. Delete harmful nodes (harmful_count > helpful_count)
    2. Prune unused nodes (no usage for 30+ days)
    3. Merge similar nodes (future - Phase 4)

    Example usage:
        curator = KnowledgeCurator(graph_lite)
        stats = curator.curate()
        print(f"Deleted: {stats['deleted_harmful']}, Pruned: {stats['pruned_unused']}")
    """

    def __init__(self, graph_lite, llm_call_func=None):
        """
        Initialize KnowledgeCurator.

        Args:
            graph_lite: GraphLite instance to curate
            llm_call_func: Optional LLM function for merge decisions
        """
        self.graph = graph_lite
        self.llm_call_func = llm_call_func

    def curate(self, save: bool = True) -> Dict[str, int]:
        """
        Run full curation cycle.

        Args:
            save: Whether to save graph after curation

        Returns:
            Dict with counts: deleted_harmful, pruned_unused, merged_groups, total_before, total_after
        """
        stats = {
            'deleted_harmful': 0,
            'pruned_unused': 0,
            'merged_groups': 0,
            'total_before': len(self.graph.nodes)
        }

        # Phase 1: Delete harmful nodes
        stats['deleted_harmful'] = self._delete_harmful_nodes()

        # Phase 2: Prune unused nodes
        prune_days = getattr(config, 'CURATOR_PRUNE_DAYS', 30)
        stats['pruned_unused'] = self._prune_unused_nodes(days=prune_days)

        # Phase 3: Merge similar nodes (if enabled - Phase 4 implementation)
        if getattr(config, 'ENABLE_NODE_MERGE', False):
            stats['merged_groups'] = self._merge_similar_nodes()

        stats['total_after'] = len(self.graph.nodes)

        # Save if requested
        if save and (stats['deleted_harmful'] > 0 or stats['pruned_unused'] > 0 or stats['merged_groups'] > 0):
            self.graph.save()

        return stats

    def _delete_harmful_nodes(self) -> int:
        """
        Delete nodes where harmful_count > helpful_count.

        ACE-style rule: If a knowledge node has been harmful more often than helpful,
        it's probably misleading and should be removed.

        Additional safeguard: Only delete if harmful_count >= 2 to avoid
        removing nodes that just had one bad experience.

        Returns:
            Number of deleted nodes
        """
        nodes_to_delete = []

        for node_id, node in self.graph.nodes.items():
            # ACE rule: harmful > helpful AND harmful >= threshold
            harmful_threshold = getattr(config, 'CURATOR_HARMFUL_THRESHOLD', 2)

            if node.harmful_count > node.helpful_count and node.harmful_count >= harmful_threshold:
                nodes_to_delete.append(node_id)
                if config.DEBUG_MODE:
                    print(f"  [Curator] Deleting harmful node: {node_id} "
                          f"(helpful={node.helpful_count}, harmful={node.harmful_count})")

        for node_id in nodes_to_delete:
            self.graph.delete_node(node_id)

        return len(nodes_to_delete)

    def _prune_unused_nodes(self, days: int = 30) -> int:
        """
        Remove nodes not used for specified days.

        Logic:
        1. Never-used nodes older than threshold -> delete
        2. Previously used but inactive for too long AND low quality -> delete

        Args:
            days: Number of days of inactivity before pruning

        Returns:
            Number of pruned nodes
        """
        threshold = datetime.now() - timedelta(days=days)
        nodes_to_prune = []

        for node_id, node in self.graph.nodes.items():
            # Case 1: Never used and old
            if node.usage_count == 0:
                try:
                    created = datetime.fromisoformat(node.created_at)
                    if created < threshold:
                        nodes_to_prune.append(node_id)
                        if config.DEBUG_MODE:
                            print(f"  [Curator] Pruning unused node: {node_id} "
                                  f"(created {days}+ days ago, never used)")
                except:
                    pass
                continue

            # Case 2: Used before but inactive AND low quality
            if node.last_used_at:
                try:
                    last_used = datetime.fromisoformat(node.last_used_at)
                    if last_used < threshold:
                        # Only prune if quality is low
                        quality = self.graph.get_node_quality_score(node)
                        if quality < 0.3:  # Not predominantly helpful
                            nodes_to_prune.append(node_id)
                            if config.DEBUG_MODE:
                                print(f"  [Curator] Pruning inactive low-quality node: {node_id} "
                                      f"(quality={quality:.2f}, last_used {days}+ days ago)")
                except:
                    pass

        for node_id in nodes_to_prune:
            self.graph.delete_node(node_id)

        return len(nodes_to_prune)

    def _merge_similar_nodes(self) -> int:
        """
        Find and merge similar nodes (Phase 4 implementation).

        Uses embedding similarity to find groups of similar nodes,
        then merges them pairwise.

        Returns:
            Number of merge operations performed
        """
        if not hasattr(self.graph, 'find_similar_nodes'):
            return 0

        threshold = getattr(config, 'MERGE_SIMILARITY_THRESHOLD', 0.85)
        groups = self.graph.find_similar_nodes(threshold=threshold)

        merged_count = 0
        for group in groups:
            if len(group) >= 2:
                # Get actual Node objects from IDs
                nodes = []
                for node_id in group:
                    node = self.graph.nodes.get(node_id)
                    if node:
                        nodes.append(node)
                
                if len(nodes) < 2:
                    continue
                
                # Merge pairwise: merge all into the first node
                base_node = nodes[0]
                for other_node in nodes[1:]:
                    try:
                        base_node = self.graph.merge_nodes(base_node, other_node)
                        merged_count += 1
                        if config.DEBUG_MODE:
                            print(f"  [Curator] Merged {other_node.id} into {base_node.id}")
                    except Exception as e:
                        if config.DEBUG_MODE:
                            print(f"  [Curator] Merge failed: {e}")

        return merged_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about node quality distribution.

        Returns:
            Dictionary with quality distribution stats:
            - total_nodes: Total number of nodes
            - high_quality: Nodes with quality > 0.5
            - neutral: Nodes with -0.3 <= quality <= 0.5
            - low_quality: Nodes with quality < -0.3
            - never_used: Nodes with usage_count == 0
            - total_helpful: Sum of all helpful_count
            - total_harmful: Sum of all harmful_count
        """
        return self.graph.get_node_stats()

    def get_candidates_for_deletion(self) -> List[Dict[str, Any]]:
        """
        Get list of nodes that would be deleted in next curation.
        Useful for preview before actual curation.

        Returns:
            List of dicts with node info and deletion reason
        """
        candidates = []
        harmful_threshold = getattr(config, 'CURATOR_HARMFUL_THRESHOLD', 2)
        prune_days = getattr(config, 'CURATOR_PRUNE_DAYS', 30)
        threshold_date = datetime.now() - timedelta(days=prune_days)

        for node_id, node in self.graph.nodes.items():
            # Check for harmful
            if node.harmful_count > node.helpful_count and node.harmful_count >= harmful_threshold:
                candidates.append({
                    'node_id': node_id,
                    'reason': 'harmful',
                    'helpful': node.helpful_count,
                    'harmful': node.harmful_count,
                    'quality': self.graph.get_node_quality_score(node)
                })
                continue

            # Check for never-used old nodes
            if node.usage_count == 0:
                try:
                    created = datetime.fromisoformat(node.created_at)
                    if created < threshold_date:
                        candidates.append({
                            'node_id': node_id,
                            'reason': 'never_used',
                            'created_at': node.created_at,
                            'age_days': (datetime.now() - created).days
                        })
                except:
                    pass
                continue

            # Check for inactive low-quality
            if node.last_used_at:
                try:
                    last_used = datetime.fromisoformat(node.last_used_at)
                    quality = self.graph.get_node_quality_score(node)
                    if last_used < threshold_date and quality < 0.3:
                        candidates.append({
                            'node_id': node_id,
                            'reason': 'inactive_low_quality',
                            'last_used': node.last_used_at,
                            'quality': quality,
                            'inactive_days': (datetime.now() - last_used).days
                        })
                except:
                    pass

        return candidates

    def print_summary(self):
        """Print a formatted summary of the graph's health."""
        stats = self.get_stats()
        candidates = self.get_candidates_for_deletion()

        print("\n" + "=" * 50)
        print("Knowledge Graph Health Report")
        print("=" * 50)
        print(f"Total nodes:        {stats['total_nodes']}")
        print(f"  High quality:     {stats['high_quality']} (quality > 0.5)")
        print(f"  Neutral:          {stats['neutral']} (-0.3 <= quality <= 0.5)")
        print(f"  Low quality:      {stats['low_quality']} (quality < -0.3)")
        print(f"  Never used:       {stats['never_used']}")
        print(f"Total helpful:      {stats['total_helpful']}")
        print(f"Total harmful:      {stats['total_harmful']}")
        print(f"\nDeletion candidates: {len(candidates)}")

        if candidates:
            print("\nNodes scheduled for deletion:")
            for c in candidates[:5]:  # Show first 5
                print(f"  - {c['node_id'][:20]}... ({c['reason']})")
            if len(candidates) > 5:
                print(f"  ... and {len(candidates) - 5} more")

        print("=" * 50 + "\n")
