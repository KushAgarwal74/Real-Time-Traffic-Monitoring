import torch


def get_device():

    # ----------------------------------
    # NVIDIA GPU
    # ----------------------------------

    if torch.cuda.is_available():

        print("Using device: CUDA")

        return "cuda"

    # ----------------------------------
    # Apple Silicon GPU
    # ----------------------------------

    if torch.backends.mps.is_available():

        print("Using device: MPS")

        return "mps"

    # ----------------------------------
    # CPU fallback
    # ----------------------------------

    print("Using device: CPU")

    return "cpu"