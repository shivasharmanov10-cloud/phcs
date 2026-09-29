
import numpy as np


class FederatedClient:
    """
    Represents one PHC participating in federated learning.

    The PHC keeps its training data locally.

    Only model parameters are sent to the federated server.

    Model:
        y = X @ weights + bias
    """

    def __init__(self, phc_id, X, y):

        self.phc_id = phc_id

        self.X = np.asarray(
            X,
            dtype=np.float64,
        )

        self.y = np.asarray(
            y,
            dtype=np.float64,
        )

        if self.X.ndim != 2:
            raise ValueError(
                f"{self.phc_id}: X must be 2-dimensional."
            )

        if self.y.ndim != 1:
            raise ValueError(
                f"{self.phc_id}: y must be 1-dimensional."
            )

        if len(self.X) != len(self.y):
            raise ValueError(
                f"{self.phc_id}: X and y have different lengths."
            )

        # One weight for every feature + one bias.
        self.weights = np.zeros(
            self.X.shape[1],
            dtype=np.float64,
        )

        self.bias = 0.0

    # ========================================================
    # LOCAL TRAINING
    # ========================================================

    def train(
        self,
        epochs=100,
        learning_rate=0.01,
    ):
        """
        Train the local demand model using gradient descent.

        The PHC's raw data never leaves this client.
        """

        if len(self.X) == 0:
            raise ValueError(
                f"{self.phc_id} has no training data."
            )

        n = len(self.X)

        for _ in range(epochs):

            # ------------------------------------------------
            # Prediction
            # ------------------------------------------------

            predictions = (
                self.X @ self.weights
                + self.bias
            )

            error = (
                predictions
                - self.y
            )

            # ------------------------------------------------
            # Gradients
            # ------------------------------------------------

            weight_gradient = (
                self.X.T @ error
            ) / n

            bias_gradient = (
                np.sum(error)
            ) / n

            # ------------------------------------------------
            # Gradient clipping for numerical stability
            # ------------------------------------------------

            weight_gradient = np.clip(
                weight_gradient,
                -10.0,
                10.0,
            )

            bias_gradient = float(
                np.clip(
                    bias_gradient,
                    -10.0,
                    10.0,
                )
            )

            # ------------------------------------------------
            # Update
            # ------------------------------------------------

            self.weights -= (
                learning_rate
                * weight_gradient
            )

            self.bias -= (
                learning_rate
                * bias_gradient
            )

        if not np.all(
            np.isfinite(
                self.weights
            )
        ):
            raise RuntimeError(
                f"{self.phc_id}: "
                "non-finite weights produced."
            )

        if not np.isfinite(
            self.bias
        ):
            raise RuntimeError(
                f"{self.phc_id}: "
                "non-finite bias produced."
            )

        return self.get_parameters()

    # ========================================================
    # PARAMETERS
    # ========================================================

    def get_parameters(self):
        """
        Return weights + bias as one parameter vector.
        """

        return np.concatenate(
            [
                self.weights,
                np.array(
                    [self.bias],
                    dtype=np.float64,
                ),
            ]
        )

    def set_parameters(
        self,
        parameters,
    ):
        """
        Load global weights + bias.
        """

        parameters = np.asarray(
            parameters,
            dtype=np.float64,
        )

        expected = (
            self.X.shape[1] + 1
        )

        if len(parameters) != expected:
            raise ValueError(
                f"{self.phc_id}: expected "
                f"{expected} parameters, "
                f"received {len(parameters)}."
            )

        self.weights = parameters[
            :-1
        ].copy()

        self.bias = float(
            parameters[-1]
        )

    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

    def get_weights(self):
        return self.get_parameters()

    def set_weights(self, weights):
        self.set_parameters(weights)

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(self, X=None):

        if X is None:
            X = self.X

        X = np.asarray(
            X,
            dtype=np.float64,
        )

        return (
            X @ self.weights
            + self.bias
        )

    # ========================================================
    # SAMPLE COUNT
    # ========================================================

    def get_sample_count(self):

        return len(self.X)