import numpy as np

# Set global print options for NumPy arrays
np.set_printoptions(formatter={'float_kind': '{:.2f}'.format})


def get_error(obtained_nutrients, optimal_nutrients):
    """
    Per dimension, calculate the relative error between the obtained and optimal nutrients.
    The total error is the square root of all relative errors squared

    This total error function can be optimized to account for different weights on each nutrient,
    and also to penalize under- or over-estimation of nutrients differently.
    """

    relative_error = (obtained_nutrients - optimal_nutrients) / optimal_nutrients
    return np.sqrt(np.sum(relative_error ** 2))


def gradient_descent(A, optimal_nutrients, learning_rate=1e-6, max_iterations=100_000, tolerance=1e-5):
    num_foods, _ = A.shape
    weights = np.random.rand(num_foods)
    # previous_cost = float('inf')

    for iteration in range(max_iterations):
        obtained_nutrients = A.T @ weights
        cost = get_error(obtained_nutrients, optimal_nutrients)

        # if abs(previous_cost - cost) < tolerance:
        if abs(cost) < tolerance:
            print(f"Converged after {iteration:,} iterations")
            break
        # previous_cost = cost

        error = obtained_nutrients - optimal_nutrients
        gradient = 2 * A @ error / num_foods
        # print(f'Iteration {iteration}')
        # print(f'{cost=:.2f}')
        # print(f'{weights=}')
        # print(f'{obtained_nutrients=}')
        # print(f'{optimal_nutrients=}')
        # print(f'{error=}')
        # print(f'{gradient=}')
        weights -= learning_rate * gradient
        weights = np.clip(weights, 0, None)

    return weights


if __name__ == '__main__':
    use_real_example = True

    if use_real_example:
        # Real food example: nutrients in 100g of food. The three columns represent vitamin A, vitamin C, and energy in kCal
        A = np.array([
            [53.2, 0.9, 49],  # Orange
            [0, 31, 165],  # Chicken Breast
            [89.2, 2.8, 34],  # Broccoli
            [0, 21, 579],  # Almonds
            [0, 20, 208],  # Salmon
            [0, 2.7, 130],  # Rice
            [28.1, 2.9, 23],  # Spinach
            [0, 0, 387],  # Sugar
        ])
        optimal_nutrients = np.array([80, 80, 2000])  # Vitamin A in mg, Vitamin C in mg, Calories in kcal
    else:
        # Simple numerical example: converges within 1000 iterations
        A = np.array([
            [2, 1, 1],
            [1, 2, 1],
            [1, 1, 2]
        ])
        optimal_nutrients = np.array([4, 4, 5])

    # Run gradient descent
    learning_rate = 1e-5 if use_real_example else 1e-2
    weights = gradient_descent(A, optimal_nutrients, learning_rate=learning_rate)
    print(f'Optimal weights: {(100*weights).astype(int)}')
    print(f'Obtained nutrients: {(A.T @ weights).astype(int)}')
    print(f'Optimal nutrients: {optimal_nutrients}')
