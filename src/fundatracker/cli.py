import argparse
import os

from . import utils
from .funda import get_funda_schema, tracker

CONNECTION = None


def cli():
    print("🔌 Connecting to database...")
    global CONNECTION
    CONNECTION = utils.get_database_connection(
        db_name="funda",
        db_user=os.environ.get("USER"),
        db_password=os.environ.get("PASSWORD"),
        db_host=os.environ.get("HOST"),
    )

    utils.db_setup("funda", get_funda_schema(), CONNECTION)

    parser = argparse.ArgumentParser()

    parser.add_argument("--postal_code", type=int, required=True)
    parser.add_argument("--km_radius", type=int, required=True)
    parser.add_argument("--publication_date", type=str, default="now-30d")

    args = parser.parse_args()

    print(f"🏃 Running with args: {args.__dict__}")

    tracker(
        args.postal_code, args.km_radius, args.publication_date, connection=CONNECTION
    )
    print("🏁 Finished")
