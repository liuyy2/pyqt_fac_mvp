"""
Matplotlib嵌入PyQt5的通用组件
Matplotlib Widget for PyQt5 Integration
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import List, Dict, Optional, Tuple

# 设置中文字体 - 优化配置避免标题显示问题
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'STSong', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 9  # 基础字体大小
matplotlib.rcParams['figure.dpi'] = 100  # 默认DPI
matplotlib.rcParams['figure.titlesize'] = 'medium'  # 标题大小
matplotlib.rcParams['figure.titleweight'] = 'bold'  # 标题粗体


class MatplotlibWidget(QWidget):
    """可嵌入PyQt5的Matplotlib画布组件"""
    
    def __init__(self, parent=None, width: int = 8, height: int = 6, dpi: int = 100):
        super().__init__(parent)
        
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 窗口resize时标记需要重绘
        self._need_redraw = False
    
    def resizeEvent(self, event):
        """窗口大小变化时的处理"""
        super().resizeEvent(event)
        # 标记需要重绘，避免立即重绘导致的性能问题
        self._need_redraw = True
    
    def showEvent(self, event):
        """窗口显示时的处理"""
        super().showEvent(event)
        if self._need_redraw:
            self.canvas.draw()
            self._need_redraw = False
    
    def clear(self):
        """清空图表"""
        self.figure.clear()
        self.canvas.draw()
    
    def draw(self):
        """刷新画布"""
        # 为标题预留足够空间，避免被裁剪
        self.figure.tight_layout(pad=1.5, h_pad=1.0, w_pad=1.0, rect=(0, 0, 1, 0.96))
        self.canvas.draw()
    
    def save_figure(self, filepath: str, dpi: int = 150):
        """保存图表到文件"""
        # 使用pad_inches确保标题不被裁剪
        self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight', pad_inches=0.3)


class RiskMatrixChart(MatplotlibWidget):
    """风险矩阵热力图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=7, height=6)
    
    def plot_matrix(self, matrix_data: List[List[int]], 
                    matrix_events: Dict[str, List[int]] = None,
                    title: str = "风险矩阵热力图"):
        """
        绘制5x5风险矩阵热力图
        
        Args:
            matrix_data: 5x5矩阵，每格为事件数量
            matrix_events: 每格对应的事件ID列表
            title: 图表标题
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 创建风险等级颜色矩阵 (L x S)
        risk_colors = np.zeros((5, 5, 3))
        color_map = {
            'low': [0.960, 0.960, 0.960],      # 极浅灰 #f5f5f5
            'medium': [0.910, 0.910, 0.910],   # 浅灰 #e8e8e8
            'high': [0.847, 0.847, 0.847],     # 中灰 #d8d8d8
            'extreme': [0.784, 0.784, 0.784]   # 深灰 #c8c8c8
        }
        
        # 填充颜色矩阵
        for i in range(5):  # L: 1-5
            for j in range(5):  # S: 1-5
                r = (i + 1) * (j + 1)
                if r <= 4:
                    risk_colors[i, j] = color_map['low']
                elif r <= 9:
                    risk_colors[i, j] = color_map['medium']
                elif r <= 16:
                    risk_colors[i, j] = color_map['high']
                else:
                    risk_colors[i, j] = color_map['extreme']
        
        # 绘制热力图背景
        ax.imshow(risk_colors, aspect='equal', origin='lower')
        
        # 在每格中显示事件数量和R值
        for i in range(5):
            for j in range(5):
                count = matrix_data[i][j]
                r = (i + 1) * (j + 1)
                
                # 显示风险分数
                ax.text(j, i, f"R={r}", ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='black')
                
                # 显示事件数量
                if count > 0:
                    ax.text(j, i, f"({count})", ha='center', va='top',
                           fontsize=9, color='#333')
        
        # 设置坐标轴
        ax.set_xticks(range(5))
        ax.set_yticks(range(5))
        ax.set_xticklabels(['1-很低', '2-低', '3-中', '4-高', '5-很高'])
        ax.set_yticklabels(['1-罕见', '2-偶发', '3-可能', '4-频繁', '5-几乎必然'])
        ax.set_xlabel('严重度 (Severity)', fontsize=11)
        ax.set_ylabel('可能性 (Likelihood)', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # 添加网格线
        ax.set_xticks(np.arange(-0.5, 5, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=2)
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=color_map['low'], label='Low (1-4)'),
            Patch(facecolor=color_map['medium'], label='Medium (5-9)'),
            Patch(facecolor=color_map['high'], label='High (10-16)'),
            Patch(facecolor=color_map['extreme'], label='Extreme (17-25)')
        ]
        ax.legend(handles=legend_elements, loc='upper left', 
                 bbox_to_anchor=(1.02, 1), fontsize=9)
        
        self.draw()


class TopNBarChart(MatplotlibWidget):
    """Top-N条形图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=8, height=5)
    
    def plot_top_risks(self, names: List[str], values: List[float], 
                       levels: List[str] = None,
                       title: str = "Top风险排序",
                       xlabel: str = "风险分数",
                       ylabel: str = "风险事件"):
        """
        绘制Top-N风险条形图
        
        Args:
            names: 名称列表
            values: 分数列表
            levels: 等级列表（用于着色）
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 颜色映射
        level_colors = {
            'Low': '#d0d0d0',
            'Medium': '#a8a8a8',
            'High': '#808080',
            'Extreme': '#606060'
        }
        
        if levels:
            colors = [level_colors.get(l, '#9E9E9E') for l in levels]
        else:
            colors = ['#888888'] * len(names)
        
        # 反转顺序使最高的在上面
        y_pos = range(len(names))
        
        bars = ax.barh(y_pos, values, color=colors, edgecolor='black', linewidth=0.5)
        
        # 设置标签
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=9)
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        
        # 在条形上显示数值
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{val:.0f}', va='center', fontsize=9)
        
        ax.invert_yaxis()  # 最高分在顶部
        ax.set_xlim(0, max(values) * 1.15 if values else 10)
        
        self.draw()


class SensitivityBarChart(MatplotlibWidget):
    """敏感性分析条形图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=9, height=5)
    
    def plot_sensitivity(self, factor_names: List[str], 
                         impact_scores: List[float],
                         title: str = "敏感性分析 - Top影响因素"):
        """
        绘制敏感性分析条形图
        
        Args:
            factor_names: 因素名称列表
            impact_scores: 影响分数列表
            title: 图表标题
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        y_pos = range(len(factor_names))
        
        # 使用灰色渐变
        cmap = plt.cm.Greys
        norm_scores = [s / max(impact_scores) if impact_scores else 0 for s in impact_scores]
        colors = [cmap(0.4 + 0.5 * ns) for ns in norm_scores]
        
        bars = ax.barh(y_pos, impact_scores, color=colors, edgecolor='#333', linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(factor_names, fontsize=9)
        ax.set_xlabel('影响分数 (Impact Score)', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # 显示数值
        for bar, val in zip(bars, impact_scores):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}', va='center', fontsize=9)
        
        ax.invert_yaxis()
        ax.set_xlim(0, max(impact_scores) * 1.15 if impact_scores else 10)
        
        self.draw()


class HistogramChart(MatplotlibWidget):
    """直方图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=7, height=5)
    
    def plot_histogram(self, data: List[float], 
                       title: str = "分布直方图",
                       xlabel: str = "值",
                       ylabel: str = "频次",
                       bins: int = 30,
                       show_stats: bool = True):
        """
        绘制直方图
        
        Args:
            data: 数据列表
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            bins: 柱子数量
            show_stats: 是否显示统计信息
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not data:
            ax.text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=14)
            self.draw()
            return
        
        data_array = np.array(data)
        
        # 绘制直方图
        n, bins_edges, patches = ax.hist(data_array, bins=bins, 
                                          color='#888888', edgecolor='black',
                                          alpha=0.7)
        
        # 添加均值线
        mean_val = np.mean(data_array)
        ax.axvline(mean_val, color='#555', linestyle='--', linewidth=2, label=f'均值: {mean_val:.1f}')
        
        # 添加P90线
        p90_val = np.percentile(data_array, 90)
        ax.axvline(p90_val, color='#333', linestyle='--', linewidth=2, label=f'P90: {p90_val:.1f}')
        
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.legend(loc='upper right')
        
        # 显示统计信息
        if show_stats:
            stats_text = f"n={len(data_array)}\n"
            stats_text += f"μ={mean_val:.2f}\n"
            stats_text += f"σ={np.std(data_array):.2f}\n"
            stats_text += f"P50={np.percentile(data_array, 50):.2f}"
            ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   fontsize=9)
        
        self.draw()


class FTATreeChart(MatplotlibWidget):
    """FTA故障树可视化图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=8)
    
    def plot_fta_tree(self, nodes: List[Dict], edges: List[Tuple[int, int]],
                      title: str = "故障树结构图"):
        """
        绘制故障树结构图
        
        Args:
            nodes: 节点列表 [{"id", "name", "node_type", "gate_type", "probability"}]
            edges: 边列表 [(parent_id, child_id), ...]
            title: 图表标题
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not nodes:
            ax.text(0.5, 0.5, '无故障树数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        try:
            import networkx as nx
            
            # 构建图
            G = nx.DiGraph()
            node_dict = {n["id"]: n for n in nodes}
            
            for n in nodes:
                G.add_node(n["id"], **n)
            
            for parent_id, child_id in edges:
                if parent_id in node_dict and child_id in node_dict:
                    G.add_edge(parent_id, child_id)
            
            # 查找顶事件（入度为0）
            top_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            
            if top_nodes:
                # 使用层次布局
                try:
                    pos = self._hierarchy_pos(G, top_nodes[0])
                except Exception:
                    pos = nx.spring_layout(G, k=2, iterations=50)
            else:
                pos = nx.spring_layout(G, k=2, iterations=50)
            
            # 节点颜色和形状（增强对比度）
            node_colors = []
            node_sizes = []
            labels = {}
            
            for n in G.nodes():
                node_data = node_dict.get(n, {})
                node_type = node_data.get("node_type", "BASIC")
                gate_type = node_data.get("gate_type", "")
                name = node_data.get("name", str(n))[:15]  # 限制名称长度
                prob = node_data.get("probability", 0)
                
                if node_type == "TOP":
                    node_colors.append('#2c2c2c')  # 深黑灰色
                    node_sizes.append(2000)
                    labels[n] = f"{name}\nP={prob:.2e}"
                elif node_type == "INTERMEDIATE":
                    if gate_type == "AND":
                        node_colors.append('#4a4a4a')  # 深灰色
                    else:  # OR
                        node_colors.append('#6e6e6e')  # 中灰色
                    node_sizes.append(1500)
                    labels[n] = f"{name}\n[{gate_type}]\nP={prob:.2e}"
                else:  # BASIC
                    node_colors.append('#e0e0e0')  # 浅灰色（更亮）
                    node_sizes.append(1200)
                    labels[n] = f"{name}\nP={prob:.2e}"
            
            # 绘制边
            nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, 
                                   arrowsize=15, edge_color='#555',
                                   connectionstyle="arc3,rad=0.1", width=1.5)
            
            # 绘制节点
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                                   node_size=node_sizes, edgecolors='black', linewidths=2)
            
            # 绘制标签（增大字体，调整颜色以确保可读性）
            for node, (x, y) in pos.items():
                label_text = labels[node]
                # 根据节点颜色选择文字颜色
                node_color = node_colors[list(G.nodes()).index(node)]
                # 深色节点用白色文字，浅色节点用黑色文字
                if node_color in ['#2c2c2c', '#4a4a4a', '#6e6e6e']:
                    text_color = 'white'
                else:
                    text_color = 'black'
                ax.text(x, y, label_text, ha='center', va='center',
                       fontsize=7, fontweight='bold', color=text_color,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=node_color, 
                                edgecolor='black', linewidth=1.5, alpha=0.9))
            
            ax.set_title(title, fontsize=11, fontweight='bold', pad=12)
            ax.axis('off')
            
            # 设置图表边距，避免被截断
            ax.set_xlim(-0.15, 1.15)
            ax.set_ylim(-0.55, 0.12)
            
            # 添加图例（更新颜色）
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#2c2c2c', edgecolor='black', label='顶事件 (TOP)'),
                Patch(facecolor='#4a4a4a', edgecolor='black', label='中间事件 (AND门)'),
                Patch(facecolor='#6e6e6e', edgecolor='black', label='中间事件 (OR门)'),
                Patch(facecolor='#e0e0e0', edgecolor='black', label='基本事件 (BASIC)')
            ]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=7,
                     frameon=True, fancybox=True, shadow=True)
            
            # 调整布局，确保标题完整显示（增加top空间）
            self.figure.subplots_adjust(top=0.92, bottom=0.02, left=0.02, right=0.98)
            
        except Exception as e:
            # 如果出错，显示错误信息
            self._plot_simple_tree(ax, nodes, edges, title, str(e))
        
        self.draw()
    
    def _hierarchy_pos(self, G, root, width=1., vert_gap=0.15, vert_loc=0, xcenter=0.5):
        """计算层次布局位置"""
        import networkx as nx
        
        def _hierarchy_pos_recursive(G, root, width, vert_gap, vert_loc, xcenter, pos, parent=None, parsed=[]):
            parsed.append(root)
            children = list(G.successors(root))
            if children:
                dx = width / len(children)
                nextx = xcenter - width/2 - dx/2
                for child in children:
                    nextx += dx
                    pos = _hierarchy_pos_recursive(G, child, width=dx, vert_gap=vert_gap,
                                                    vert_loc=vert_loc-vert_gap, xcenter=nextx,
                                                    pos=pos, parent=root, parsed=parsed)
            pos[root] = (xcenter, vert_loc)
            return pos
        
        return _hierarchy_pos_recursive(G, root, width, vert_gap, vert_loc, xcenter, {}, parsed=[])
    
    def _plot_simple_tree(self, ax, nodes, edges, title, error_msg=""):
        """简化树形图（出错时使用）"""
        msg = f'故障树包含 {len(nodes)} 个节点'
        if error_msg:
            msg += f'\n错误: {error_msg[:50]}'
        ax.text(0.5, 0.5, msg,
               ha='center', va='center', fontsize=11,
               bbox=dict(boxstyle='round', facecolor='#f0f0f0'))
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axis('off')


class FTAContributionChart(MatplotlibWidget):
    """FTA贡献度分析图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=8, height=6)
    
    def plot_contribution(self, names: List[str], contributions: List[float],
                          probabilities: List[float] = None,
                          title: str = "基本事件贡献度分析"):
        """
        绘制贡献度横向条形图和饼图组合
        
        Args:
            names: 事件名称列表
            contributions: 贡献度列表
            probabilities: 概率列表（用于显示）
            title: 图表标题
        """
        self.figure.clear()
        
        if not names:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '无贡献度数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        # 两列布局：左边条形图，右边饼图（调整比例）
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        
        # 条形图
        y_pos = range(len(names))
        
        # 使用灰色渐变
        max_contrib = max(contributions) if contributions else 1
        colors = [plt.cm.Greys(0.3 + 0.5 * (c / max_contrib)) for c in contributions]
        
        bars = ax1.barh(y_pos, contributions, color=colors, edgecolor='#333', linewidth=0.5)
        
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels([n[:12] for n in names], fontsize=8)  # 限制名称长度
        ax1.set_xlabel('贡献度', fontsize=9)
        ax1.set_title('贡献度排名', fontsize=10, fontweight='bold', pad=10)
        
        # 显示数值和概率
        for i, (bar, val) in enumerate(zip(bars, contributions)):
            label = f'{val:.1%}'
            if probabilities and i < len(probabilities):
                label += f' (P={probabilities[i]:.0e})'
            ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    label, va='center', fontsize=7)
        
        ax1.invert_yaxis()
        ax1.set_xlim(0, max_contrib * 1.4 if contributions else 1)
        
        # 饼图（显示前5个）
        top_n = min(5, len(names))
        pie_names = list(names[:top_n])
        pie_contribs = list(contributions[:top_n])
        
        # 添加"其他"类别
        if len(names) > 5:
            others_contrib = sum(contributions[5:])
            pie_names.append('其他')
            pie_contribs.append(others_contrib)
        
        pie_colors = [plt.cm.Greys(0.3 + i * 0.1) for i in range(len(pie_names))]
        
        wedges, texts, autotexts = ax2.pie(pie_contribs, labels=None, autopct='%1.1f%%',
                                            colors=pie_colors, startangle=90,
                                            wedgeprops=dict(edgecolor='white', linewidth=1.5),
                                            pctdistance=0.75)
        # 调整百分比文字大小
        for autotext in autotexts:
            autotext.set_fontsize(8)
        
        ax2.legend(wedges, [n[:10] for n in pie_names], 
                   title="基本事件", loc="upper right",
                   bbox_to_anchor=(1.35, 1.0), fontsize=7, title_fontsize=8)
        ax2.set_title('贡献度分布', fontsize=10, fontweight='bold', pad=10)
        
        # 调整整体布局，确保标题和标签完整显示
        self.figure.subplots_adjust(top=0.90, bottom=0.08, left=0.18, right=0.82, wspace=0.35)
        self.draw()


class FTASensitivityChart(MatplotlibWidget):
    """FTA敏感性分析专用图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=9, height=6)
    
    def plot_tornado(self, names: List[str], 
                     base_probs: List[float],
                     minus_changes: List[float],
                     plus_changes: List[float],
                     base_top_prob: float,
                     title: str = "FTA敏感性分析"):
        """
        绘制龙卷风图展示敏感性分析结果
        
        Args:
            names: 基本事件名称
            base_probs: 基准概率
            minus_changes: 概率降低后的顶事件概率变化
            plus_changes: 概率增加后的顶事件概率变化
            base_top_prob: 基准顶事件概率
            title: 图表标题
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not names:
            ax.text(0.5, 0.5, '无敏感性分析数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        y_pos = range(len(names))
        
        # 计算变化量（相对于基准）
        minus_delta = [(m - base_top_prob) for m in minus_changes]
        plus_delta = [(p - base_top_prob) for p in plus_changes]
        
        # 绘制双向条形图
        bars1 = ax.barh(y_pos, minus_delta, height=0.4, color='#888888', 
                        edgecolor='#333', label='概率降低10%', align='center')
        bars2 = ax.barh([y + 0.4 for y in y_pos], plus_delta, height=0.4, 
                        color='#555555', edgecolor='#333', label='概率增加10%', align='center')
        
        # 绘制基准线
        ax.axvline(0, color='black', linewidth=1.5, linestyle='-')
        
        ax.set_yticks([y + 0.2 for y in y_pos])
        ax.set_yticklabels([f"{n[:12]}" for n in names], fontsize=8)
        ax.set_xlabel(f'顶事件概率变化 (基准: {base_top_prob:.2e})', fontsize=9)
        ax.set_title(title, fontsize=10, fontweight='bold', pad=12)
        ax.legend(loc='lower right', fontsize=7)
        ax.invert_yaxis()
        
        # 添加网格
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        
        # 调整布局，确保标题和标签完整显示
        self.figure.subplots_adjust(top=0.90, bottom=0.15, left=0.18, right=0.95)
        
        self.draw()


class AHPRadarChart(MatplotlibWidget):
    """AHP雷达图（蛛网图）组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=7, height=6)
    
    def plot_radar(self, indicator_names: List[str], 
                   weights: List[float],
                   scores: List[float],
                   title: str = "AHP指标权重与得分雷达图"):
        """
        绘制雷达图展示各指标权重和得分
        
        Args:
            indicator_names: 指标名称列表
            weights: 权重列表
            scores: 得分列表 (0~1)
            title: 图表标题
        """
        self.figure.clear()
        
        if not indicator_names:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '无AHP数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        # 限制显示的指标数量
        max_indicators = 12
        if len(indicator_names) > max_indicators:
            indicator_names = indicator_names[:max_indicators]
            weights = weights[:max_indicators]
            scores = scores[:max_indicators]
        
        # 计算角度
        num_vars = len(indicator_names)
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        angles += angles[:1]  # 闭合
        
        # 准备数据（闭合）
        weights_plot = list(weights) + [weights[0]]
        scores_plot = list(scores) + [scores[0]]
        
        ax = self.figure.add_subplot(111, polar=True)
        
        # 绘制权重
        ax.plot(angles, weights_plot, 'o-', linewidth=2, color='#666666', label='修正权重')
        ax.fill(angles, weights_plot, alpha=0.25, color='#888888')
        
        # 绘制得分
        ax.plot(angles, scores_plot, 's--', linewidth=2, color='#333333', label='归一化得分')
        ax.fill(angles, scores_plot, alpha=0.15, color='#444444')
        
        # 设置角度标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([n[:10] for n in indicator_names], fontsize=8)
        
        # 设置径向范围
        ax.set_ylim(0, max(max(weights_plot), max(scores_plot)) * 1.1)
        
        ax.set_title(title, fontsize=10, fontweight='bold', pad=15)
        # 将图例移到右上角外侧，避免与雷达图重叠
        ax.legend(loc='upper left', bbox_to_anchor=(1.12, 1.05), fontsize=8,
                 frameon=True, fancybox=True, shadow=True)
        
        # 调整布局，确保标题和图例完整显示
        self.figure.subplots_adjust(top=0.86, bottom=0.05, left=0.1, right=0.78)
        self.draw()


class AHPContributionChart(MatplotlibWidget):
    """AHP贡献度瀑布图/条形图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=6)
    
    def plot_waterfall(self, indicator_names: List[str],
                       contributions: List[float],
                       total_score: float,
                       title: str = "AHP指标贡献度瀑布图"):
        """
        绘制瀑布图展示各指标对总分的贡献
        
        Args:
            indicator_names: 指标名称列表
            contributions: 各指标贡献（加权得分）
            total_score: 总分
            title: 图表标题
        """
        self.figure.clear()
        
        if not indicator_names:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '无AHP贡献度数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        ax = self.figure.add_subplot(111)
        
        # 排序并取前10个
        sorted_data = sorted(zip(indicator_names, contributions), key=lambda x: x[1], reverse=True)
        if len(sorted_data) > 10:
            sorted_data = sorted_data[:10]
        
        names = [d[0][:15] for d in sorted_data]
        values = [d[1] for d in sorted_data]
        
        # 计算累积值（用于瀑布效果）
        cumulative = [0]
        for v in values[:-1]:
            cumulative.append(cumulative[-1] + v)
        
        # 绘制瀑布图
        x_pos = range(len(names))
        
        # 使用灰色渐变
        max_val = max(values) if values else 1
        colors = [plt.cm.Greys(0.4 + 0.4 * (v / max_val)) for v in values]
        
        bars = ax.bar(x_pos, values, bottom=cumulative, color=colors, 
                      edgecolor='#333', linewidth=1)
        
        # 添加连接线
        for i in range(len(names) - 1):
            ax.hlines(cumulative[i+1] + values[i], i + 0.4, i + 0.6, 
                     colors='gray', linestyles='dashed', linewidth=1)
        
        # 设置标签
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('贡献度累积', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        
        # 在条形上显示数值
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + height/2,
                   f'{val:.3f}', ha='center', va='center', fontsize=8, 
                   fontweight='bold', color='white' if val > max_val * 0.5 else 'black')
        
        # 添加总分线
        ax.axhline(y=total_score, color='#333', linestyle='--', linewidth=2,
                   label=f'总分: {total_score:.4f}')
        ax.legend(loc='upper right', fontsize=10)
        
        # 设置Y轴范围
        ax.set_ylim(0, max(total_score * 1.1, sum(values) * 1.1))
        
        self.figure.tight_layout()
        self.draw()
    
    def plot_horizontal_bar(self, indicator_names: List[str],
                            weights: List[float],
                            scores: List[float],
                            contributions: List[float],
                            title: str = "AHP指标权重-得分-贡献度对比"):
        """
        绘制水平分组条形图对比权重、得分、贡献度
        
        Args:
            indicator_names: 指标名称
            weights: 权重列表
            scores: 得分列表
            contributions: 贡献度列表
            title: 图表标题
        """
        self.figure.clear()
        
        if not indicator_names:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '无AHP数据', ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        ax = self.figure.add_subplot(111)
        
        # 限制显示数量
        max_items = 12
        if len(indicator_names) > max_items:
            # 按贡献度排序取前N个
            sorted_indices = sorted(range(len(contributions)), 
                                   key=lambda i: contributions[i], reverse=True)[:max_items]
            indicator_names = [indicator_names[i] for i in sorted_indices]
            weights = [weights[i] for i in sorted_indices]
            scores = [scores[i] for i in sorted_indices]
            contributions = [contributions[i] for i in sorted_indices]
        
        y_pos = np.arange(len(indicator_names))
        bar_height = 0.25
        
        # 三组条形
        bars1 = ax.barh(y_pos - bar_height, weights, bar_height, 
                        label='修正权重', color='#888888', edgecolor='#333')
        bars2 = ax.barh(y_pos, scores, bar_height, 
                        label='归一化得分', color='#666666', edgecolor='#333')
        bars3 = ax.barh(y_pos + bar_height, contributions, bar_height, 
                        label='贡献度', color='#444444', edgecolor='#333')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(indicator_names, fontsize=8)  # 显示完整名称
        ax.set_xlabel('数值', fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold', pad=12)
        ax.legend(loc='lower right', fontsize=8)
        ax.invert_yaxis()
        
        # 添加网格
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        
        # 调整布局，确保Y轴标签完整显示
        self.figure.subplots_adjust(left=0.25, right=0.95, top=0.90, bottom=0.1)
        self.draw()
