import errno
import os
from typing import List, Tuple, Union

import numpy as np
import onnxruntime as ort
from PIL import Image

from onnx_clip import Preprocessor, Tokenizer


class OnnxClip:
    """
    This class can be utilised to predict the most relevant text snippet, given an image,
    without directly optimizing for the task, similarly to the zero-shot capabilities of GPT-2 and 3.
    The difference between this class and [CLIP](https://github.com/openai/CLIP) is that here we do not use any
    PyTorch dependencies.
    """

    def __init__(self):
        """
        Instantiates the model and required encoding classes.
        """
        self.model = self._load_model()
        self._tokenizer = Tokenizer()
        self._preprocessor = Preprocessor()

    def _load_model(self):
        """
        Grabs the ONNX model. This is the same model that can be found in CLIP:
        https://github.com/openai/CLIP/blob/main/clip/model.py

        We have exported it to ONNX to remove the PyTorch dependencies.
        """
        MODEL_ONNX_EXPORT_PATH = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data/clip_model.onnx"
        )
        if os.path.exists(MODEL_ONNX_EXPORT_PATH):
            return ort.InferenceSession(MODEL_ONNX_EXPORT_PATH)
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), MODEL_ONNX_EXPORT_PATH
            )

    def run(
        self, image: Image.Image, text: Union[str, List[str]]
    ) -> Tuple[np.array, np.array]:
        """
        Given a batch of PIL images and a batch of text, returns two arrays, containing the logit scores corresponding
        to each image and text input.
        The values are cosine similarities between the corresponding image and text features, times 100.

        The images and text are encoded in a similar manner to the `preprocess` and `tokenize` functions within CLIP,
        after which they are passed to the ONNX version of the CLIP model.

        Example usage:
            image = Image.open("lakera_clip/data/CLIP.png").convert("RGB")
            text = ["a photo of a man", "a photo of a woman"]
            onnx_model = OnnxClip()
            logits_per_image, logits_per_text = onnx_model.run(image, text)
            probas = lakera_model.softmax(logits_per_image)
            print(logits_per_image, probas)
            [20.380428 19.790262], [0.64340323 0.35659674]

        Args:
            image: the original PIL image. This image must be a 3-channel (RGB) image.
                   Can be any size, as the preprocessing step is done to convert this image to size (224, 224).
            text: the text to tokenize. Each category in the given list cannot be longer than 77 characters.

        Returns:
            (logits_per_image, logits_per_text) tuple.
        """
        image = self._preprocessor.encode_image(image)
        text = self._tokenizer.encode_text(text)

        logits_per_image, logits_per_text = self.model.run(
            None, {"IMAGE": image, "TEXT": text}
        )
        return logits_per_image, logits_per_text

    def softmax(self, x: np.array) -> np.array:
        """
        Computes softmax values for each sets of scores in x.
        This ensures the output sums to 1.
        """
        return (np.exp(x) / np.sum(np.exp(x), axis=1))[0]
