class ValidatorAgent:
    def validate(self, event, fix):
        if "Manual" in fix:
            return "Failed"
        else:
            return "Success"