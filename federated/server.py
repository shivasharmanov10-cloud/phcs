
import numpy as np

from federated.aggregation import aggregate_client_models


class FederatedServer:
    """
    Central federated-learning coordinator.

    The server receives model parameters from PHCs,
    performs weighted FedAvg aggregation, and distributes
    the resulting global model.

    The parameter vector contains:

        [feature_weights..., bias]
    """

    def __init__(self):

        self.global_parameters = None
        self.round_number = 0

    # ========================================================
    # INITIALIZE GLOBAL MODEL
    # ========================================================

    def initialize(self, feature_count):

        # feature weights + bias
        self.global_parameters = np.zeros(
            feature_count + 1,
            dtype=np.float64,
        )

        self.round_number = 0

    # ========================================================
    # AGGREGATION
    # ========================================================

    def aggregate(
        self,
        client_parameters,
        client_sizes,
    ):

        if not client_parameters:
            raise ValueError(
                "No client models received."
            )

        if len(client_parameters) != len(
            client_sizes
        ):
            raise ValueError(
                "Number of client models and "
                "client sample counts must match."
            )

        self.global_parameters = (
            aggregate_client_models(
                client_parameters,
                client_sizes,
            )
        )

        self.global_parameters = np.asarray(
            self.global_parameters,
            dtype=np.float64,
        )

        if not np.all(
            np.isfinite(
                self.global_parameters
            )
        ):
            raise RuntimeError(
                "FedAvg produced non-finite "
                "global parameters."
            )

        self.round_number += 1

        return self.global_parameters.copy()

    # ========================================================
    # DISTRIBUTE GLOBAL MODEL
    # ========================================================

    def distribute(self):

        if self.global_parameters is None:
            raise ValueError(
                "Global model has not been initialized."
            )

        return self.global_parameters.copy()

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        return {
            "round": self.round_number,

            "model_initialized": (
                self.global_parameters
                is not None
            ),

            "model_parameters": (
                len(
                    self.global_parameters
                )
                if self.global_parameters
                is not None
                else 0
            ),
        }


# ============================================================
# COMPLETE FEDERATED ROUND
# ============================================================

def run_federated_round(
    clients,
    server,
    epochs=100,
    learning_rate=0.01,
):
    """
    Execute one complete federated-learning round.

    1. Server distributes global parameters.
    2. Each PHC trains locally.
    3. PHCs return model parameters.
    4. Server performs weighted FedAvg.
    5. New global parameters are returned to PHCs.
    """

    if not clients:
        raise ValueError(
            "No federated clients available."
        )

    global_parameters = (
        server.distribute()
    )

    client_parameters = []
    client_sizes = []

    # --------------------------------------------------------
    # LOCAL PHC TRAINING
    # --------------------------------------------------------

    for client in clients:

        client.set_parameters(
            global_parameters
        )

        trained_parameters = (
            client.train(
                epochs=epochs,
                learning_rate=learning_rate,
            )
        )

        if not np.all(
            np.isfinite(
                trained_parameters
            )
        ):
            raise RuntimeError(
                f"{client.phc_id}: "
                "non-finite parameters."
            )

        client_parameters.append(
            trained_parameters
        )

        client_sizes.append(
            client.get_sample_count()
        )

    # --------------------------------------------------------
    # FEDAVG
    # --------------------------------------------------------

    new_global_parameters = (
        server.aggregate(
            client_parameters,
            client_sizes,
        )
    )

    # --------------------------------------------------------
    # DISTRIBUTE UPDATED MODEL
    # --------------------------------------------------------

    for client in clients:

        client.set_parameters(
            new_global_parameters
        )

    return new_global_parameters