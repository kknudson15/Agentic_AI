class DetectorAgent:
    def detect(self, event):
        if event["error"]:
            return True
        return False