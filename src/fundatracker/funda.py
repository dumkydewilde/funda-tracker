import datetime
import json
import logging
import time
import uuid
from functools import lru_cache
from typing import Literal

import requests
import xxhash

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"

run_id = str(uuid.uuid4())
neighbourhood_insights = {}


def get_authorization_key():
    # Funda seems to use a basic auth key (base64 encoded) for all anonymous requests
    return "Basic ZjVhMjQyZGIxZmUwOjM5ZDYxMjI3LWQ1YTgtNDIxMi04NDY4LWU1NWQ0MjhjMmM2Zg=="


def get_funda_schema():
    return {
        "id": "VARCHAR(100) PRIMARY KEY",
        "agent_id": "VARCHAR(100)",
        "agent_url": "VARCHAR(500)",
        "listing_id": "VARCHAR(100)",
        "agent_name": "VARCHAR(500)",
        "agent_association": "VARCHAR(500)",
        "address_country": "VARCHAR(100)",
        "address_province": "VARCHAR(100)",
        "address_city": "VARCHAR(100)",
        "address_neighbourhood": "VARCHAR(100)",
        "address_municipality": "VARCHAR(100)",
        "address_house_number": "VARCHAR(100)",
        "address_house_number_suffix": "VARCHAR(100)",
        "address_postal_code": "VARCHAR(100)",
        "address_street_name": "VARCHAR(500)",
        "number_of_bedrooms": "INTEGER",
        "number_of_rooms": "INTEGER",
        "object_type": "VARCHAR(100)",
        "energy_label": "VARCHAR(100)",
        "floor_area": "INTEGER",
        "plot_area": "INTEGER",
        "publish_date": "TIMESTAMP",
        "url_path": "VARCHAR(500)",
        "status": "VARCHAR(100)",
        "price": "INTEGER",
        "price_type": "VARCHAR(100)",
        "price_condition": "VARCHAR(100)",
        "placement_type": "VARCHAR(100)",
        "availability": "VARCHAR(100)",
        "amenities": "VARCHAR(1000)",
        "construction_date_range": "VARCHAR(100)",
        "construction_period": "VARCHAR(100)",
        "construction_type": "VARCHAR(100)",
        "handover_date_range": "VARCHAR(100)",
        "offering_type": "VARCHAR(100)",
        "project": "VARCHAR(100)",
        "sale_date_range": "VARCHAR(100)",
        "selected_area": "VARCHAR(100)",
        "description": "VARCHAR",
        "description_tags": "VARCHAR(1000)",
        "zoning": "VARCHAR(100)",
        "surrounding": "VARCHAR(1000)",
        "exterior_space_garden_size": "VARCHAR(100)",
        "exterior_space_type": "VARCHAR(100)",
        "exterior_space_garden_orientation": "VARCHAR(100)",
        "garage_capacity": "VARCHAR(100)",
        "garage_type": "VARCHAR(100)",
        "neighbourhood_inhabitants": "INTEGER",
        "neighbourhood_avg_askingprice_m2": "INTEGER",
        "neighbourhood_families_with_children_pct": "REAL",
        "listing_nr_of_saves": "INTEGER",
        "listing_nr_of_views": "INTEGER",
        "search_query": "VARCHAR(500)",
        "_processing_time": "TIMESTAMP",
        "_run_id": "VARCHAR(100)",
    }


def get_results(
    postal_code4: Literal[1000, 9999],
    km_radius: Literal[1, 2, 5, 10, 15, 30, 50, 100, None] = 1,
    publication_date: Literal[
        "now-1d", "now-3d", "now-5d", "now-10d", "now-30d", "no_preference"
    ] = "no_preference",
    offering_type: Literal["buy", "rent"] = "buy",
    start_index: int = 0,
    page_size: int = 100,
):
    """
    Get property listings from Funda API using the new endpoint format.

    Args:
        postal_code4: 4-digit postal code for location search
        km_radius: Search radius in kilometers
        publication_date: Filter by publication date
        offering_type: Type of offering (buy/rent/all)
        start_index: Starting index for pagination
        page_size: Number of results per page

    Returns:
        dict: API response containing property listings
    """
    base_url = "https://listing-search-wonen.funda.io/_msearch/template"

    # Map publication_date to new format
    publication_date_map = {
        "now-1d": {"1": True},
        "now-3d": {"3": True},
        "now-5d": {"5": True},
        "now-10d": {"10": True},
        "now-30d": {"30": True},
        "no_preference": {},
    }

    # Build query parameters for new API format
    query_params = {
        "collapse_projects": False,
        "radius_search": {
            "index": "geo-wonen-alias-prod",
            "id": f"{postal_code4}-0",
            "path": f"area_with_radius.{km_radius}"
            if km_radius
            else "area_with_radius.1",
        },
        "offering_type": offering_type,
        "project_phase": {},
        "publication_date": publication_date_map.get(publication_date, {}),
        "availability": ["available", "negotiations", "unavailable"],
        "free_text_search": "",
        "page": {"from": start_index},  # Remove size parameter to match sample
        "zoning": ["residential", "recreational"],
        "type": ["single", "group"],
        "sort": {"field": None, "order": None},
        "open_house": {},
    }

    # Create NDJSON request body (newline-delimited JSON)
    index_line = {"index": "listings-wonen-searcher-alias-prod"}
    query_line = {
        "id": "search_result_20250808",
        "params": query_params,
    }  # Format as NDJSON (each JSON object on a separate line)
    ndjson_body = json.dumps(index_line) + "\n" + json.dumps(query_line) + "\n"

    headers = {
        "accept": "application/x-ndjson",
        "content-type": "application/x-ndjson",
        "Referer": "https://www.funda.nl/",
        "User-Agent": USER_AGENT,
    }

    res = requests.post(base_url, data=ndjson_body, headers=headers)

    if res.status_code != 200:
        raise Exception(
            f"Failed to get results from funda. Status code: {res.status_code}. Response: {res.text}"
        )

    return res.json()


@lru_cache
def get_listing_insights(listing_id):
    url = f"https://marketinsights.funda.io/v1/objectinsights/{listing_id}"

    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": get_authorization_key(),
    }

    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()
    if res.status_code == 204:
        # No insights available
        return {}
    else:
        logging.error(
            f"Failed to get listing insights for {listing_id}. Status code: {res.status_code}. Response: {res.text}"
        )
        return {}


@lru_cache(maxsize=2400)
def get_neighbourhood_insights(city, neighbourhood):
    global neighbourhood_insights
    neighbourhood = neighbourhood.replace("/", "-").replace(" ", "-").replace("--", "-")
    neighbourhood_key = xxhash.xxh64(f"{city}-{neighbourhood}").hexdigest()
    if neighbourhood_key in neighbourhood_insights:
        return neighbourhood_insights[neighbourhood_key]

    url = f"https://marketinsights.funda.io/v2/LocalInsights/preview/{city}/{neighbourhood}"

    headers = {"User-Agent": USER_AGENT}

    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        neighbourhood_insights[neighbourhood_key] = res.json()
        return neighbourhood_insights[neighbourhood_key]
    if res.status_code == 204:
        # No insights available
        return {}
    else:
        logging.error(
            f"Failed to get listing insights for {city} - {neighbourhood}. Status code: {res.status_code}. Response: {res.text}"
        )
        return {}


def parse_funda_results(results_object, use_listing_insights=True):
    """
    Parse Funda API results from the new API format.

    Args:
        results_object: API response object
        use_listing_insights: Whether to fetch additional listing insights

    Returns:
        list: Parsed listing data
    """
    try:
        listings = results_object["responses"][0]["hits"]["hits"]
    except Exception as e:
        raise Exception(f"Failed to parse results. Error: {e} — Got: {results_object}")

    logging.debug(f"Parsing {len(listings)} listings...")
    parsed_results = []
    for listing in listings:
        try:
            listing_details = listing["_source"]
            listing_parsed = {
                "listing_id": listing["_id"],
                "agent_id": listing_details.get("agent", [{}])[0].get("id", ""),
                "agent_url": listing_details.get("agent", [{}])[0].get(
                    "relative_url", ""
                ),
                "agent_name": listing_details.get("agent", [{}])[0].get("name", ""),
                "agent_association": listing_details.get("agent", [{}])[0].get(
                    "association", ""
                ),
                "address_country": listing_details["address"]["country"],
                "address_province": listing_details["address"].get("province", ""),
                "address_city": listing_details["address"].get("city", ""),
                "address_neighbourhood": listing_details["address"].get(
                    "neighbourhood", ""
                ),
                "address_municipality": listing_details["address"].get(
                    "municipality", ""
                ),
                "address_house_number": listing_details["address"].get(
                    "house_number", ""
                ),
                "address_house_number_suffix": listing_details["address"].get(
                    "house_number_suffix", ""
                ),
                "address_postal_code": listing_details["address"]["postal_code"],
                "address_street_name": listing_details["address"].get(
                    "street_name", ""
                ),
                "number_of_bedrooms": listing_details.get("number_of_bedrooms", None),
                "number_of_rooms": listing_details.get("number_of_rooms", None),
                "object_type": listing_details.get("object_type", None),
                "energy_label": listing_details.get("energy_label", None),
                "floor_area": listing_details.get("floor_area", [None])[0],
                "plot_area": listing_details.get("plot_area", [None])[0],
                "publish_date": listing_details["publish_date"],
                "url_path": listing_details["object_detail_page_relative_url"],
                "status": listing_details.get("status", ""),
                "price": listing_details["price"].get("selling_price", [None])[0],
                "price_type": listing_details["price"].get("selling_price_type", ""),
                "price_condition": listing_details["price"].get(
                    "selling_price_condition", ""
                ),
                "placement_type": listing_details.get("placement_type", ""),
                "availability": listing_details.get("availability", ""),
                "amenities": ",".join(listing_details.get("amenities", [])),
                "construction_date_range": f"{listing_details.get('construction_date_range', {}).get('gte', '')}~{listing_details.get('construction_date_range', {}).get('lte', '')}",
                "construction_period": listing_details.get("construction_period", ""),
                "construction_type": listing_details.get("construction_type", ""),
                "offering_type": listing_details.get("offering_type", ""),
                "project": listing_details.get("project", {}).get("id", ""),
                "sale_date_range": f"{listing_details.get('sale_date_range', {}).get('gte', '')}~{listing_details.get('sale_date_range', {}).get('lte', '')}",
                "selected_area": listing_details.get("selected_area", ""),
                "description": listing_details.get("description", {}).get("dutch", ""),
                "description_tags": listing_details.get("description", {}).get(
                    "tags", ""
                ),
                "zoning": listing_details.get("zoning", ""),
                "surrounding": ",".join(listing_details.get("surrounding", [])),
                "exterior_space_garden_size": listing_details.get(
                    "exterior_space_garden_size", ""
                ),
                "exterior_space_type": listing_details.get("exterior_space_type", ""),
                "exterior_space_garden_orientation": listing_details.get(
                    "exterior_space_garden_orientation", ""
                ),
                "garage_capacity": listing_details.get("garage_capacity", ""),
                "garage_type": listing_details.get("garage_type", ""),
            }

            neightbourhood_insights = get_neighbourhood_insights(
                listing_parsed["address_city"], listing_parsed["address_neighbourhood"]
            )
            listing_parsed["neighbourhood_inhabitants"] = neightbourhood_insights.get(
                "inhabitants", None
            )
            listing_parsed["neighbourhood_avg_askingprice_m2"] = (
                neightbourhood_insights.get("averageAskingPricePerM2", None)
            )
            listing_parsed["neighbourhood_families_with_children_pct"] = (
                neightbourhood_insights.get("familiesWithChildren", None)
            )

            if use_listing_insights:
                try:
                    listing_insights = get_listing_insights(
                        listing_parsed["listing_id"]
                    )
                    listing_parsed["listing_nr_of_views"] = listing_insights[
                        "nrOfViews"
                    ]
                    listing_parsed["listing_nr_of_saves"] = listing_insights[
                        "nrOfSaves"
                    ]
                except Exception as e:
                    logging.debug(
                        f"Failed to get listing insights for {listing_parsed['listing_id']}: {e}"
                    )
                    pass

            parsed_results.append(listing_parsed)
        except Exception as e:
            print(f"Failed to parse listing. Error: {e} — {listing}")
            continue

    return parsed_results


def store_results(results, table, conn):
    cursor = conn.cursor()
    logging.debug(f"Storing {len(results)} results...")
    for result in results:
        try:
            data = {
                "id": xxhash.xxh64(
                    "~~".join([str(x) for x in result.values()])
                ).hexdigest(),
                **result,
                "_processing_time": str(datetime.datetime.now()),
                "_run_id": run_id,
            }

            query = f"""
                INSERT INTO {table}({", ".join(data.keys())})
                VALUES({", ".join(["%s"] * len(data.keys()))})
                ON CONFLICT (id) DO NOTHING
            """

            cursor.execute(query, tuple(data.values()))

        except Exception as e:
            logging.error(
                f"Error storing results for {result['listing_id']} ({result}) \n\n {query}"
            )
            logging.error(e)


def tracker(
    postal_code, km_radius, publication_date, connection, sleep_between_requests_sec=5
):
    results_processed = 0
    results_total = 1
    page_size = 100
    while results_processed < results_total:
        res = get_results(
            postal_code4=postal_code,
            km_radius=km_radius,
            publication_date=publication_date,
            start_index=results_processed,
            page_size=page_size,
        )

        try:
            results_total = res["responses"][0]["hits"]["total"]["value"]
            results_current_length = len(res["responses"][0]["hits"]["hits"])

        except Exception as e:
            raise Exception(
                f"Failed to get results from funda. Got: {res}\n\nError: {e}"
            )

        if results_total == 0:
            logging.info("No results returned.")
            return

        logging.info(
            f"Processing results {results_processed}-{results_processed + results_current_length}/{results_total}..."
        )

        parsed_results = [
            {**x, "search_query": f"{postal_code}~{km_radius}~{publication_date}"}
            for x in parse_funda_results(res)
            if x
        ]

        store_results(parsed_results, "funda", connection)

        results_processed += results_current_length

        time.sleep(sleep_between_requests_sec)

    return
