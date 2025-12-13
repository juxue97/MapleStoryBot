from dataclasses import dataclass

@dataclass
class FilterConfig:
    h_min: int = 0
    h_max: int = 179 

    s_min: int = 0
    s_max: int = 255

    v_min: int = 0
    v_max: int = 255

    hsv_channel: int = 2

    brightness: int = 0
    contrast: int = 30

    gaussian: int = 3

    use_adaptive: bool = True
    thresh_min: int = 90

    kernel_size: int = 3
    dilation_iterations: int = 1
    erosion_iterations: int = 1
