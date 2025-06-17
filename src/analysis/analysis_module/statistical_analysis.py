from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

import math
import statistics

@dataclass
class BoxPlotStats:
    """Statistics for box plot visualization"""
    q1: float
    median: float  # Q2
    q3: float
    iqr: float
    lower_whisker: float  # Actual minimum within 1.5*IQR of Q1
    upper_whisker: float  # Actual maximum within 1.5*IQR of Q3
    outliers: List[float]  # Values beyond whiskers
    min_value: float  # Absolute minimum in dataset
    max_value: float  # Absolute maximum in dataset
    sample_size: int

@dataclass
class CorrelationMatrix:
    """Data class for correlation matrix results"""
    matrix: List[List[float]]
    labels: List[str]
    correlation_type: str
    sample_size: int
    p_values: Optional[List[List[float]]] = None
    
    def get_correlation(self, var1: str, var2: str) -> Optional[float]:
        """Get correlation between two variables"""
        try:
            idx1 = self.labels.index(var1)
            idx2 = self.labels.index(var2)
            return self.matrix[idx1][idx2]
        except ValueError:
            return None
    
    def get_significant_correlations(self, threshold: float = 0.05) -> List[Tuple[str, str, float]]:
        """Get statistically significant correlations"""
        if not self.p_values:
            return []
        
        significant = []
        for i, var1 in enumerate(self.labels):
            for j, var2 in enumerate(self.labels):
                if i < j and self.p_values[i][j] < threshold:
                    correlation = self.matrix[i][j]
                    significant.append((var1, var2, correlation))
        
        return significant

class StatisticalAnalysis:
    """Provide comprehensive statistical utilities for chart overlays & insights."""

    def __init__(self):
        self.outlier_methods = ['iqr', 'zscore', 'modified_zscore']

    def calculate_linear_regression(self, x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
        """Return slope and intercept for simple linear regression (y = m*x + b).
        If variance is zero, slope is 0.
        """
        if not x_values or not y_values or len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must be of same length and non-empty")

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x*y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x*x for x in x_values)

        denominator = n * sum_x2 - sum_x ** 2
        if math.isclose(denominator, 0):
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept

    def calculate_r_squared(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate R-squared (coefficient of determination) for linear regression."""
        if not x_values or not y_values or len(x_values) != len(y_values):
            return 0.0
        
        if len(y_values) < 2:
            return 0.0
        
        # Check if Y values are constant (no variance)
        y_mean = sum(y_values) / len(y_values)
        y_variance = sum((y - y_mean) ** 2 for y in y_values)
        if math.isclose(y_variance, 0):
            return 0.0  # No variance in Y means no relationship to explain
            
        slope, intercept = self.calculate_linear_regression(x_values, y_values)
        
        # Calculate predicted values
        y_predicted = [slope * x + intercept for x in x_values]
        
        # Calculate total sum of squares (TSS) and residual sum of squares (RSS)
        tss = sum((y - y_mean) ** 2 for y in y_values)
        rss = sum((y_actual - y_pred) ** 2 for y_actual, y_pred in zip(y_values, y_predicted))
        
        # Avoid division by zero
        if math.isclose(tss, 0):
            return 1.0 if math.isclose(rss, 0) else 0.0
        
        r_squared = 1 - (rss / tss)
        return max(0.0, min(1.0, r_squared))  # Clamp between 0 and 1

    def calculate_confidence_intervals(self, x_values: List[float], y_values: List[float], 
                                     confidence_level: float = 0.95) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Calculate confidence intervals for regression line and prediction bands.
        
        Returns:
            Tuple of (confidence_intervals, prediction_bands)
            Each is a list of (lower_bound, upper_bound) tuples corresponding to x_values
        """
        if not x_values or not y_values or len(x_values) != len(y_values) or len(x_values) < 3:
            return [], []
        
        n = len(x_values)
        slope, intercept = self.calculate_linear_regression(x_values, y_values)
        
        # Calculate residuals and standard error
        y_predicted = [slope * x + intercept for x in x_values]
        residuals = [y_actual - y_pred for y_actual, y_pred in zip(y_values, y_predicted)]
        
        # Standard error of the estimate
        mse = sum(r ** 2 for r in residuals) / (n - 2)
        se = math.sqrt(mse)
        
        # t-value for confidence level (approximation for large samples)
        alpha = 1 - confidence_level
        if n > 30:
            t_value = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        else:
            # Simplified t-values for small samples
            t_value = 2.0 if confidence_level == 0.95 else 2.5
        
        # Calculate means and sums for standard errors
        x_mean = sum(x_values) / n
        sum_x_squared_deviations = sum((x - x_mean) ** 2 for x in x_values)
        
        confidence_intervals = []
        prediction_bands = []
        
        for x in x_values:
            y_pred = slope * x + intercept
            
            # Standard error for confidence interval (mean response)
            se_mean = se * math.sqrt(1/n + (x - x_mean)**2 / sum_x_squared_deviations)
            ci_margin = t_value * se_mean
            
            # Standard error for prediction interval (individual response)
            se_pred = se * math.sqrt(1 + 1/n + (x - x_mean)**2 / sum_x_squared_deviations)
            pred_margin = t_value * se_pred
            
            confidence_intervals.append((y_pred - ci_margin, y_pred + ci_margin))
            prediction_bands.append((y_pred - pred_margin, y_pred + pred_margin))
        
        return confidence_intervals, prediction_bands

    def calculate_moving_average(self, values: List[float], window_size: int) -> List[Optional[float]]:
        """Calculate moving average with specified window size.
        
        Returns list same length as input, with None for positions where window is incomplete.
        """
        if window_size <= 0 or window_size > len(values):
            return [None] * len(values)
        
        moving_averages = []
        for i in range(len(values)):
            if i < window_size - 1:
                moving_averages.append(None)
            else:
                window_values = values[i - window_size + 1:i + 1]
                avg = sum(window_values) / window_size
                moving_averages.append(avg)
        
        return moving_averages

    def calculate_exponential_moving_average(self, values: List[float], alpha: float = 0.3) -> List[float]:
        """Calculate exponential moving average with smoothing factor alpha.
        
        Args:
            values: Input data series
            alpha: Smoothing factor (0 < alpha <= 1). Higher values give more weight to recent observations.
        """
        if not values or alpha <= 0 or alpha > 1:
            return []
        
        ema = [values[0]]  # First value is the initial EMA
        
        for i in range(1, len(values)):
            ema_value = alpha * values[i] + (1 - alpha) * ema[i-1]
            ema.append(ema_value)
        
        return ema

    def calculate_standard_deviation(self, values: List[float]) -> Tuple[float, float]:
        """Calculate sample standard deviation and variance.
        
        Returns:
            Tuple of (standard_deviation, variance)
        """
        if len(values) < 2:
            return 0.0, 0.0
        
        try:
            std_dev = statistics.stdev(values)
            variance = statistics.variance(values)
            return std_dev, variance
        except statistics.StatisticsError:
            return 0.0, 0.0

    def calculate_statistical_summary(self, values: List[float]) -> Dict[str, float]:
        """Calculate comprehensive statistical summary of a dataset.
        
        Returns:
            Dictionary with mean, median, mode, std_dev, variance, min, max, range
        """
        if not values:
            return {}
        
        try:
            summary = {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
                'variance': statistics.variance(values) if len(values) > 1 else 0.0,
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values),
                'count': len(values)
            }
            
            # Try to calculate mode, but handle cases where there's no unique mode
            try:
                summary['mode'] = statistics.mode(values)
            except statistics.StatisticsError:
                summary['mode'] = None
                
            return summary
        except Exception:
            return {}

    def generate_trend_points(self, x_values: List[float], y_values: List[float]) -> List[Tuple[float, float]]:
        """Generate points representing a linear trend line spanning the given x range."""
        slope, intercept = self.calculate_linear_regression(x_values, y_values)
        if not x_values:
            return []
        x_min, x_max = min(x_values), max(x_values)
        # Two point line for rendering
        return [(x_min, slope * x_min + intercept), (x_max, slope * x_max + intercept)]

    def calculate_correlation(self, data: Dict[str, List[float]]) -> Dict[Tuple[str, str], float]:
        """Return simple Pearson correlations for each pair of variables in data.
        data: {variable_name: [values...]}
        This is a minimal implementation; for larger analysis consider numpy/pandas.
        """
        correlations = {}
        variables = list(data.keys())
        for i in range(len(variables)):
            for j in range(i+1, len(variables)):
                var_a, var_b = variables[i], variables[j]
                x_vals, y_vals = data[var_a], data[var_b]
                if len(x_vals) != len(y_vals):
                    continue
                mean_x = sum(x_vals) / len(x_vals)
                mean_y = sum(y_vals) / len(y_vals)
                num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
                den_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_vals))
                den_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_vals))
                denom = den_x * den_y
                if math.isclose(denom, 0):
                    corr = 0.0
                else:
                    corr = num / denom
                correlations[(var_a, var_b)] = corr
        return correlations

    def detect_outliers(self, values: List[float], method: str = 'iqr') -> List[int]:
        """Detect outliers using specified method.
        
        Args:
            values: Input data
            method: 'iqr' (Interquartile Range) or 'zscore' (Z-score)
            
        Returns:
            List of indices where outliers are detected
        """
        if len(values) < 4:
            return []
        
        outlier_indices = []
        
        if method == 'iqr':
            # Interquartile Range method
            sorted_values = sorted(values)
            n = len(sorted_values)
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            q1 = sorted_values[q1_idx]
            q3 = sorted_values[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    outlier_indices.append(i)
                    
        elif method == 'zscore':
            # Z-score method (values beyond 2 standard deviations)
            mean_val = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            if std_dev > 0:
                for i, value in enumerate(values):
                    z_score = abs((value - mean_val) / std_dev)
                    if z_score > 2:  # 2 standard deviations
                        outlier_indices.append(i)
        
        return outlier_indices 

    def calculate_box_plot_stats(self, data: List[Tuple], y_variable: Tuple[str, str]) -> Optional[BoxPlotStats]:
        """Calculate comprehensive box plot statistics for a Y variable.
        
        Args:
            data: Chart data as list of tuples where Y variable is at specific index
            y_variable: Tuple of (y_variable_name, y_variable_type)
            
        Returns:
            BoxPlotStats object or None if insufficient data
        """
        if not data or len(data) < 5:  # Need minimum 5 points for meaningful box plot
            return None
        
        y_var_name, y_var_type = y_variable
        
        # Extract Y values, assuming Y variable is at index 1 (after X variable)
        y_values = []
        for row in data:
            if len(row) >= 2:
                try:
                    y_val = float(row[1]) if row[1] is not None else None
                    if y_val is not None:
                        y_values.append(y_val)
                except (ValueError, TypeError):
                    continue
        
        if len(y_values) < 5:
            return None
        
        # Calculate quartiles using proper percentile method
        sorted_values = sorted(y_values)
        n = len(sorted_values)
        
        # Calculate quartiles using interpolation method
        def percentile(data, p):
            """Calculate percentile using linear interpolation"""
            if len(data) == 1:
                return data[0]
            
            index = (len(data) - 1) * p
            lower_index = int(index)
            upper_index = min(lower_index + 1, len(data) - 1)
            
            if lower_index == upper_index:
                return data[lower_index]
            
            # Linear interpolation
            weight = index - lower_index
            return data[lower_index] * (1 - weight) + data[upper_index] * weight
        
        q1 = percentile(sorted_values, 0.25)
        median = percentile(sorted_values, 0.50)  # Q2
        q3 = percentile(sorted_values, 0.75)
        iqr = q3 - q1
        
        # Calculate whisker bounds
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        
        # Find actual whisker values (closest values within bounds)
        lower_whisker = min(sorted_values)  # Default to min
        upper_whisker = max(sorted_values)  # Default to max
        
        # Find the actual whisker positions
        for value in sorted_values:
            if value >= lower_fence:
                lower_whisker = value
                break
        
        for value in reversed(sorted_values):
            if value <= upper_fence:
                upper_whisker = value
                break
        
        # Identify outliers
        outliers = [value for value in y_values if value < lower_fence or value > upper_fence]
        
        return BoxPlotStats(
            q1=q1,
            median=median,
            q3=q3,
            iqr=iqr,
            lower_whisker=lower_whisker,
            upper_whisker=upper_whisker,
            outliers=outliers,
            min_value=min(y_values),
            max_value=max(y_values),
            sample_size=len(y_values)
        ) 

    def calculate_correlation_matrix(self, data: Dict[str, List[float]], 
                                   correlation_type: str = 'pearson',
                                   min_periods: int = 10) -> CorrelationMatrix:
        """Calculate correlation matrix for multiple variables
        
        Args:
            data: Dictionary mapping variable names to value lists
            correlation_type: 'pearson' or 'spearman'
            min_periods: Minimum number of valid observations required
            
        Returns:
            CorrelationMatrix object with correlation matrix and metadata
        """
        import math
        from typing import List, Tuple
        
        # Validate input
        if len(data) < 2:
            raise ValueError("At least 2 variables required for correlation matrix")
        
        variables = list(data.keys())
        n_vars = len(variables)
        
        # Initialize matrices
        correlation_matrix = [[0.0 for _ in range(n_vars)] for _ in range(n_vars)]
        p_value_matrix = [[0.0 for _ in range(n_vars)] for _ in range(n_vars)]
        
        # Calculate pairwise correlations
        total_sample_size = 0
        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i == j:
                    # Perfect correlation with self
                    correlation_matrix[i][j] = 1.0
                    p_value_matrix[i][j] = 0.0
                elif i < j:
                    # Calculate correlation between var1 and var2
                    corr, p_val, n_obs = self._calculate_pairwise_correlation(
                        data[var1], data[var2], correlation_type, min_periods
                    )
                    correlation_matrix[i][j] = corr
                    correlation_matrix[j][i] = corr  # Symmetric matrix
                    p_value_matrix[i][j] = p_val
                    p_value_matrix[j][i] = p_val
                    total_sample_size = max(total_sample_size, n_obs)
        
        return CorrelationMatrix(
            matrix=correlation_matrix,
            labels=variables,
            correlation_type=correlation_type,
            sample_size=total_sample_size,
            p_values=p_value_matrix
        )
    
    def _calculate_pairwise_correlation(self, x_values: List[float], y_values: List[float],
                                      correlation_type: str, min_periods: int) -> Tuple[float, float, int]:
        """Calculate correlation between two variables with significance test"""
        import math
        
        # Align data (remove pairs where either value is None/NaN)
        aligned_pairs = []
        for x, y in zip(x_values, y_values):
            if (x is not None and y is not None and 
                not (isinstance(x, float) and math.isnan(x)) and
                not (isinstance(y, float) and math.isnan(y))):
                aligned_pairs.append((float(x), float(y)))
        
        n_obs = len(aligned_pairs)
        
        # Check minimum observations
        if n_obs < min_periods:
            return 0.0, 1.0, n_obs  # No correlation, p-value = 1
        
        if n_obs < 3:
            return 0.0, 1.0, n_obs  # Need at least 3 points
        
        # Extract aligned values
        x_aligned = [pair[0] for pair in aligned_pairs]
        y_aligned = [pair[1] for pair in aligned_pairs]
        
        # Calculate correlation
        if correlation_type.lower() == 'spearman':
            correlation = self._calculate_spearman_correlation(x_aligned, y_aligned)
        else:
            correlation = self._calculate_pearson_correlation(x_aligned, y_aligned)
        
        # Calculate p-value (simplified t-test)
        if abs(correlation) >= 0.999:
            p_value = 0.0  # Nearly perfect correlation
        else:
            # t-statistic for correlation
            t_stat = correlation * math.sqrt((n_obs - 2) / (1 - correlation**2))
            # Simplified p-value calculation (two-tailed)
            p_value = self._calculate_t_test_p_value(abs(t_stat), n_obs - 2)
        
        return correlation, p_value, n_obs
    
    def _calculate_pearson_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = len(x_values)
        if n == 0:
            return 0.0
        
        # Calculate means
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        # Calculate numerator and denominators
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
        sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
        
        # Avoid division by zero
        if sum_sq_x == 0 or sum_sq_y == 0:
            return 0.0
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        return numerator / denominator
    
    def _calculate_spearman_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate Spearman rank correlation coefficient"""
        n = len(x_values)
        if n == 0:
            return 0.0
        
        # Convert to ranks
        x_ranks = self._convert_to_ranks(x_values)
        y_ranks = self._convert_to_ranks(y_values)
        
        # Calculate Pearson correlation of ranks
        return self._calculate_pearson_correlation(x_ranks, y_ranks)
    
    def _convert_to_ranks(self, values: List[float]) -> List[float]:
        """Convert values to ranks (average rank for ties)"""
        # Create (value, original_index) pairs and sort by value
        indexed_values = [(val, i) for i, val in enumerate(values)]
        indexed_values.sort(key=lambda x: x[0])
        
        # Assign ranks
        ranks = [0.0] * len(values)
        i = 0
        while i < len(indexed_values):
            # Find end of tied group
            j = i
            while j < len(indexed_values) and indexed_values[j][0] == indexed_values[i][0]:
                j += 1
            
            # Calculate average rank for tied group (1-based ranking)
            avg_rank = (i + j + 1) / 2.0
            
            # Assign average rank to all tied values
            for k in range(i, j):
                original_index = indexed_values[k][1]
                ranks[original_index] = avg_rank
            
            i = j
        
        return ranks
    
    def _calculate_t_test_p_value(self, t_stat: float, degrees_freedom: int) -> float:
        """Simplified p-value calculation for t-test"""
        # This is a simplified approximation
        # For more accuracy, would need scipy.stats or similar
        import math
        
        if degrees_freedom <= 0:
            return 1.0
        
        # Simple approximation based on t-distribution properties
        if t_stat > 4.0:
            return 0.001  # Very significant
        elif t_stat > 3.0:
            return 0.01   # Significant
        elif t_stat > 2.0:
            return 0.05   # Marginally significant
        elif t_stat > 1.0:
            return 0.2    # Not significant
        else:
            return 0.5    # Not significant 