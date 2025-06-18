import sqlite3


class TemplateDatabase:
    def __init__(self, db_file="settings.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY,
                    pattern TEXT NOT NULL UNIQUE,
                    replacement TEXT NOT NULL
                )
            """)

    def add_default_templates(self):
        """Adds default regex templates if they don't already exist."""
        defaults = [
            # Remove duplicate artist names like "Artist - Artist - Track"
            (r"(.+?)\s*-\s*\1\s*-\s*", r"\1 - "),
            # Remove duplicate artist names with underscores like "Artist_-_Artist_-_Track"
            (r"(.+?)_+-+_+\1_+-+_+", r"\1 - "),
            # Remove redundant artist repetition in formats like "Artist_-_Artist_-_Track"
            (r"(.+?)\s*[-_]+\s*\1\s*[-_]+\s*", r"\1 - "),
            # Replace underscores with spaces
            (r"_+", " "),
            # Remove tags like [Official Video], (Official Audio), [Lyrics], etc.
            (r"\s*\[\s*official.*?video\s*\]", ""),
            (r"\s*\(\s*official.*?video\s*\)", ""),
            (r"\s*\[\s*official.*?audio\s*\]", ""),
            (r"\s*\(\s*official.*?audio\s*\)", ""),
            (r"\s*\[\s*lyrics?\s*\]", ""),
            (r"\s*\(\s*lyrics?\s*\)", ""),
            (r"\s*\[\s*live\s*\]", ""),
            (r"\s*\(\s*live\s*\)", ""),
            # Strip leading/trailing hyphens, underscores, or whitespace
            (r"^\s*[-_]+\s*", ""),
            (r"\s*[-_]+\s*$", ""),
        ]
        with self.conn:
            for pattern, replacement in defaults:
                try:
                    self.conn.execute(
                        "INSERT INTO templates (pattern, replacement) VALUES (?, ?)",
                        (pattern, replacement),
                    )
                except sqlite3.IntegrityError:
                    # Template already exists, this is fine
                    pass

    def get_all_templates(self):
        with self.conn:
            cursor = self.conn.execute("SELECT id, pattern, replacement FROM templates")
            return cursor.fetchall()

    def add_template(self, pattern, replacement):
        with self.conn:
            self.conn.execute(
                "INSERT INTO templates (pattern, replacement) VALUES (?, ?)",
                (pattern, replacement),
            )

    def delete_template(self, template_id):
        with self.conn:
            self.conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))

    def close(self):
        self.conn.close()
