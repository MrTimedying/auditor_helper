"""
Enhanced Chart Styling System

This module provides comprehensive styling capabilities for charts including
themes, responsive design, accessibility features, and professional formatting.
"""

from typing import Dict, List, Tuple, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import rcParams
import numpy as np

class ChartTheme:
    """Represents a complete chart theme with colors, fonts, and styling options"""
    
    def __init__(self, name: str, colors: Dict[str, str], typography: Dict[str, Any], 
                 layout: Dict[str, Any], accessibility: Dict[str, Any] = None):
        self.name = name
        self.colors = colors
        self.typography = typography
        self.layout = layout
        self.accessibility = accessibility or {}

class ChartStyleManager:
    """Advanced chart styling system with themes, responsive design, and accessibility"""
    
    def __init__(self):
        self.current_theme = "professional"
        self.custom_themes = {}
        self._initialize_built_in_themes()
        
        # Base styling configuration
        self.base_config = {
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'savefig.facecolor': 'white',
            'savefig.edgecolor': 'none',
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 11,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 10,
            'figure.titlesize': 16
        }
    
    def _initialize_built_in_themes(self):
        """Initialize built-in chart themes"""
        
        # Professional Business Theme
        self.built_in_themes = {
            "professional": ChartTheme(
                name="Professional",
                colors={
                    "primary": "#2E3440",
                    "secondary": "#5E81AC", 
                    "accent": "#88C0D0",
                    "success": "#A3BE8C",
                    "warning": "#EBCB8B",
                    "error": "#BF616A",
                    "background": "#FFFFFF",
                    "surface": "#F8F9FA",
                    "text": "#2E3440",
                    "text_light": "#4C566A",
                    "grid": "#E5E7EB",
                    "palette": ["#5E81AC", "#88C0D0", "#81A1C1", "#A3BE8C", "#EBCB8B", "#D08770", "#BF616A", "#B48EAD"]
                },
                typography={
                    "font_family": "Source Sans Pro",
                    "title_size": 16,
                    "label_size": 11,
                    "tick_size": 9,
                    "legend_size": 10,
                    "title_weight": "bold",
                    "label_weight": "normal"
                },
                layout={
                    "margins": {"left": 0.1, "right": 0.95, "top": 0.9, "bottom": 0.1},
                    "grid_alpha": 0.15,  # More subtle grid
                    "spine_width": 0.8,
                    "tick_length": 4,
                    "legend_frameon": True,
                    "legend_shadow": False
                },
                accessibility={
                    "high_contrast": False,
                    "colorblind_safe": True,
                    "pattern_fills": False
                }
            ),
            
            # Modern Dark Theme
            "dark": ChartTheme(
                name="Dark Mode",
                colors={
                    "primary": "#FFFFFF",
                    "secondary": "#64FFDA", 
                    "accent": "#00BCD4",
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "background": "#121212",
                    "surface": "#1E1E1E",
                    "text": "#FFFFFF",
                    "text_light": "#B0B0B0",
                    "grid": "#404040",
                    "palette": ["#64FFDA", "#00BCD4", "#2196F3", "#9C27B0", "#E91E63", "#F44336", "#FF9800", "#4CAF50"]
                },
                typography={
                    "font_family": "Inter",
                    "title_size": 16,
                    "label_size": 11,
                    "tick_size": 9,
                    "legend_size": 10,
                    "title_weight": "600",
                    "label_weight": "400"
                },
                layout={
                    "margins": {"left": 0.1, "right": 0.95, "top": 0.9, "bottom": 0.1},
                    "grid_alpha": 0.1,  # Very subtle grid for dark theme
                    "spine_width": 0.5,
                    "tick_length": 3,
                    "legend_frameon": False,
                    "legend_shadow": False
                },
                accessibility={
                    "high_contrast": True,
                    "colorblind_safe": True,
                    "pattern_fills": False
                }
            ),
            
            # Minimal Clean Theme
            "minimal": ChartTheme(
                name="Minimal",
                colors={
                    "primary": "#1A1A1A",
                    "secondary": "#007AFF", 
                    "accent": "#5AC8FA",
                    "success": "#34C759",
                    "warning": "#FF9500",
                    "error": "#FF3B30",
                    "background": "#FFFFFF",
                    "surface": "#FFFFFF",
                    "text": "#1A1A1A",
                    "text_light": "#8E8E93",
                    "grid": "#F2F2F7",
                    "palette": ["#007AFF", "#5AC8FA", "#34C759", "#FF9500", "#FF3B30", "#AF52DE", "#FF2D92", "#5856D6"]
                },
                typography={
                    "font_family": "SF Pro Display",
                    "title_size": 15,
                    "label_size": 10,
                    "tick_size": 8,
                    "legend_size": 9,
                    "title_weight": "500",
                    "label_weight": "400"
                },
                layout={
                    "margins": {"left": 0.08, "right": 0.97, "top": 0.92, "bottom": 0.08},
                    "grid_alpha": 0.08,  # Extremely subtle grid for minimal theme
                    "spine_width": 0,
                    "tick_length": 0,
                    "legend_frameon": False,
                    "legend_shadow": False
                },
                accessibility={
                    "high_contrast": False,
                    "colorblind_safe": True,
                    "pattern_fills": False
                }
            ),
            
            # High Contrast Accessibility Theme
            "accessible": ChartTheme(
                name="High Contrast",
                colors={
                    "primary": "#000000",
                    "secondary": "#0000FF", 
                    "accent": "#008000",
                    "success": "#008000",
                    "warning": "#FF8C00",
                    "error": "#FF0000",
                    "background": "#FFFFFF",
                    "surface": "#FFFFFF",
                    "text": "#000000",
                    "text_light": "#333333",
                    "grid": "#999999",
                    "palette": ["#000000", "#0000FF", "#008000", "#FF0000", "#FF8C00", "#800080", "#008080", "#800000"]
                },
                typography={
                    "font_family": "Arial",
                    "title_size": 18,
                    "label_size": 12,
                    "tick_size": 10,
                    "legend_size": 11,
                    "title_weight": "bold",
                    "label_weight": "bold"
                },
                layout={
                    "margins": {"left": 0.12, "right": 0.93, "top": 0.88, "bottom": 0.12},
                    "grid_alpha": 0.8,
                    "spine_width": 2,
                    "tick_length": 6,
                    "legend_frameon": True,
                    "legend_shadow": False
                },
                accessibility={
                    "high_contrast": True,
                    "colorblind_safe": True,
                    "pattern_fills": True
                }
            )
        }
    
    def set_theme(self, theme_name: str):
        """Set the active chart theme"""
        if theme_name in self.built_in_themes or theme_name in self.custom_themes:
            self.current_theme = theme_name
            self._apply_theme_to_matplotlib()
        else:
            raise ValueError(f"Theme '{theme_name}' not found")
    
    def get_theme(self, theme_name: str = None) -> ChartTheme:
        """Get a specific theme or the current theme"""
        if theme_name is None:
            theme_name = self.current_theme
        
        if theme_name in self.built_in_themes:
            return self.built_in_themes[theme_name]
        elif theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        else:
            return self.built_in_themes["professional"]
    
    def _apply_theme_to_matplotlib(self):
        """Apply the current theme to matplotlib's global settings"""
        theme = self.get_theme()
        
        # Update rcParams with theme values
        config = self.base_config.copy()
        
        # Colors
        config['figure.facecolor'] = theme.colors['background']
        config['axes.facecolor'] = theme.colors['background']
        config['savefig.facecolor'] = theme.colors['background']
        config['text.color'] = theme.colors['text']
        config['axes.labelcolor'] = theme.colors['text']
        config['xtick.color'] = theme.colors['text']
        config['ytick.color'] = theme.colors['text']
        config['axes.edgecolor'] = theme.colors['text_light']
        
        # Typography
        config['font.size'] = theme.typography['label_size']
        config['axes.titlesize'] = theme.typography['title_size']
        config['axes.labelsize'] = theme.typography['label_size']
        config['xtick.labelsize'] = theme.typography['tick_size']
        config['ytick.labelsize'] = theme.typography['tick_size']
        config['legend.fontsize'] = theme.typography['legend_size']
        config['figure.titlesize'] = theme.typography['title_size']
        
        # Layout
        config['axes.linewidth'] = theme.layout['spine_width']
        config['xtick.major.size'] = theme.layout['tick_length']
        config['ytick.major.size'] = theme.layout['tick_length']
        config['legend.frameon'] = theme.layout['legend_frameon']
        
        # Apply to matplotlib
        rcParams.update(config)
    
    def apply_chart_styling(self, fig, ax, chart_type: str, title: str = "", 
                          x_label: str = "", y_label: str = "", 
                          responsive: bool = True) -> None:
        """Apply comprehensive styling to a chart"""
        theme = self.get_theme()
        
        # Apply theme-based styling
        self._style_figure(fig, theme, responsive)
        self._style_axes(ax, theme, chart_type)
        self._style_labels(ax, theme, title, x_label, y_label)
        self._style_grid(ax, theme)
        self._style_spines(ax, theme)
        
        # Apply accessibility features if needed
        if theme.accessibility.get('high_contrast', False):
            self._apply_high_contrast(ax, theme)
        
        if theme.accessibility.get('pattern_fills', False):
            self._apply_pattern_fills(ax, chart_type)
    
    def _style_figure(self, fig, theme: ChartTheme, responsive: bool):
        """Style the figure container"""
        fig.patch.set_facecolor(theme.colors['background'])
        
        # Set margins
        margins = theme.layout['margins']
        fig.subplots_adjust(
            left=margins['left'],
            right=margins['right'], 
            top=margins['top'],
            bottom=margins['bottom']
        )
        
        # Responsive sizing
        if responsive:
            fig.set_size_inches(10, 6)  # Professional aspect ratio
    
    def _style_axes(self, ax, theme: ChartTheme, chart_type: str):
        """Style the axes based on chart type"""
        ax.set_facecolor(theme.colors['background'])
        
        # Chart-type specific styling
        if chart_type == "Line Chart":
            # Emphasize data lines
            ax.tick_params(axis='both', which='major', 
                          labelsize=theme.typography['tick_size'],
                          length=theme.layout['tick_length'])
        
        elif chart_type == "Bar Chart":
            # Clean bar chart styling
            ax.tick_params(axis='x', rotation=45 if chart_type == "Bar Chart" else 0)
        
        elif chart_type == "Scatter Plot":
            # Minimal scatter plot styling
            ax.tick_params(axis='both', which='major',
                          labelsize=theme.typography['tick_size'])
        
        elif chart_type == "Pie Chart":
            # Clean pie chart (no axes needed)
            ax.set_aspect('equal')
    
    def _style_labels(self, ax, theme: ChartTheme, title: str, x_label: str, y_label: str):
        """Style chart labels and title"""
        if title:
            ax.set_title(title, 
                        fontsize=theme.typography['title_size'],
                        fontweight=theme.typography['title_weight'],
                        color=theme.colors['text'],
                        pad=20)
        
        if x_label:
            ax.set_xlabel(x_label,
                         fontsize=theme.typography['label_size'],
                         fontweight=theme.typography['label_weight'],
                         color=theme.colors['text'])
        
        if y_label:
            ax.set_ylabel(y_label,
                         fontsize=theme.typography['label_size'],
                         fontweight=theme.typography['label_weight'],
                         color=theme.colors['text'])
    
    def _style_grid(self, ax, theme: ChartTheme):
        """Style chart grid with dotted, subtle lines"""
        ax.grid(True, 
               color=theme.colors['grid'],
               alpha=theme.layout['grid_alpha'],
               linewidth=0.5,
               linestyle=':')  # Dotted lines instead of solid
        ax.set_axisbelow(True)  # Grid behind data
    
    def _style_spines(self, ax, theme: ChartTheme):
        """Style chart spines (borders)"""
        spine_width = theme.layout['spine_width']
        spine_color = theme.colors['text_light']
        
        if spine_width == 0:
            # Hide all spines for minimal theme
            for spine in ax.spines.values():
                spine.set_visible(False)
        else:
            # Style visible spines
            for spine in ax.spines.values():
                spine.set_linewidth(spine_width)
                spine.set_color(spine_color)
    
    def _apply_high_contrast(self, ax, theme: ChartTheme):
        """Apply high contrast accessibility features"""
        # Increase line widths
        for line in ax.get_lines():
            line.set_linewidth(max(line.get_linewidth(), 2.5))
        
        # Increase marker sizes
        for line in ax.get_lines():
            if line.get_marker() != 'None':
                line.set_markersize(max(line.get_markersize(), 8))
    
    def _apply_pattern_fills(self, ax, chart_type: str):
        """Apply pattern fills for colorblind accessibility"""
        patterns = ['///', '...', '+++', 'xxx', '|||', '---', '\\\\\\']
        
        if chart_type == "Bar Chart":
            # Apply patterns to bars
            bars = ax.patches
            for i, bar in enumerate(bars):
                pattern = patterns[i % len(patterns)]
                bar.set_hatch(pattern)
                bar.set_edgecolor('black')
                bar.set_linewidth(1)
    
    def get_theme_colors(self, theme_name: str = None) -> List[str]:
        """Get the color palette for a theme"""
        theme = self.get_theme(theme_name)
        return theme.colors['palette']
    
    def get_semantic_color(self, variable_name: str, theme_name: str = None) -> str:
        """Get semantic color for a variable, falling back to theme palette"""
        theme = self.get_theme(theme_name)
        
        # Semantic color mappings (from existing SemanticColorManager)
        semantic_mappings = {
            'fail_rate': theme.colors.get('error', '#E74C3C'),
            'error_rate': theme.colors.get('error', '#E74C3C'),
            'total_earnings': theme.colors.get('success', '#27AE60'),
            'revenue': theme.colors.get('success', '#27AE60'),
            'duration': theme.colors.get('secondary', '#3498DB'),
            'total_time': theme.colors.get('secondary', '#3498DB'),
            'performance_score': theme.colors.get('warning', '#F39C12'),
            'count': theme.colors.get('accent', '#9B59B6'),
            'percentage': theme.colors.get('warning', '#E67E22')
        }
        
        # Check for semantic matches
        var_lower = variable_name.lower()
        for key, color in semantic_mappings.items():
            if key in var_lower:
                return color
        
        # Fall back to theme palette
        palette = theme.colors['palette']
        # Simple hash-based selection for consistency
        index = hash(variable_name) % len(palette)
        return palette[index]
    
    def create_custom_theme(self, name: str, base_theme: str = "professional", 
                          color_overrides: Dict[str, str] = None,
                          typography_overrides: Dict[str, Any] = None,
                          layout_overrides: Dict[str, Any] = None) -> ChartTheme:
        """Create a custom theme based on an existing theme"""
        base = self.get_theme(base_theme)
        
        # Create copies and apply overrides
        colors = base.colors.copy()
        if color_overrides:
            colors.update(color_overrides)
        
        typography = base.typography.copy()
        if typography_overrides:
            typography.update(typography_overrides)
        
        layout = base.layout.copy()
        if layout_overrides:
            layout.update(layout_overrides)
        
        custom_theme = ChartTheme(
            name=name,
            colors=colors,
            typography=typography,
            layout=layout,
            accessibility=base.accessibility.copy()
        )
        
        self.custom_themes[name] = custom_theme
        return custom_theme
    
    def get_available_themes(self) -> List[str]:
        """Get list of all available themes"""
        return list(self.built_in_themes.keys()) + list(self.custom_themes.keys())
    
    def export_theme_preview(self, output_path: str, theme_names: List[str] = None):
        """Export a preview image showing different themes"""
        if theme_names is None:
            theme_names = list(self.built_in_themes.keys())
        
        # Create sample data
        x = np.linspace(0, 10, 100)
        y1 = np.sin(x)
        y2 = np.cos(x)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, theme_name in enumerate(theme_names[:4]):
            if i >= len(axes):
                break
                
            ax = axes[i]
            self.set_theme(theme_name)
            
            # Plot sample data
            ax.plot(x, y1, label='Sin(x)', linewidth=2)
            ax.plot(x, y2, label='Cos(x)', linewidth=2)
            ax.legend()
            
            self.apply_chart_styling(fig, ax, "Line Chart", 
                                   title=f"{self.get_theme(theme_name).name} Theme",
                                   x_label="X Values", 
                                   y_label="Y Values")
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

class ResponsiveChartManager:
    """Manages responsive chart behavior and adaptive layouts"""
    
    def __init__(self, style_manager: ChartStyleManager):
        self.style_manager = style_manager
        
        # Breakpoints for responsive design
        self.breakpoints = {
            'mobile': {'width': 480, 'height': 320},
            'tablet': {'width': 768, 'height': 512},
            'desktop': {'width': 1024, 'height': 640},
            'large': {'width': 1200, 'height': 800}
        }
    
    def get_responsive_config(self, container_width: int, container_height: int) -> Dict[str, Any]:
        """Get responsive configuration based on container size"""
        
        # Determine breakpoint
        breakpoint = 'mobile'
        for bp_name, bp_size in self.breakpoints.items():
            if container_width >= bp_size['width']:
                breakpoint = bp_name
        
        # Responsive configurations
        configs = {
            'mobile': {
                'figure_size': (8, 5),
                'title_size': 12,
                'label_size': 9,
                'tick_size': 7,
                'legend_size': 8,
                'margins': {'left': 0.15, 'right': 0.9, 'top': 0.85, 'bottom': 0.15},
                'max_categories': 8,
                'rotate_labels': True
            },
            'tablet': {
                'figure_size': (10, 6),
                'title_size': 14,
                'label_size': 10,
                'tick_size': 8,
                'legend_size': 9,
                'margins': {'left': 0.12, 'right': 0.92, 'top': 0.88, 'bottom': 0.12},
                'max_categories': 12,
                'rotate_labels': False
            },
            'desktop': {
                'figure_size': (12, 7),
                'title_size': 16,
                'label_size': 11,
                'tick_size': 9,
                'legend_size': 10,
                'margins': {'left': 0.1, 'right': 0.95, 'top': 0.9, 'bottom': 0.1},
                'max_categories': 20,
                'rotate_labels': False
            },
            'large': {
                'figure_size': (14, 8),
                'title_size': 18,
                'label_size': 12,
                'tick_size': 10,
                'legend_size': 11,
                'margins': {'left': 0.08, 'right': 0.97, 'top': 0.92, 'bottom': 0.08},
                'max_categories': 30,
                'rotate_labels': False
            }
        }
        
        return configs[breakpoint]
    
    def apply_responsive_styling(self, fig, ax, chart_type: str, 
                               container_width: int = 1024, container_height: int = 640,
                               title: str = "", x_label: str = "", y_label: str = "") -> None:
        """Apply responsive styling based on container size"""
        config = self.get_responsive_config(container_width, container_height)
        
        # Apply responsive figure size
        fig.set_size_inches(config['figure_size'])
        
        # Apply responsive margins
        margins = config['margins']
        fig.subplots_adjust(
            left=margins['left'],
            right=margins['right'],
            top=margins['top'],
            bottom=margins['bottom']
        )
        
        # Apply responsive typography
        if title:
            ax.set_title(title, fontsize=config['title_size'])
        if x_label:
            ax.set_xlabel(x_label, fontsize=config['label_size'])
        if y_label:
            ax.set_ylabel(y_label, fontsize=config['label_size'])
        
        # Apply responsive tick styling
        ax.tick_params(axis='both', which='major', labelsize=config['tick_size'])
        
        # Rotate labels if needed (mobile)
        if config.get('rotate_labels', False):
            ax.tick_params(axis='x', rotation=45)
        
        # Legend sizing
        legend = ax.get_legend()
        if legend:
            legend.set_fontsize(config['legend_size']) 