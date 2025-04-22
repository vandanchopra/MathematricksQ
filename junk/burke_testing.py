import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import time

def generate_equity_curve(
    num_points: int = 252,  # 1 year of trading days
    drawdown_depths: List[float] = None,
    drawdown_durations: List[int] = None,
    final_return: float = None,
    noise_level: float = 0.002  # Daily volatility
) -> np.ndarray:
    """
    Generate a random equity curve with specified drawdowns and final return.
    
    Args:
        num_points: Number of points in the curve (default: 252 trading days)
        drawdown_depths: List of drawdown depths to use
        drawdown_durations: List of drawdown durations in days
        final_return: Target final return for the curve
        noise_level: Standard deviation of daily returns for random noise
    """
    if drawdown_depths is None:
        num_drawdowns = np.random.randint(3, 8)
        drawdown_depths = [np.random.uniform(0.05, 0.15) for _ in range(num_drawdowns)]
    
    if drawdown_durations is None:
        drawdown_durations = [np.random.randint(10, 40) for _ in range(len(drawdown_depths))]
        
    if final_return is None:
        final_return = np.random.uniform(0.10, 0.30)  # 10% to 30% annual return
    
    # Initialize curve with base upward trend to achieve final return
    x = np.linspace(0, 1, num_points)
    base_curve = np.exp(x * np.log(1 + final_return))
    
    # Add random drawdowns
    for depth, duration in zip(drawdown_depths, drawdown_durations):
        # Random drawdown location
        start = np.random.randint(0, num_points - duration)
        end = min(start + duration, num_points)
        
        # Create drawdown effect
        drawdown = np.linspace(0, -depth, end - start)
        recovery = np.linspace(-depth, 0, end - start)
        effect = np.concatenate([drawdown[:len(drawdown)//2], recovery[len(recovery)//2:]])
        
        # Apply drawdown
        base_curve[start:end] *= (1 + effect[:end-start])
    
    # Add random noise
    daily_noise = np.random.normal(0, noise_level, num_points)
    noisy_curve = base_curve * np.exp(np.cumsum(daily_noise))
    
    # Rescale to maintain target final return
    final_scale = (1 + final_return) / noisy_curve[-1]
    noisy_curve *= final_scale
    
    return noisy_curve

def calculate_burke_ratio(equity_curve: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Burke Ratio for an equity curve.
    Burke Ratio = (R_p - R_f) / sqrt(sum(drawdowns^2))
    where R_p is portfolio return, R_f is risk-free rate
    """
    print("\nBurke Ratio Calculation Steps:")
    print("-------------------------------")
    
    # Step 1: Calculate running peaks and drawdowns
    peak = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - peak) / peak
    print(f"Step 1: Initial and final equity values:")
    print(f"  Initial value: {equity_curve[0]:.4f}")
    print(f"  Final value: {equity_curve[-1]:.4f}")
    print(f"  Peak value reached: {np.max(peak):.4f}")
    print(f"  Worst drawdown: {np.min(drawdowns):.4f}")
    
    # Step 2: Find local maxima in peaks to identify drawdown periods
    max_drawdowns = []
    current_peak = equity_curve[0]
    current_min = equity_curve[0]
    
    for i in range(1, len(equity_curve)):
        if equity_curve[i] > current_peak:
            # New peak found
            if current_min < current_peak:
                # Record drawdown if there was one
                drawdown = (current_min - current_peak) / current_peak
                max_drawdowns.append(abs(drawdown))
            current_peak = equity_curve[i]
            current_min = equity_curve[i]
        elif equity_curve[i] < current_min:
            # New minimum in current drawdown
            current_min = equity_curve[i]
    
    # Check for final drawdown
    if current_min < current_peak:
        drawdown = (current_min - current_peak) / current_peak
        max_drawdowns.append(abs(drawdown))
    
    print("\nStep 2: Maximum drawdowns found:")
    print(f"  Number of drawdowns: {len(max_drawdowns)}")
    if max_drawdowns:
        print(f"  Drawdown depths: {[f'{dd:.4f}' for dd in max_drawdowns]}")
        print(f"  Sum of squared drawdowns: {sum([dd**2 for dd in max_drawdowns]):.4f}")
    else:
        print("  No drawdowns found")
        max_drawdowns = [abs(np.min(drawdowns))]  # Use worst drawdown if no local maxima found
        print(f"  Using worst drawdown: {max_drawdowns[0]:.4f}")
    
    # Step 3: Calculate Burke Ratio components
    total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
    denominator = np.sqrt(sum([dd**2 for dd in max_drawdowns]))
    
    print("\nStep 3: Burke Ratio Components:")
    print(f"  Total return (Rp): {total_return:.4f}")
    print(f"  Risk-free rate (Rf): {risk_free_rate:.4f}")
    print(f"  Excess return (Rp - Rf): {(total_return - risk_free_rate):.4f}")
    print(f"  Denominator (sqrt(sum(drawdowns^2))): {denominator:.4f}")
    
    # Step 4: Calculate final Burke ratio
    burke_ratio = (total_return - risk_free_rate) / denominator if denominator != 0 else 0
    print("\nStep 4: Final Burke Ratio:")
    print(f"  Burke Ratio = {burke_ratio:.4f}")
    print("-------------------------------")
    
    return burke_ratio

def main():
    # Generate and set random seed
    seed = np.random.randint(0, 10000000)
    np.random.seed(seed)
    print(f"Random seed: {seed}")
    print()
    
    # Generate curves with different parameters
    curves = []
    burke_ratios = []
    
    for i in range(2):
        # Random parameters for each curve
        num_dd = np.random.randint(2, 8)
        min_dd = np.random.uniform(0.05, 0.10)
        max_dd = np.random.uniform(0.15, 0.25)
        drawdown_depths = [np.random.uniform(min_dd, max_dd) for _ in range(num_dd)]
        
        # Random drawdown durations
        min_duration = 10
        max_duration = 40
        drawdown_durations = [np.random.randint(min_duration, max_duration) for _ in range(num_dd)]
        
        final_ret = np.random.uniform(-0.30, 0.30)  # Random final return
        noise = np.random.uniform(0.001, 0.003)  # Random noise level for each curve
        
        print(f"Generating curve {i+1} with params:")
        print(f"  num_drawdowns: {num_dd}")
        print(f"  min_max_dd: ({min_dd:.2f}, {max_dd:.2f})")
        print(f"  drawdown_depths: {[f'{d:.2f}' for d in drawdown_depths]}")
        print(f"  drawdown_durations: {drawdown_durations}")
        print(f"  sum of drawdowns: {sum(drawdown_depths):.2f}")
        print(f"  final_ret: {final_ret:.2f}")
        print(f"  noise: {noise:.4f}")  # Using 4 decimal places for noise
        
        # Generate curve
        curve = generate_equity_curve(
            drawdown_depths=drawdown_depths,
            drawdown_durations=drawdown_durations,
            final_return=final_ret,
            noise_level=noise
        )
        curves.append(curve)
        
        # Calculate Burke ratio
        burke_ratio = calculate_burke_ratio(curve)
        burke_ratios.append(burke_ratio)
        print()
    
    # Plot curves
    plt.figure(figsize=(12, 8))
    colors = ['blue', 'red', 'green']
    
    for i, (curve, ratio, color) in enumerate(zip(curves, burke_ratios, colors)):
        plt.plot(curve, label=f'Curve {i+1} (Burke: {ratio:.2f})', color=color)
    
    plt.title(f'Equity Curves with Burke Ratios (Seed: {seed})')
    plt.xlabel('Trading Days')
    plt.ylabel('Equity Value')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()