import decouple as dc
import supabase as sb

from aero_data.models import Countries

# Read configuration with safe defaults
db_url = dc.config("SUPABASE_URL", default=None)  # type: ignore
db_key = dc.config("SUPABASE_KEY", default=None)  # type: ignore

# Create client only when credentials are available
db_client = None
if db_url and db_key:
    try:
        db_client = sb.Client(db_url, db_key)  # type: ignore
    except Exception:
        db_client = None

# Load countries data if database is available; otherwise keep an empty container
countries: Countries
try:
    if db_client is not None:
        countries = Countries().populate_data(  # type: ignore
            db_client.table("countries").select("*").execute()
        )
    else:
        countries = Countries()
except Exception:
    countries = Countries()
