"""
Enhanced Chart Styling System

This module provides comprehensive styling capabilities for charts including
themes, responsive design, accessibility features, and professional formatting.
"""

from typing import Dict, List, Tuple, Any, Optional
from PySide6 import QtGui, QtCore, QtWidgets
# Lazy imports for matplotlib - deferred until first use
from core.optimization.lazy_imports import get_lazy_manager

class ChartTheme:
    """Represents a complete chart theme with colors, fonts, and styling options"""
    
    def __init__(self, name: str, colors: Dict[str, str], typography: Dict[str, Any], 
                 layout: Dict[str, Any], accessibility: Dict[str, Any] = None):
        self.name = name
        self.colors = colors
        self.typography = typography
        self.layout = layout
        self.accessibility = accessibility or {}

class QtChartStyleEnhancer:
    """Enhanced styling capabilities specifically for Qt Charts with gradients and modern effects"""
    
    def __init__(self):
        # Modern gradient color schemes
        self.gradient_palettes = {
            "ocean": {
                "primary": ["#667eea", "#764ba2"],
                "secondary": ["#f093fb", "#f5576c"],
                "accent": ["#4facfe", "#00f2fe"]
            },
            "sunset": {
                "primary": ["#fa709a", "#fee140"],
                "secondary": ["#ffd89b", "#19547b"],
                "accent": ["#667eea", "#764ba2"]
            },
            "forest": {
                "primary": ["#134e5e", "#71b280"],
                "secondary": ["#a8edea", "#fed6e3"],
                "accent": ["#d299c2", "#fef9d7"]
            },
            "aurora": {
                "primary": ["#2196f3", "#21cbf3"],
                "secondary": ["#45b7d1", "#96c93d"],
                "accent": ["#667eea", "#764ba2"]
            },
            "professional": {
                "primary": ["#5E81AC", "#88C0D0"],
                "secondary": ["#81A1C1", "#A3BE8C"],
                "accent": ["#EBCB8B", "#D08770"]
            },
            # NEW: Enhanced gradient collections
            "cosmic": {
                "primary": ["#4338ca", "#7c3aed"],
                "secondary": ["#c026d3", "#f59e0b"],
                "accent": ["#06b6d4", "#10b981"]
            },
            "fire": {
                "primary": ["#ef4444", "#f97316"],
                "secondary": ["#f59e0b", "#eab308"],
                "accent": ["#84cc16", "#22c55e"]
            },
            "ice": {
                "primary": ["#0ea5e9", "#06b6d4"],
                "secondary": ["#8b5cf6", "#a855f7"],
                "accent": ["#ec4899", "#f43f5e"]
            },
            "earth": {
                "primary": ["#78716c", "#a3a3a3"],
                "secondary": ["#84cc16", "#22c55e"],
                "accent": ["#f59e0b", "#ef4444"]
            },
            "neon": {
                "primary": ["#00ff41", "#00d4ff"],
                "secondary": ["#ff0080", "#ff4000"],
                "accent": ["#8000ff", "#0080ff"]
            }
        }
        
        # Modern solid color schemes for fallback
        self.modern_palettes = {
            "vibrant": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"],
            "corporate": ["#2C3E50", "#3498DB", "#E74C3C", "#F39C12", "#27AE60", "#9B59B6", "#E67E22", "#1ABC9C"],
            "pastel": ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#FFDFBA", "#E0BBE4", "#FFC9DE", "#C9C9FF"],
            "dark": ["#64FFDA", "#00BCD4", "#2196F3", "#9C27B0", "#E91E63", "#F44336", "#FF9800", "#4CAF50"],
            # NEW: Enhanced modern palettes
            "neo": ["#FF6B9D", "#45D1DC", "#FFE66D", "#A8E6CF", "#9B59B6", "#FF8C94", "#A8E6CF", "#C7CEEA"],
            "electric": ["#00F5FF", "#FF1744", "#76FF03", "#FFEA00", "#E91E63", "#3F51B5", "#FF9800", "#4CAF50"],
            "warm": ["#FF5722", "#FF9800", "#FFC107", "#FFEB3B", "#CDDC39", "#8BC34A", "#4CAF50", "#009688"],
            "cool": ["#2196F3", "#03DAC6", "#00BCD4", "#009688", "#4CAF50", "#8BC34A", "#CDDC39", "#FFC107"],
            "monochrome": ["#212121", "#424242", "#616161", "#757575", "#9E9E9E", "#BDBDBD", "#E0E0E0", "#F5F5F5"],
            "rainbow": ["#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00", "#00FF80", "#00FFFF", "#0080FF"]
        }
    
    def create_gradient_brush(self, start_color: str, end_color: str, direction: str = "vertical") -> QtGui.QBrush:
        """Create a gradient brush for Qt Charts"""
        gradient = QtGui.QLinearGradient()
        
        if direction == "vertical":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, 1)
        elif direction == "horizontal":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(1, 0)
        elif direction == "diagonal":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(1, 1)
        
        gradient.setColorAt(0, QtGui.QColor(start_color))
        gradient.setColorAt(1, QtGui.QColor(end_color))
        
        return QtGui.QBrush(gradient)
    
    def create_radial_gradient_brush(self, center_color: str, edge_color: str, center_x: float = 0.5, center_y: float = 0.5) -> QtGui.QBrush:
        """Create a radial gradient brush for modern chart effects"""
        gradient = QtGui.QRadialGradient()
        gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        gradient.setCenter(center_x, center_y)
        gradient.setRadius(0.8)
        
        gradient.setColorAt(0, QtGui.QColor(center_color))
        gradient.setColorAt(1, QtGui.QColor(edge_color))
        
        return QtGui.QBrush(gradient)
    
    def create_shadow_effect(self, blur_radius: int = 10, offset_x: int = 2, offset_y: int = 2, opacity: float = 0.3) -> QtWidgets.QGraphicsDropShadowEffect:
        """Create a drop shadow effect for chart elements"""
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(offset_x, offset_y)
        shadow.setColor(QtGui.QColor(0, 0, 0, int(opacity * 255)))
        return shadow
    
    def get_gradient_colors_for_palette(self, palette_name: str, count: int = 1) -> List[Tuple[str, str]]:
        """Get gradient color pairs for a specific palette"""
        if palette_name not in self.gradient_palettes:
            palette_name = "professional"
        
        palette = self.gradient_palettes[palette_name]
        gradient_pairs = []
        
        # Create gradient pairs from the palette
        primary = palette["primary"]
        secondary = palette["secondary"]
        accent = palette["accent"]
        
        all_gradients = [primary, secondary, accent]
        
        for i in range(count):
            gradient_pairs.append(all_gradients[i % len(all_gradients)])
        
        return gradient_pairs
    
    def apply_modern_styling_to_series(self, series, style_config: Dict[str, Any]):
        """Apply modern styling to a Qt Charts series"""
        if hasattr(series, 'setPen'):  # Line series
            pen = series.pen()
            if 'gradient' in style_config:
                # For line charts, we'll use a solid color but with enhanced styling
                pen.setColor(QtGui.QColor(style_config['gradient'][0]))
                pen.setWidth(style_config.get('line_width', 3))
                pen.setCapStyle(QtCore.Qt.RoundCap)
                pen.setJoinStyle(QtCore.Qt.RoundJoin)
                series.setPen(pen)
        
        if hasattr(series, 'setBrush'):  # Area series or bars
            if 'gradient' in style_config:
                gradient_brush = self.create_gradient_brush(
                    style_config['gradient'][0], 
                    style_config['gradient'][1],
                    style_config.get('gradient_direction', 'vertical')
                )
                series.setBrush(gradient_brush)
    
    def create_advanced_shadow_effect(self, shadow_type: str = "drop", blur_radius: int = 15, offset_x: int = 3, offset_y: int = 3, opacity: float = 0.4) -> QtWidgets.QGraphicsDropShadowEffect:
        """Create advanced shadow effects with different types"""
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        
        if shadow_type == "glow":
            # Glow effect - no offset, high blur
            shadow.setBlurRadius(blur_radius * 1.5)
            shadow.setOffset(0, 0)
            shadow.setColor(QtGui.QColor(100, 200, 255, int(opacity * 255)))
        elif shadow_type == "inner":
            # Inner shadow simulation
            shadow.setBlurRadius(blur_radius // 2)
            shadow.setOffset(-offset_x, -offset_y)
            shadow.setColor(QtGui.QColor(0, 0, 0, int(opacity * 200)))
        elif shadow_type == "long":
            # Long shadow effect
            shadow.setBlurRadius(blur_radius // 3)
            shadow.setOffset(offset_x * 3, offset_y * 3)
            shadow.setColor(QtGui.QColor(0, 0, 0, int(opacity * 150)))
        else:  # drop (default)
            shadow.setBlurRadius(blur_radius)
            shadow.setOffset(offset_x, offset_y)
            shadow.setColor(QtGui.QColor(0, 0, 0, int(opacity * 255)))
        
        return shadow
    
    def create_multi_gradient_brush(self, colors: List[str], direction: str = "vertical") -> QtGui.QBrush:
        """Create gradient brush with multiple color stops"""
        if len(colors) < 2:
            colors = colors + ["#FFFFFF"]  # Fallback
        
        gradient = QtGui.QLinearGradient()
        
        if direction == "vertical":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, 1)
        elif direction == "horizontal":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(1, 0)
        elif direction == "diagonal":
            gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(1, 1)
        
        # Distribute colors evenly across gradient
        for i, color in enumerate(colors):
            position = i / (len(colors) - 1) if len(colors) > 1 else 0
            gradient.setColorAt(position, QtGui.QColor(color))
        
        return QtGui.QBrush(gradient)
    
    def create_conical_gradient_brush(self, center_color: str, edge_color: str, center_x: float = 0.5, center_y: float = 0.5, angle: float = 0) -> QtGui.QBrush:
        """Create conical (angular) gradient brush for special effects"""
        gradient = QtGui.QConicalGradient()
        gradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        gradient.setCenter(center_x, center_y)
        gradient.setAngle(angle)
        
        gradient.setColorAt(0, QtGui.QColor(center_color))
        gradient.setColorAt(1, QtGui.QColor(edge_color))
        
        return QtGui.QBrush(gradient)

class ChartStyleManager:
    """Advanced chart styling system with themes, responsive design, and accessibility"""
    
    def __init__(self):
        self.current_theme = "professional"
        self.custom_themes = {}
        self._lazy_manager = get_lazy_manager()
        self._setup_lazy_imports()
        self._initialize_built_in_themes()
        
        # NEW: Qt Charts style enhancer
        self.qt_enhancer = QtChartStyleEnhancer()
        
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
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for heavy scientific libraries"""
        # Register matplotlib and numpy for lazy loading
        self._lazy_manager.register_module('matplotlib', 'matplotlib.pyplot')
        self._lazy_manager.register_module('matplotlib_patches', 'matplotlib.patches')
        self._lazy_manager.register_module('matplotlib_rcparams', 'matplotlib')
        self._lazy_manager.register_module('numpy', 'numpy')
    
    @property
    def plt(self):
        """Lazy-loaded matplotlib.pyplot module"""
        return self._lazy_manager.get_module('matplotlib')
    
    @property
    def patches(self):
        """Lazy-loaded matplotlib.patches module"""
        return self._lazy_manager.get_module('matplotlib_patches')
    
    @property
    def rcParams(self):
        """Lazy-loaded matplotlib rcParams"""
        matplotlib_module = self._lazy_manager.get_module('matplotlib_rcparams')
        return matplotlib_module.rcParams
    
    @property
    def np(self):
        """Lazy-loaded numpy module"""
        return self._lazy_manager.get_module('numpy')
    
    def _initialize_built_in_themes(self):
        """Initialize built-in chart themes"""
        
        # Professional Business Theme - ENHANCED with gradients
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
                    "background": "#232423",  # Changed from #FFFFFF to match app's dark theme
                    "surface": "#2a2b2a",     # Slightly lighter than background
                    "text": "#D6D6D6",       # Light text for dark background
                    "text_light": "#B0B0B0", # Adjusted for dark background
                    "grid": "#404040",       # Dark grid lines
                    "palette": ["#5E81AC", "#88C0D0", "#81A1C1", "#A3BE8C", "#EBCB8B", "#D08770", "#BF616A", "#B48EAD"],
                    # NEW: Gradient configurations
                    "gradients": {
                        "primary": ["#5E81AC", "#88C0D0"],
                        "secondary": ["#81A1C1", "#A3BE8C"],
                        "accent": ["#EBCB8B", "#D08770"]
                    }
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
                    "legend_shadow": False,
                    # NEW: Modern styling options
                    "use_gradients": True,
                    "shadow_effects": True,
                    "rounded_corners": True
                },
                accessibility={
                    "high_contrast": False,
                    "colorblind_safe": True,
                    "pattern_fills": False
                }
            ),
            
            # Modern Dark Theme - ENHANCED with gradients
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
                    "palette": ["#64FFDA", "#00BCD4", "#2196F3", "#9C27B0", "#E91E63", "#F44336", "#FF9800", "#4CAF50"],
                    # NEW: Dark theme gradients
                    "gradients": {
                        "primary": ["#64FFDA", "#00BCD4"],
                        "secondary": ["#2196F3", "#9C27B0"],
                        "accent": ["#E91E63", "#F44336"]
                    }
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
                    "legend_shadow": False,
                    # NEW: Enhanced dark theme styling
                    "use_gradients": True,
                    "shadow_effects": True,
                    "rounded_corners": True,
                    "glow_effects": True  # Special for dark theme
                },
                accessibility={
                    "high_contrast": True,
                    "colorblind_safe": True,
                    "pattern_fills": False
                }
            ),
            
            # Minimal Clean Theme - ENHANCED with subtle gradients
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
                    "palette": ["#007AFF", "#5AC8FA", "#34C759", "#FF9500", "#FF3B30", "#AF52DE", "#FF2D92", "#5856D6"],
                    # NEW: Minimal theme subtle gradients
                    "gradients": {
                        "primary": ["#007AFF", "#5AC8FA"],
                        "secondary": ["#34C759", "#FF9500"],
                        "accent": ["#AF52DE", "#FF2D92"]
                    }
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
                    "legend_shadow": False,
                    # NEW: Minimal modern styling
                    "use_gradients": False,  # Very subtle or no gradients
                    "shadow_effects": False,  # Clean, no shadows
                    "rounded_corners": True
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
        """Apply current theme to matplotlib global settings with error handling"""
        try:
            theme = self.get_theme()
            
            # Build matplotlib configuration
            config = self.base_config.copy()
            
            # Apply theme colors
            config.update({
                'figure.facecolor': theme.colors['background'],
                'axes.facecolor': theme.colors['background'],
                'savefig.facecolor': theme.colors['background'],
                'text.color': theme.colors['text'],
                'axes.labelcolor': theme.colors['text'],
                'xtick.color': theme.colors['text'],
                'ytick.color': theme.colors['text'],
                'axes.edgecolor': theme.colors['grid'],
                'grid.color': theme.colors['grid'],
                'grid.alpha': theme.layout['grid_alpha']
            })
            
            # Apply typography
            config.update({
                'font.family': theme.typography['font_family'],
                'font.size': theme.typography['tick_size'],
                'axes.titlesize': theme.typography['title_size'],
                'axes.labelsize': theme.typography['label_size'],
                'xtick.labelsize': theme.typography['tick_size'],
                'ytick.labelsize': theme.typography['tick_size'],
                'legend.fontsize': theme.typography['legend_size'],
                'axes.titleweight': theme.typography['title_weight'],
                'axes.labelweight': theme.typography['label_weight']
            })
            
            # Apply layout
            config.update({
                'axes.spines.left': True,
                'axes.spines.bottom': True,
                'axes.spines.top': False,
                'axes.spines.right': False,
                'axes.linewidth': theme.layout['spine_width'],
                'xtick.major.size': theme.layout['tick_length'],
                'ytick.major.size': theme.layout['tick_length'],
                'legend.frameon': theme.layout['legend_frameon'],
                'legend.shadow': theme.layout['legend_shadow']
            })
            
            # Update rcParams with theme values
            self.rcParams.update(config)
        except ImportError:
            # Matplotlib not available - skip theme application
            pass
        except Exception as e:
            # Log other errors but don't crash
            import logging
            logging.warning(f"Failed to apply matplotlib theme: {e}")
    
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

    # NEW: Qt Charts specific methods
    def get_qt_gradient_brush(self, theme_name: str = None, gradient_type: str = "primary", direction: str = "vertical") -> QtGui.QBrush:
        """Get a gradient brush for Qt Charts based on current theme"""
        theme = self.get_theme(theme_name)
        
        if "gradients" in theme.colors and gradient_type in theme.colors["gradients"]:
            gradient_colors = theme.colors["gradients"][gradient_type]
            return self.qt_enhancer.create_gradient_brush(
                gradient_colors[0], 
                gradient_colors[1], 
                direction
            )
        else:
            # Fallback to solid color
            color = theme.colors.get(gradient_type, theme.colors.get("primary", "#5E81AC"))
            return QtGui.QBrush(QtGui.QColor(color))
    
    def get_qt_shadow_effect(self, theme_name: str = None) -> QtWidgets.QGraphicsDropShadowEffect:
        """Get a shadow effect for Qt Charts based on current theme"""
        theme = self.get_theme(theme_name)
        
        if theme.layout.get("shadow_effects", False):
            if theme.name == "Dark Mode":
                # Stronger shadow for dark theme
                return self.qt_enhancer.create_shadow_effect(
                    blur_radius=15, offset_x=3, offset_y=3, opacity=0.5
                )
            else:
                # Subtle shadow for light themes
                return self.qt_enhancer.create_shadow_effect(
                    blur_radius=10, offset_x=2, offset_y=2, opacity=0.3
                )
        return None
    
    def get_modern_color_palette(self, theme_name: str = None, palette_type: str = "vibrant") -> List[str]:
        """Get modern color palette for Qt Charts"""
        theme = self.get_theme(theme_name)
        
        # First try theme's own palette
        if "palette" in theme.colors:
            return theme.colors["palette"]
        
        # Fallback to modern palettes from Qt enhancer
        if palette_type in self.qt_enhancer.modern_palettes:
            return self.qt_enhancer.modern_palettes[palette_type]
        
        # Final fallback
        return self.qt_enhancer.modern_palettes["corporate"]
    
    def apply_qt_series_styling(self, series, variable_name: str, series_index: int = 0, theme_name: str = None):
        """Apply modern styling to a Qt Charts series"""
        theme = self.get_theme(theme_name)
        
        # Get semantic color
        base_color = self.get_semantic_color(variable_name, theme_name)
        
        # Build style configuration
        style_config = {
            "base_color": base_color,
            "series_index": series_index
        }
        
        # Add gradient if theme supports it
        if theme.layout.get("use_gradients", False) and "gradients" in theme.colors:
            gradients = list(theme.colors["gradients"].values())
            gradient_pair = gradients[series_index % len(gradients)]
            style_config["gradient"] = gradient_pair
            style_config["gradient_direction"] = "vertical"
        
        # Enhanced line styling
        if theme.layout.get("rounded_corners", False):
            style_config["line_width"] = 3
        else:
            style_config["line_width"] = 2
        
        # Apply the styling
        self.qt_enhancer.apply_modern_styling_to_series(series, style_config)
        
        return style_config
    
    def get_chart_background_brush(self, theme_name: str = None) -> QtGui.QBrush:
        """Get chart background brush with optional gradient"""
        theme = self.get_theme(theme_name)
        
        background_color = theme.colors.get("background", "#FFFFFF")
        surface_color = theme.colors.get("surface", background_color)
        
        # For dark themes, use subtle gradient
        if theme.name == "Dark Mode":
            return self.qt_enhancer.create_gradient_brush(
                background_color, surface_color, "diagonal"
            )
        else:
            return QtGui.QBrush(QtGui.QColor(background_color))
    
    def export_theme_preview(self, output_path: str, theme_names: List[str] = None):
        """Export a preview image showing different themes"""
        if theme_names is None:
            theme_names = list(self.built_in_themes.keys())
        
        # Create sample data
        x = self.np.linspace(0, 10, 100)
        y1 = self.np.sin(x)
        y2 = self.np.cos(x)
        
        fig, axes = self.plt.subplots(2, 2, figsize=(15, 10))
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
        
        self.plt.tight_layout()
        self.plt.savefig(output_path, dpi=300, bbox_inches='tight')
        self.plt.close()

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