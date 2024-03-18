import torch
from pathlib import Path
from typing import Union, Tuple

from boxmot.utils import WEIGHTS
from boxmot.utils import logger as LOGGER
from boxmot.appearance import export_formats
from boxmot.appearance.backends.onnx_backend import ONNXBackend
from boxmot.appearance.backends.openvino_backend import OpenVinoBackend
from boxmot.appearance.backends.pytorch_backend import PyTorchBackend
from boxmot.appearance.backends.tensorrt_backend import TensorRTBackend
from boxmot.appearance.backends.tflite_backend import TFLiteBackend
from boxmot.appearance.backends.torchscript_backend import TorchscriptBackend
from boxmot.appearance.backends.base_backend import BaseModelBackend


class ReidAutoBackend():
    def __init__(
        self,
        weights: Path = WEIGHTS / "osnet_x0_25_msmt17.pt",
        device: torch.device = torch.device("cpu"),
        half: bool = False) -> None:
        """
        Initializes the ReidAutoBackend instance with specified weights, device, and precision mode.

        Args:
            weights (Union[str, List[str]]): Path to the model weights. Can be a string or a list of strings; if a list, the first element is used.
            device (torch.device): The device to run the model on, e.g., CPU or GPU.
            half (bool): Whether to use half precision for model inference.
        """
        super().__init__()
        w = weights[0] if isinstance(weights, list) else weights
        
        self.framework = self.identify_framework(w)  # get backend
        self.weights = weights
        self.device = device
        self.half = half


    def get_backend(self) -> Union['PyTorchBackend', 'TorchscriptBackend', 'ONNXBackend', 'TensorRTBackend', 'OpenVinoBackend', 'TFLiteBackend']:
        """
        Returns an instance of the appropriate backend based on the model type.

        Returns:
            An instance of a backend class corresponding to the detected model type.
        
        Raises:
            SystemExit: If no supported model framework is detected.
        """

        # Mapping of conditions to backend constructors
        backend_map = [
            (self.pt, PyTorchBackend),
            (self.torchscript, TorchscriptBackend),
            (self.onnx, ONNXBackend),
            (self.tensorrt, TensorRTBackend),
            (self.openvino, OpenVinoBackend),
            (self.tflite, TFLiteBackend)
        ]

        # Iterate through the mapping and return the first matching backend
        for condition, backend_class in backend_map.items():
            if condition:
                return backend_class(self.weights, self.device, self.half)

        # If no condition is met, log an error and exit
        LOGGER.error("This model framework is not supported yet!")
        exit()


    def forward(self, im_batch: torch.Tensor) -> torch.Tensor:
        """
        Processes an image batch through the selected backend and returns the processed batch.

        Args:
            im_batch (torch.Tensor): The batch of images to process.

        Returns:
            torch.Tensor: The processed image batch.
        """
        im_batch = self.backend.preprocess_input(im_batch)
        return self.backend.get_features(im_batch)


    def check_suffix(self, file: Path = "osnet_x0_25_msmt17.pt", suffix: Union[str, Tuple[str, ...]] = (".pt",), msg: str = "") -> None:
        """
        Validates that the file or files have an acceptable suffix.

        Args:
            file (Union[str, List[str], Path]): The file or files to check.
            suffix (Union[str, Tuple[str, ...]]): Acceptable suffix or suffixes.
            msg (str): Additional message to log in case of an error.
        """

        suffix = [suffix] if isinstance(suffix, str) else list(suffix)
        files = [file] if isinstance(file, (str, Path)) else list(file)

        for f in files:
            file_suffix = Path(f).suffix.lower()
            if file_suffix and file_suffix not in suffix:
                LOGGER.error(f"File {f} does not have an acceptable suffix. Expected: {suffix}")


    def identify_framework(self, path: Path):
        # Extract the file extension
        file_extension = file_path.suffix.lower()  # lowercase for consistency

        # Initialize the dictionary with all values set to False
        framework_presence = {
            "pytorch": False,
            "tensorrt": False,
            "onnx": False,
            "torchscript": False,
            "openvino": False,
            "tflite": False
        }
        
        # Check the file extension and update the dictionary accordingly
        if file_extension in ['.pt', '.pth']:
            framework_presence["pytorch"] = True
        elif file_extension == '.onnx':
            framework_presence["onnx"] = True
        elif file_extension == '.torchscript':
            framework_presence["torchscript"] = True
        elif file_extension == '.xml':  # Assuming an OpenVINO model; further checks for .bin would be outside this function's scope
            framework_presence["openvino"] = True
        elif file_extension in ['.plan', '.engine']:
            framework_presence["tensorrt"] = True
        else:
            LOGGER.error("This model framework is not supported yet!")
            exit()
            
        for framework, is_present in framework_dict.items():
            if is_present:
                return framework
            else:
                LOGGER.error("Framework now found")
                exit()
        
