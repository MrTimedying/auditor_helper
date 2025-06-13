"""
Intelligent Variable Suggestion System

This module provides context-aware, data-driven suggestions for variable selection
in chart creation, improving user experience and chart effectiveness.
"""

from typing import Dict, List, Tuple, Any, Optional, Set
from enum import Enum
import statistics
from collections import Counter

class SuggestionType(Enum):
    """Types of suggestions the system can provide"""
    RECOMMENDED = "recommended"  # Strongly recommended
    COMPATIBLE = "compatible"    # Works well with current selection
    WARNING = "warning"          # Potential issues
    ALTERNATIVE = "alternative"  # Better alternatives available

class VariableSuggestion:
    """Represents a single variable suggestion with reasoning"""
    
    def __init__(self, variable_name: str, variable_type: str, suggestion_type: SuggestionType,
                 reason: str, confidence: float = 1.0, metadata: Dict[str, Any] = None):
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.suggestion_type = suggestion_type
        self.reason = reason
        self.confidence = confidence  # 0.0 to 1.0
        self.metadata = metadata or {}

class ChartTypeSuggestion:
    """Represents a chart type suggestion based on variable selection"""
    
    def __init__(self, chart_type: str, suitability_score: float, reasons: List[str],
                 potential_issues: List[str] = None):
        self.chart_type = chart_type
        self.suitability_score = suitability_score  # 0.0 to 1.0
        self.reasons = reasons
        self.potential_issues = potential_issues or []

class VariableAnalyzer:
    """Analyzes variable characteristics and data patterns"""
    
    def __init__(self):
        # Statistical thresholds for analysis
        self.high_cardinality_threshold = 20
        self.low_cardinality_threshold = 5
        self.outlier_threshold = 3.0  # Standard deviations
        self.null_rate_warning_threshold = 0.1  # 10%
        
    def analyze_variable_data(self, variable_name: str, data: List[Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis of variable data"""
        if not data:
            return self._empty_analysis(variable_name)
        
        # Filter out None values for analysis
        clean_data = [val for val in data if val is not None]
        null_rate = (len(data) - len(clean_data)) / len(data) if data else 0
        
        analysis = {
            "variable_name": variable_name,
            "total_count": len(data),
            "valid_count": len(clean_data),
            "null_rate": null_rate,
            "data_type": self._detect_data_type(clean_data),
            "cardinality": len(set(clean_data)) if clean_data else 0,
            "unique_values": list(set(clean_data))[:10] if clean_data else [],  # Sample of unique values
        }
        
        # Additional analysis for quantitative data
        if analysis["data_type"] == "quantitative" and clean_data:
            try:
                numeric_data = [float(val) for val in clean_data if self._is_numeric(val)]
                if numeric_data:
                    analysis.update(self._analyze_numeric_data(numeric_data))
            except (ValueError, TypeError):
                pass
        
        # Additional analysis for categorical data
        if analysis["data_type"] == "categorical" and clean_data:
            analysis.update(self._analyze_categorical_data(clean_data))
        
        return analysis
    
    def _empty_analysis(self, variable_name: str) -> Dict[str, Any]:
        """Return analysis for empty data"""
        return {
            "variable_name": variable_name,
            "total_count": 0,
            "valid_count": 0,
            "null_rate": 1.0,
            "data_type": "unknown",
            "cardinality": 0,
            "unique_values": [],
            "issues": ["No data available"]
        }
    
    def _detect_data_type(self, data: List[Any]) -> str:
        """Detect whether data is categorical or quantitative"""
        if not data:
            return "unknown"
        
        # Check if most values are numeric
        numeric_count = sum(1 for val in data if self._is_numeric(val))
        numeric_ratio = numeric_count / len(data)
        
        # If most values are numeric and there are many unique values, likely quantitative
        if numeric_ratio > 0.8:
            unique_ratio = len(set(data)) / len(data)
            if unique_ratio > 0.1 or len(set(data)) > self.low_cardinality_threshold:
                return "quantitative"
        
        return "categorical"
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if a value can be converted to a number"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _analyze_numeric_data(self, data: List[float]) -> Dict[str, Any]:
        """Analyze numeric data for patterns and characteristics"""
        analysis = {}
        
        try:
            analysis["min_value"] = min(data)
            analysis["max_value"] = max(data)
            analysis["mean"] = statistics.mean(data)
            analysis["median"] = statistics.median(data)
            
            if len(data) > 1:
                analysis["std_dev"] = statistics.stdev(data)
                
                # Detect outliers using standard deviation method
                mean = analysis["mean"]
                std_dev = analysis["std_dev"]
                outliers = [val for val in data if abs(val - mean) > self.outlier_threshold * std_dev]
                analysis["outlier_count"] = len(outliers)
                analysis["outlier_rate"] = len(outliers) / len(data)
            
            # Detect if data looks like a time series or date
            analysis["is_likely_temporal"] = self._detect_temporal_pattern(data)
            
        except (ValueError, ZeroDivisionError):
            analysis["analysis_failed"] = True
        
        return analysis
    
    def _analyze_categorical_data(self, data: List[Any]) -> Dict[str, Any]:
        """Analyze categorical data for patterns"""
        value_counts = Counter(data)
        total_count = len(data)
        
        analysis = {
            "most_common": value_counts.most_common(5),
            "value_distribution": dict(value_counts),
            "is_high_cardinality": len(value_counts) > self.high_cardinality_threshold,
            "is_low_cardinality": len(value_counts) < self.low_cardinality_threshold,
            "uniformity": self._calculate_uniformity(value_counts, total_count)
        }
        
        # Check if it looks like a date/time categorical variable
        sample_values = [str(val) for val in list(value_counts.keys())[:5]]
        analysis["is_likely_temporal"] = self._detect_temporal_categorical(sample_values)
        
        return analysis
    
    def _detect_temporal_pattern(self, data: List[float]) -> bool:
        """Detect if numeric data represents temporal values"""
        # Simple heuristics for temporal data
        if not data:
            return False
        
        # Check if values are sequential or incrementing
        sorted_data = sorted(data)
        if len(sorted_data) > 2:
            differences = [sorted_data[i+1] - sorted_data[i] for i in range(len(sorted_data)-1)]
            avg_diff = sum(differences) / len(differences)
            
            # If differences are relatively consistent, might be temporal
            consistent_diffs = sum(1 for diff in differences if abs(diff - avg_diff) < avg_diff * 0.5)
            consistency_ratio = consistent_diffs / len(differences)
            
            return consistency_ratio > 0.7
        
        return False
    
    def _detect_temporal_categorical(self, sample_values: List[str]) -> bool:
        """Detect if categorical values represent dates/times"""
        temporal_indicators = [
            "-", "/", ":", "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "mon", "tue", "wed", "thu", "fri", "sat", "sun", "week", "day", "month", "year"
        ]
        
        matches = 0
        for value in sample_values:
            value_lower = str(value).lower()
            if any(indicator in value_lower for indicator in temporal_indicators):
                matches += 1
        
        return matches > len(sample_values) * 0.5
    
    def _calculate_uniformity(self, value_counts: Counter, total_count: int) -> float:
        """Calculate how uniformly distributed the categorical values are"""
        if not value_counts:
            return 0.0
        
        # Calculate entropy-like measure
        probabilities = [count / total_count for count in value_counts.values()]
        expected_prob = 1.0 / len(value_counts)
        
        # Measure deviation from uniform distribution
        deviations = [abs(prob - expected_prob) for prob in probabilities]
        avg_deviation = sum(deviations) / len(deviations)
        
        # Convert to uniformity score (1.0 = perfectly uniform, 0.0 = highly skewed)
        return max(0.0, 1.0 - (avg_deviation / expected_prob))

class IntelligentVariableSuggester:
    """Main class for providing intelligent variable suggestions"""
    
    def __init__(self):
        self.analyzer = VariableAnalyzer()
        
        # Chart type compatibility rules
        self.chart_compatibility = {
            "Line Chart": {
                "preferred_x": ["quantitative", "temporal"],
                "preferred_y": ["quantitative"],
                "min_variables": 1,
                "max_variables": 10,
                "best_for": ["trends", "time_series", "continuous_data"]
            },
            "Bar Chart": {
                "preferred_x": ["categorical"],
                "preferred_y": ["quantitative"],
                "min_variables": 1,
                "max_variables": 8,
                "best_for": ["comparisons", "categorical_analysis"]
            },
            "Scatter Plot": {
                "preferred_x": ["quantitative"],
                "preferred_y": ["quantitative"],
                "min_variables": 1,
                "max_variables": 1,
                "best_for": ["correlations", "relationships"]
            },
            "Pie Chart": {
                "preferred_x": ["categorical"],
                "preferred_y": ["quantitative"],
                "min_variables": 1,
                "max_variables": 1,
                "best_for": ["proportions", "parts_of_whole"]
            }
        }
        
        # Variable role suggestions
        self.role_suggestions = {
            "categorical_low_cardinality": ["x_axis", "grouping"],
            "categorical_high_cardinality": ["filtering", "avoid_x_axis"],
            "quantitative_continuous": ["y_axis", "x_axis"],
            "temporal": ["x_axis_primary"],
            "binary": ["y_axis", "filtering"]
        }
    
    def get_variable_suggestions(self, current_selection: Dict[str, Any], 
                               available_variables: List[Tuple[str, str]], 
                               data_samples: Dict[str, List[Any]] = None) -> List[VariableSuggestion]:
        """Get intelligent suggestions for variable selection"""
        suggestions = []
        
        # Analyze current selection context
        context = self._analyze_selection_context(current_selection)
        
        # Get data analysis if available
        data_analysis = {}
        if data_samples:
            for var_name, var_type in available_variables:
                if var_name in data_samples:
                    data_analysis[var_name] = self.analyzer.analyze_variable_data(
                        var_name, data_samples[var_name]
                    )
        
        # Generate suggestions for each available variable
        for var_name, var_type in available_variables:
            var_suggestions = self._suggest_for_variable(
                var_name, var_type, context, data_analysis.get(var_name, {})
            )
            suggestions.extend(var_suggestions)
        
        # Sort suggestions by confidence and type priority
        suggestions.sort(key=lambda s: (s.suggestion_type.value, -s.confidence))
        
        return suggestions
    
    def get_chart_type_suggestions(self, x_variable: Optional[Tuple[str, str]], 
                                 y_variables: List[Tuple[str, str]],
                                 data_analysis: Dict[str, Dict[str, Any]] = None) -> List[ChartTypeSuggestion]:
        """Suggest appropriate chart types based on variable selection"""
        suggestions = []
        
        if not x_variable:
            return suggestions
        
        x_var_name, x_var_type = x_variable
        x_analysis = data_analysis.get(x_var_name, {}) if data_analysis else {}
        
        # Evaluate each chart type
        for chart_type, rules in self.chart_compatibility.items():
            score, reasons, issues = self._evaluate_chart_type_suitability(
                chart_type, rules, x_variable, y_variables, x_analysis
            )
            
            if score > 0:  # Only include viable options
                suggestions.append(ChartTypeSuggestion(
                    chart_type=chart_type,
                    suitability_score=score,
                    reasons=reasons,
                    potential_issues=issues
                ))
        
        # Sort by suitability score
        suggestions.sort(key=lambda s: -s.suitability_score)
        
        return suggestions
    
    def _analyze_selection_context(self, current_selection: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current variable selection context"""
        context = {
            "has_x_variable": bool(current_selection.get("x_variable")),
            "y_variable_count": len(current_selection.get("y_variables", [])),
            "chart_type": current_selection.get("chart_type"),
            "selected_variables": set()
        }
        
        # Collect all selected variable names
        if current_selection.get("x_variable"):
            context["selected_variables"].add(current_selection["x_variable"][0])
        
        for y_var in current_selection.get("y_variables", []):
            context["selected_variables"].add(y_var[0])
        
        return context
    
    def _suggest_for_variable(self, var_name: str, var_type: str, 
                            context: Dict[str, Any], analysis: Dict[str, Any]) -> List[VariableSuggestion]:
        """Generate suggestions for a specific variable"""
        suggestions = []
        
        # Skip if already selected
        if var_name in context["selected_variables"]:
            return suggestions
        
        # Check for data quality issues
        if analysis.get("null_rate", 0) > 0.5:
            suggestions.append(VariableSuggestion(
                variable_name=var_name,
                variable_type=var_type,
                suggestion_type=SuggestionType.WARNING,
                reason=f"High null rate ({analysis['null_rate']:.1%}) - may not provide meaningful insights",
                confidence=0.9
            ))
        
        # Suggest role based on variable characteristics
        role_suggestions = self._get_role_suggestions(var_name, var_type, analysis, context)
        suggestions.extend(role_suggestions)
        
        # Suggest based on semantic meaning
        semantic_suggestions = self._get_semantic_suggestions(var_name, var_type, context)
        suggestions.extend(semantic_suggestions)
        
        return suggestions
    
    def _get_role_suggestions(self, var_name: str, var_type: str, 
                            analysis: Dict[str, Any], context: Dict[str, Any]) -> List[VariableSuggestion]:
        """Suggest appropriate roles for the variable based on its characteristics"""
        suggestions = []
        
        # Temporal variables are excellent for X-axis
        if analysis.get("is_likely_temporal", False):
            if not context["has_x_variable"]:
                suggestions.append(VariableSuggestion(
                    variable_name=var_name,
                    variable_type=var_type,
                    suggestion_type=SuggestionType.RECOMMENDED,
                    reason="Temporal data works excellently as X-axis for trend analysis",
                    confidence=0.9
                ))
        
        # High cardinality categorical variables
        if var_type == "categorical" and analysis.get("is_high_cardinality", False):
            suggestions.append(VariableSuggestion(
                variable_name=var_name,
                variable_type=var_type,
                suggestion_type=SuggestionType.WARNING,
                reason=f"High cardinality ({analysis.get('cardinality', 0)} categories) may create cluttered visualizations",
                confidence=0.8
            ))
        
        # Low cardinality categorical variables are great for grouping
        if var_type == "categorical" and analysis.get("is_low_cardinality", False):
            if not context["has_x_variable"]:
                suggestions.append(VariableSuggestion(
                    variable_name=var_name,
                    variable_type=var_type,
                    suggestion_type=SuggestionType.RECOMMENDED,
                    reason="Low cardinality categorical data is ideal for comparisons",
                    confidence=0.8
                ))
        
        # Quantitative variables with outliers
        if var_type == "quantitative" and analysis.get("outlier_rate", 0) > 0.1:
            suggestions.append(VariableSuggestion(
                variable_name=var_name,
                variable_type=var_type,
                suggestion_type=SuggestionType.WARNING,
                reason=f"Contains outliers ({analysis['outlier_rate']:.1%}) - consider data cleaning",
                confidence=0.7
            ))
        
        return suggestions
    
    def _get_semantic_suggestions(self, var_name: str, var_type: str, 
                                context: Dict[str, Any]) -> List[VariableSuggestion]:
        """Provide suggestions based on variable name semantics"""
        suggestions = []
        var_name_lower = var_name.lower()
        
        # Date/time variables
        if any(term in var_name_lower for term in ["date", "time", "week", "day", "month", "year"]):
            if not context["has_x_variable"]:
                suggestions.append(VariableSuggestion(
                    variable_name=var_name,
                    variable_type=var_type,
                    suggestion_type=SuggestionType.RECOMMENDED,
                    reason="Date/time variables are excellent for X-axis to show trends over time",
                    confidence=0.9
                ))
        
        # Performance metrics work well together
        performance_terms = ["fail", "error", "success", "rate", "score", "performance"]
        if any(term in var_name_lower for term in performance_terms):
            if context["y_variable_count"] == 0:
                suggestions.append(VariableSuggestion(
                    variable_name=var_name,
                    variable_type=var_type,
                    suggestion_type=SuggestionType.RECOMMENDED,
                    reason="Performance metrics provide valuable insights as Y-axis variables",
                    confidence=0.8
                ))
        
        # Financial metrics
        financial_terms = ["earning", "revenue", "profit", "cost", "bonus", "pay"]
        if any(term in var_name_lower for term in financial_terms):
            suggestions.append(VariableSuggestion(
                variable_name=var_name,
                variable_type=var_type,
                suggestion_type=SuggestionType.RECOMMENDED,
                reason="Financial metrics are important for performance analysis",
                confidence=0.8
            ))
        
        return suggestions
    
    def _evaluate_chart_type_suitability(self, chart_type: str, rules: Dict[str, Any],
                                       x_variable: Tuple[str, str], y_variables: List[Tuple[str, str]],
                                       x_analysis: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Evaluate how suitable a chart type is for the given variables"""
        score = 0.0
        reasons = []
        issues = []
        
        x_var_name, x_var_type = x_variable
        
        # Check X-axis compatibility
        if x_var_type in rules.get("preferred_x", []):
            score += 0.4
            reasons.append(f"X-axis type '{x_var_type}' is well-suited for {chart_type}")
        elif x_var_type not in rules.get("preferred_x", []):
            score -= 0.2
            issues.append(f"X-axis type '{x_var_type}' is not optimal for {chart_type}")
        
        # Check Y-axis compatibility
        y_compatible_count = 0
        for y_var_name, y_var_type in y_variables:
            if y_var_type in rules.get("preferred_y", []):
                y_compatible_count += 1
        
        if y_variables:
            y_compatibility = y_compatible_count / len(y_variables)
            score += 0.3 * y_compatibility
            if y_compatibility > 0.7:
                reasons.append("Y-axis variables are compatible with this chart type")
        
        # Check variable count constraints
        y_count = len(y_variables)
        min_vars = rules.get("min_variables", 1)
        max_vars = rules.get("max_variables", 10)
        
        if min_vars <= y_count <= max_vars:
            score += 0.2
            reasons.append(f"Variable count ({y_count}) is appropriate for {chart_type}")
        else:
            if y_count < min_vars:
                issues.append(f"Need at least {min_vars} Y-variable(s) for {chart_type}")
            else:
                issues.append(f"Too many Y-variables ({y_count}) for {chart_type} (max: {max_vars})")
        
        # Special considerations based on data analysis
        if x_analysis.get("is_high_cardinality", False) and chart_type in ["Bar Chart", "Pie Chart"]:
            score -= 0.2
            issues.append("High cardinality X-axis may create cluttered visualization")
        
        if x_analysis.get("is_likely_temporal", False) and chart_type == "Line Chart":
            score += 0.1
            reasons.append("Temporal data works excellently with line charts")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score, reasons, issues
    
    def get_variable_relationships(self, variables: List[str], 
                                 data_samples: Dict[str, List[Any]]) -> Dict[str, List[str]]:
        """Identify relationships between variables that work well together"""
        relationships = {}
        
        # Simple relationship detection based on semantic similarity
        for var1 in variables:
            related = []
            var1_lower = var1.lower()
            
            for var2 in variables:
                if var1 == var2:
                    continue
                
                var2_lower = var2.lower()
                
                # Check for semantic relationships
                if self._are_semantically_related(var1_lower, var2_lower):
                    related.append(var2)
            
            if related:
                relationships[var1] = related
        
        return relationships
    
    def _are_semantically_related(self, var1: str, var2: str) -> bool:
        """Check if two variables are semantically related"""
        # Performance metrics
        performance_terms = ["fail", "error", "success", "rate", "score", "performance", "efficiency"]
        var1_performance = any(term in var1 for term in performance_terms)
        var2_performance = any(term in var2 for term in performance_terms)
        
        if var1_performance and var2_performance:
            return True
        
        # Financial metrics
        financial_terms = ["earning", "revenue", "profit", "cost", "bonus", "pay", "money"]
        var1_financial = any(term in var1 for term in financial_terms)
        var2_financial = any(term in var2 for term in financial_terms)
        
        if var1_financial and var2_financial:
            return True
        
        # Time-related metrics
        time_terms = ["time", "duration", "speed", "pace"]
        var1_time = any(term in var1 for term in time_terms)
        var2_time = any(term in var2 for term in time_terms)
        
        if var1_time and var2_time:
            return True
        
        return False 