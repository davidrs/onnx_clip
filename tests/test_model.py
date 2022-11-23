import os

import numpy as np
import pytest
from PIL import Image

from onnx_clip import OnnxClip


def load_image_text(convert=True):
    """
    Load a test image and convert to 3-channel RBG instead of 4-channel RGBA.

    Returns:
        (test_image, test_text)
    """
    IMAGE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../onnx_clip/data/CLIP.png"
    )
    if convert:
        return Image.open(IMAGE_PATH).convert("RGB"), [
            "a photo of a man",
            "a photo of a woman",
        ]
    else:
        return Image.open(IMAGE_PATH), [
            "a photo of a man",
            "a photo of a woman",
        ]


def test_bad_image_input():
    """
    Test that a non-PIL input is bad for an image.
    """
    _, text = load_image_text()

    onnx_model = OnnxClip()
    with pytest.raises(TypeError):
        onnx_model.run("bad image input", text)

def test_bad_image_channels():
    """
    Test that a 4-channel image raises the appropriate error.
    """
    image, text = load_image_text(convert=False)

    onnx_model = OnnxClip()
    with pytest.raises(AttributeError):
        onnx_model.run(image, text)


def test_bad_text_input():
    """
    Test that a non-tokenized input text is bad for model.
    """
    image, _ = load_image_text()

    onnx_model = OnnxClip()
    with pytest.raises(TypeError):
        onnx_model.run(image, 123)


def test_softmax_values():
    """
    Test the softmax function works as expected.
    """
    onnx_model = OnnxClip()
    logits = np.array([[0, 10, -10]])
    assert sum(onnx_model.softmax(logits)) == 1


def test_model_runs():
    """
    Test full process.
    """
    image, text = load_image_text()

    onnx_model = OnnxClip()

    logits_per_image, logits_per_text = onnx_model.run(image, text)

    assert logits_per_image.shape == (1, 2)
    assert logits_per_text.shape == (2, 1)

    probas = onnx_model.softmax(logits_per_image)

    assert len(probas) == 2
