from dataclasses import dataclass

@dataclass
class FilterConfig:
    # HSV ranges
    hMin: int = 0
    sMin: int = 0
    vMin: int = 0

    hMax: int = 179
    sMax: int = 255
    vMax: int = 255

    # Gaussian blur
    gaussian: int = 1  # must be odd

    # Canny edges
    canny_low_threshold: int = 0
    canny_high_threshold: int = 0

    # Morph kernels
    kernelXY_d: int = 10
    kernelXY_e: int = 10

    # Morph iterations
    dilation_iterations: int = 1
    erosion_iterations: int = 1
