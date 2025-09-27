class RecoveryAgent:
    MAX_RETRIES = 1  # simulate retry once for transient errors

    def apply_fix(self, event, retry_count=0):
        error = event.get("error")
        if not error:
            return "No fix needed", retry_count

        fix = "Manual intervention required"

        if "Missing file" in error:
            fix = "Reloaded missing file"
        elif "Schema mismatch" in error:
            fix = "Applied schema mapping"
        elif "Null values" in error:
            fix = "Filled nulls with default values"

        # Retry logic
        if retry_count < self.MAX_RETRIES and "Manual" not in fix:
            retry_count += 1

        return fix, retry_count