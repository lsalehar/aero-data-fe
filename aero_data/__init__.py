import decouple as dc
import supabase as sb

from aero_data.models import Countries

db_url: str = dc.config("SUPABASE_URL")  # type: ignore
db_key: str = dc.config("SUPABASE_KEY")  # type: ignore
db_client: sb.Client = sb.Client(db_url, db_key)  # type: ignore
countries: Countries = Countries().populate_data(
    db_client.table("countries").select("*").execute()
)
