"""Email everyone who hasn't logged progress yet this week.

Run manually:
    cd backend && python -m scripts.weekly_nudge

Runs automatically every Monday via .github/workflows/weekly-nudge.yml (also
triggerable on demand from the Actions tab - "Run workflow").

Requires SUPABASE_URL, SUPABASE_SERVICE_KEY, and RESEND_API_KEY. FRONTEND_URL
and REMINDER_FROM_EMAIL are optional (see app/services/nudge.py for defaults).
"""

import json

from dotenv import load_dotenv

load_dotenv()

from app.services.nudge import run  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
