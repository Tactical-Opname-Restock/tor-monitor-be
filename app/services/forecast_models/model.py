"""XGBoost model creation and training utilities."""

from typing import Union

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error as mae
from xgboost import XGBRegressor


def create_model(
    n_estimators: int = 100,
    lr: float = 0.1,
) -> XGBRegressor:
    """Create configured XGBoost regression model.

    Model hyperparameters are tuned for demand forecasting:
    - High max_depth for capturing non-linear patterns
    - Low learning rate for stability
    - Specific subsample and colsample for regularization

    Args:
        n_estimators: Number of boosting rounds (default 100)
        lr: Learning rate / eta parameter (default 0.1)

    Returns:
        Configured XGBRegressor instance
    """
    xgb = XGBRegressor(
        n_estimators=n_estimators,
        learning_rate=lr,
        max_depth=50,
        gamma=0,
        colsample_bytree=1,
        subsample=0.37,
        alpha=0,
        reg_lambda=0.79,
        min_child_weight=1.32,
    )
    return xgb


def get_model_mae(
    model: XGBRegressor,
    X_train: Union[np.ndarray, pd.DataFrame],
    y_train: Union[np.ndarray, pd.Series],
) -> int:
    """Train model and calculate mean absolute error on test split.

    Uses last 7 days as test set for evaluation.

    Args:
        model: Unfitted XGBoost model
        X_train: Feature matrix (numpy array or pandas DataFrame)
        y_train: Target vector (numpy array or pandas Series)

    Returns:
        Mean absolute error (rounded to int)
    """
    model.fit(X_train[:-7], y_train[:-7])
    preds = model.predict(X_train[-7:])
    model_mae = mae(y_train[-7:], preds)
    return int(round(model_mae))
