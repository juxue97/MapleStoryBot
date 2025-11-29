class Filter:

    def __init__(self,gaussian=None, canny_low_threshold=None, canny_high_threshold=None,
                 kernelXY_d=None, kernelXY_e=None,
                 dilation_iterations=None, erosion_iterations=None,
                 hMin=None, sMin=None, vMin=None, hMax=None, sMax=None, vMax=None):
        
        self.gaussian = gaussian

        self.canny_low_threshold = canny_low_threshold
        self.canny_high_threshold = canny_high_threshold

        self.kernelXY_d= kernelXY_d
        self.kernelXY_e = kernelXY_e

        self.dilation_iterations = dilation_iterations
        self.erosion_iterations = erosion_iterations

        self.hMin = hMin
        self.sMin = sMin
        self.vMin = vMin

        self.hMax = hMax
        self.sMax = sMax
        self.vMax = vMax
