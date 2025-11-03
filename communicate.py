from lib.gost_subscribe import gost_subscribe


class gost_subcribe_term(gost_subscribe):
    def __init__(self):
        super().__init__()

    def stream_out(self, text: str):
        yield text
    def text_out(self, text: str):
        self.stream_out(text)
        
