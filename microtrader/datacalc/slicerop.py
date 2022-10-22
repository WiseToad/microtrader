class SlicerOperator:

    def __init__(self, configs, slicer, params, streams):

    
    def calc(self):
        for s in slicer:
            if s:
                self._operator = CompoundOperator(configs, params, streams)