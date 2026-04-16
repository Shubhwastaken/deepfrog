class DocumentParser:
    def extract_text(self, file_path: str) -> str:
        try:
            with open(file_path, "r", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def structure(self, text: str) -> dict:
        # Integrate LLM call here for production
        return {"raw_text": text, "fields": {}}
