
import numpy as np


def fed_avg(client_weights, client_sizes):
    """
    Federated Averaging (FedAvg).

    client_weights:
        List of model parameter arrays from each PHC.

    client_sizes:
        Number of training samples used by each PHC.
    """

    if not client_weights:
        raise ValueError("No client weights provided.")

    if len(client_weights) != len(client_sizes):
        raise ValueError("client_weights and client_sizes must have the same length.")

    total_samples = sum(client_sizes)

    if total_samples == 0:
        raise ValueError("Total client samples cannot be zero.")

    aggregated = np.zeros_like(client_weights[0], dtype=float)

    for weights, size in zip(client_weights, client_sizes):
        weight = size / total_samples
        aggregated += weights * weight

    return aggregated


def aggregate_client_models(client_models, client_sizes):
    """
    Aggregate multiple client model parameter vectors.
    """

    if len(client_models) == 0:
        raise ValueError("No client models received.")

    return fed_avg(client_models, client_sizes)