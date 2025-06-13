from typing import List, Tuple, Dict, Optional

import math
import statistics

class StatisticalAnalysis:
    """Provide comprehensive statistical utilities for chart overlays & insights."""

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