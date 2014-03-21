class RunTemplate(object):
    
    def __init__(self, d):
        self.inputs = {}
        try:
            inputs_attributes = d['inputs_attributes']
            for a in inputs_attributes:
                name = a['name']
                if 'value' in a:
                    value = a['value']
                else:
                    value = None
                self.inputs[name] = value
        except KeyError:
            pass