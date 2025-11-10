"""Dependency graph visualization.

Generates course prerequisite dependency tree/DAG visualization.
Supports cycle detection, focus mode, and layered layout.
"""

from __future__ import annotations

import os
from typing import Dict, Set, Tuple, List, Optional

try:
    import networkx as nx  # type: ignore
    import matplotlib.pyplot as plt  # type: ignore
    import matplotlib.cm as cm  # type: ignore
    import matplotlib.patches as mpatches  # type: ignore
    import numpy as np  # type: ignore
except ImportError as e:  # pragma: no cover
    raise RuntimeError("networkx and matplotlib are required. Install: pip install networkx matplotlib") from e

from .common import load_relations, load_exclusions, build_graph


def remove_transitive_edges(g):
    """Remove transitive (redundant) edges from the graph.
    
    If there's a path A → B → C and also a direct edge A → C,
    remove A → C because it's redundant (transitive).
    
    This simplifies the visualization by keeping only direct dependencies.
    
    Args:
        g: NetworkX directed graph
        
    Returns:
        New graph with transitive edges removed
    """
    # Use NetworkX's transitive_reduction
    # This returns a new graph with the minimal set of edges
    try:
        # transitive_reduction removes edges that can be inferred from other paths
        reduced = nx.transitive_reduction(g)
        
        # Copy node attributes from original graph
        for node in reduced.nodes():
            if node in g.nodes:
                reduced.nodes[node].update(g.nodes[node])
        
        return reduced
    except Exception:
        # If reduction fails (e.g., cycles), return original graph
        return g


def find_roots(g) -> List[str]:
    """Find courses with no prerequisites (in-degree == 0)."""
    return [n for n in g.nodes if g.in_degree(n) == 0]


def detect_cycles(g) -> List[List[str]]:
    """Detect all cycles in the graph."""
    try:
        return list(nx.simple_cycles(g))
    except Exception:
        return []


def layered_layout(g, max_per_layer: Optional[int] = None, separate_roots: bool = False):
    """Compute a tree-like layered layout from bottom to top.
    
    Layout rules:
      1. Root nodes (no prerequisites) at the bottom (y=0)
      2. Higher layers for courses that depend on lower layers
      3. If a layer has more than max_per_layer nodes, split into sub-layers
      4. Sub-layers are inserted between main layers with proportional y spacing
      
    Args:
        g: NetworkX directed graph
        max_per_layer: Maximum nodes per row. If exceeded, create sub-layers.
        separate_roots: Legacy parameter, ignored (roots are always at bottom)
    
    Returns:
        Dictionary mapping node -> (x, y) position
    """
    if len(g.nodes) == 0:
        return {}
    
    try:
        order = list(nx.topological_sort(g))
    except Exception:
        # If graph has cycles, fall back to spring layout
        return nx.spring_layout(g, seed=42)
    
    # Calculate longest path from roots for each node (层级)
    longest: Dict[str, int] = {n: 0 for n in order}
    for n in order:
        for succ in g.successors(n):
            longest[succ] = max(longest.get(succ, 0), longest[n] + 1)
    
    # Group nodes by their layer level
    by_rank: Dict[int, List[str]] = {}
    for node, lv in longest.items():
        by_rank.setdefault(lv, []).append(node)
    
    # Sort layers by rank (0 = roots at bottom)
    ranks_sorted = sorted(by_rank.keys())
    
    # Split oversized layers into sub-layers
    # Structure: List of (main_rank, sub_index, nodes)
    sublayers: List[Tuple[int, int, List[str]]] = []
    
    for rank in ranks_sorted:
        nodes = by_rank[rank]
        # Sort nodes for stable layout
        nodes_sorted = sorted(nodes, key=lambda n: (g.out_degree(n), g.in_degree(n), n))
        
        if max_per_layer and max_per_layer > 0 and len(nodes_sorted) > max_per_layer:
            # Split into multiple sub-layers
            num_sublayers = (len(nodes_sorted) + max_per_layer - 1) // max_per_layer
            for sub_idx in range(num_sublayers):
                start = sub_idx * max_per_layer
                end = min(start + max_per_layer, len(nodes_sorted))
                sublayers.append((rank, sub_idx, nodes_sorted[start:end]))
        else:
            # Single sub-layer
            sublayers.append((rank, 0, nodes_sorted))
    
    # Calculate y positions for each sublayer
    # Main layers are at integer y values, sub-layers between them
    total_main_layers = len(ranks_sorted)
    pos: Dict[str, Tuple[float, float]] = {}
    
    # 增加层间距离，避免节点和连接线重叠
    # 使用更大的垂直空间分布
    y_margin = 0.08  # 顶部和底部边距
    y_usable = 1.0 - 2 * y_margin  # 可用的Y轴空间
    
    for sublayer_idx, (rank, sub_idx, nodes) in enumerate(sublayers):
        # Find how many sub-layers belong to this rank
        sublayers_in_rank = sum(1 for r, _, _ in sublayers if r == rank)
        
        # Calculate y position: bottom to top
        # rank determines the main layer (0 at bottom, higher numbers go up)
        # sub_idx distributes within the layer's vertical space
        if total_main_layers == 1:
            base_y = 0.5
        else:
            # Invert y: rank 0 (roots) at y=0 (bottom), higher ranks go up
            # 增加层间距，使用更大的垂直空间
            base_y = y_margin + (rank / (total_main_layers - 1)) * y_usable
        
        # If multiple sub-layers, distribute them vertically within the layer spacing
        if sublayers_in_rank > 1:
            # Space between main layers - 增加子层间距
            layer_spacing = y_usable / max(1, total_main_layers - 1) if total_main_layers > 1 else y_usable
            # Distribute sub-layers within this spacing - 增加到0.9以获得更大间距
            sub_offset = (sub_idx / sublayers_in_rank) * layer_spacing * 0.9
            y = base_y + sub_offset
        else:
            y = base_y
        
        # Calculate x positions for nodes in this sublayer
        # 增加水平间距，避免节点过于拥挤
        count = len(nodes)
        x_margin = 0.05  # 左右边距
        x_usable = 1.0 - 2 * x_margin  # 可用的X轴空间
        
        for i, node in enumerate(nodes):
            if count == 1:
                x = 0.5
            else:
                # Spread horizontally with larger margins
                # 确保节点间有足够间距
                x = x_margin + x_usable * (i / (count - 1))
            pos[node] = (x, y)
    
    # Ensure all nodes have positions
    for n in g.nodes:
        if n not in pos:
            pos[n] = (0.5, 0.5)
    
    return pos


def render_dependency_tree(
    db_path: str,
    out_path: str,
    highlight_cycles: bool = True,
    focus: Optional[str] = None,
    layered: bool = True,
    max_depth: Optional[int] = None,
    truncate_title: Optional[int] = 40,
    color_by_unit: bool = True,
    max_per_layer: Optional[int] = 16,
    exclude_isolated: bool = True,
    straight_edges: bool = True,
    reduce_transitive: bool = True,
) -> str:
    """Render the course dependency DAG as a PNG image.

    Args:
        db_path: path to SQLite DB
        out_path: output image path (.png recommended)
        highlight_cycles: color cycle edges red
        focus: if provided, only render the subgraph reachable from this course (its prerequisites chain)
        layered: use layered layout (vs spring layout) - default True for tree-like hierarchy
        max_depth: limit depth (levels) from roots or focus
        truncate_title: truncate course title to this length
        color_by_unit: color nodes by offering unit
        max_per_layer: wrap wide layers into multiple rows
        exclude_isolated: remove courses with no prerequisites and no dependents - default True
        straight_edges: draw straight edges (no curvature) - default True
        reduce_transitive: remove redundant transitive edges (e.g., A→B→C removes A→C) - default True
        
    Returns:
        Path to written image file.
    """
    courses, edges = load_relations(db_path)
    excl_map = load_exclusions(db_path)
    g = build_graph(courses, edges)
    
    # Remove transitive edges to simplify the graph
    if reduce_transitive:
        g = remove_transitive_edges(g)
    
    # Optionally remove isolated nodes (no incoming and no outgoing edges)
    if exclude_isolated:
        iso = [n for n in list(g.nodes) if g.in_degree(n) == 0 and g.out_degree(n) == 0]
        if iso:
            g.remove_nodes_from(iso)
    
    if focus and focus in g.nodes:
        # Limit to prerequisites ancestors of focus
        if max_depth is None:
            ancestors = nx.ancestors(g, focus)
            sub_nodes = ancestors | {focus}
        else:
            # Traverse reversed graph up to max_depth levels
            gr = g.reverse()
            sub_nodes = {focus}
            frontier = {focus}
            for _ in range(max_depth):
                nxt = set()
                for n in frontier:
                    nxt.update(gr.successors(n))
                sub_nodes |= nxt
                frontier = nxt
        g = g.subgraph(sub_nodes).copy()
    elif max_depth is not None:
        # Global trim by level from roots
        try:
            order = list(nx.topological_sort(g))
            longest: Dict[str, int] = {n: 0 for n in order}
            for n in order:
                for succ in g.successors(n):
                    longest[succ] = max(longest.get(succ, 0), longest[n] + 1)
            keep = {n for n, lv in longest.items() if lv <= max_depth}
            g = g.subgraph(keep).copy()
        except Exception:
            pass
    
    cycles = detect_cycles(g) if highlight_cycles else []
    cycle_edges: Set[Tuple[str, str]] = set()
    for cyc in cycles:
        if len(cyc) >= 2:
            for i in range(len(cyc)):
                a = cyc[i]
                b = cyc[(i + 1) % len(cyc)]
                if g.has_edge(a, b):
                    cycle_edges.add((a, b))
    
    pos = layered_layout(g, max_per_layer=max_per_layer) if layered else layered_layout(g, max_per_layer=None)
    
    # Dynamic figure size based on layers and max layer width
    # Calculate actual number of visual rows (including sub-layers)
    y_values = sorted(set(y for _, y in pos.values()))
    num_visual_rows = len(y_values)
    max_nodes_per_row = max_per_layer if max_per_layer else 16
    
    # 增加图像尺寸，确保节点间有足够空间
    # Width based on max nodes per row - 增加每个节点的水平空间
    width = min(max(12, 2.2 * max_nodes_per_row), 60)
    # Height based on number of rows - 增加每层的垂直空间
    height = min(max(10, 2.8 * num_visual_rows), 60)
    
    plt.figure(figsize=(width, height))
    
    # Node labels: code plus full title with word wrapping
    def wrap_title(title: str, max_words_per_line: int = 3) -> str:
        """将标题按单词数换行"""
        words = title.split()
        if len(words) <= max_words_per_line:
            return title
        
        lines = []
        for i in range(0, len(words), max_words_per_line):
            lines.append(' '.join(words[i:i + max_words_per_line]))
        return '\n'.join(lines)
    
    labels = {}
    for n in g.nodes:
        title_raw = (g.nodes[n].get('title') or '').strip()
        title_wrapped = wrap_title(title_raw, max_words_per_line=3)
        
        # 构建标签内容
        label_parts = [n, title_wrapped]
        
        # 添加互斥课程信息
        excl = excl_map.get(n)
        if excl:
            exlist = sorted(excl)
            if len(exlist) > 5:
                text = ", ".join(exlist[:5]) + f" (+{len(exlist)-5})"
            else:
                text = ", ".join(exlist)
            label_parts.append(f"Excl: {text}")
        
        labels[n] = '\n'.join(label_parts)
    
    # ========== 按父节点（源节点）分组绘制彩色连接线 ==========
    # 普通边：按父节点（前置课程）分组，每个父节点的所有出边使用相同颜色
    normal_edges = [e for e in g.edges if e not in cycle_edges]
    
    # 按源节点（父节点/前置课程）分组边
    edges_by_source: Dict[str, List[Tuple[str, str]]] = {}
    for src, dst in normal_edges:
        if src not in edges_by_source:
            edges_by_source[src] = []
        edges_by_source[src].append((src, dst))
    
    # 为每个父节点分配一个颜色
    # 使用质性色彩映射，确保颜色差异明显
    source_nodes = sorted(edges_by_source.keys())
    num_sources = len(source_nodes)
    
    # 优先使用tab20/tab20b/tab20c组合，提供高对比度的离散颜色
    if num_sources > 0:
        # 定义多组高对比度的颜色池
        distinct_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',  # tab10
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
            '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',  # tab20 浅色
            '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
            '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',  # tab20b
            '#bd9e39', '#ad494a', '#a55194', '#6b6ecf', '#b5cf6b',
        ]
        
        # 循环使用颜色池
        source_colors = {src: distinct_colors[i % len(distinct_colors)] 
                        for i, src in enumerate(source_nodes)}
    else:
        source_colors = {}
    
    # 绘制节点 - 使用连接线颜色（如果该节点是父节点）
    node_colors = []
    for node in g.nodes:
        if node in source_colors:
            # 如果是父节点，使用其连接线颜色
            node_colors.append(source_colors[node])
        else:
            # 如果不是父节点（叶子节点），使用默认灰色
            node_colors.append('#cccccc')
    
    nx.draw_networkx_nodes(g, pos, node_size=650, node_color=node_colors, alpha=0.85, edgecolors='black', linewidths=1)
    
    # 绘制边
    if straight_edges:
        # 使用直线绘制边，按父节点分组着色
        for src, edges_list in edges_by_source.items():
            color = source_colors.get(src, "#2E5090")
            nx.draw_networkx_edges(
                g, pos, edgelist=edges_list,
                edge_color=color, arrows=True, arrowstyle='-|>',
                arrowsize=15, width=1.5, alpha=0.7, node_size=650
            )
        
        # 绘制循环依赖边（红色）
        if cycle_edges:
            nx.draw_networkx_edges(
                g, pos, edgelist=list(cycle_edges),
                edge_color='#D32F2F', arrows=True, arrowstyle='-|>',
                arrowsize=15, width=2.5, alpha=0.8, node_size=650
            )
    else:
        # 使用曲线绘制边
        for src, edges_list in edges_by_source.items():
            color = source_colors.get(src, "#2E5090")
            nx.draw_networkx_edges(
                g, pos, edgelist=edges_list,
                edge_color=color, arrows=True, arrowstyle='-|>',
                arrowsize=15, width=1.5, alpha=0.7, connectionstyle='arc3,rad=0.1', node_size=650
            )
        
        if cycle_edges:
            nx.draw_networkx_edges(
                g, pos, edgelist=list(cycle_edges),
                edge_color='#D32F2F', arrows=True, arrowstyle='-|>',
                arrowsize=15, width=2.5, alpha=0.8, connectionstyle='arc3,rad=0.1', node_size=650
            )
    
    # 绘制标签，居中对齐
    nx.draw_networkx_labels(g, pos, labels=labels, font_size=8, horizontalalignment='center', verticalalignment='center')
    
    title = "Course Dependency Tree (Bottom: Prerequisites → Top: Dependents)"
    if focus:
        title += f" | Focus: {focus}"
    if cycle_edges:
        title += f" | Cycles: {len(cycles)}"
    if max_per_layer:
        title += f" | Max/Layer: {max_per_layer}"
    
    plt.title(title, fontsize=11, pad=20)  # 增加标题间距
    
    # Set y-axis with roots at bottom (y=0)
    ax = plt.gca()
    # 增加上下边距，避免节点被裁切
    ax.set_ylim(-0.08, 1.08)
    ax.set_xlim(-0.03, 1.03)  # 增加左右边距
    ax.invert_yaxis()  # Invert so y=0 is at bottom, y=1 at top
    plt.axis("off")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


__all__ = [
    "render_dependency_tree",
]
