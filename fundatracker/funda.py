import requests, uuid, json, os, datetime, xxhash, time, random, argparse
import utils # local
from typing import Literal

# GLOBALS
user_agent = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.1234.47 Safari/537.36 Edg/103.0.1264.37",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36"
]

run_id = str(uuid.uuid4())
CONNECTION = None
neighbourhood_insights = {}

funda_schema = {
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
        "availability" : "VARCHAR(100)",
        "amenities" : "VARCHAR(1000)",
        "construction_date_range" : "VARCHAR(100)",
        "construction_period" : "VARCHAR(100)",
        "construction_type" : "VARCHAR(100)",
        "handover_date_range" : "VARCHAR(100)",
        "offering_type" : "VARCHAR(100)",
        "project" : "VARCHAR(100)",
        "sale_date_range" : "VARCHAR(100)",
        "selected_area" : "VARCHAR(100)",
        "description" : "VARCHAR",
        "description_tags" : "VARCHAR(1000)",
        "zoning" : "VARCHAR(100)",
        "surrounding" : "VARCHAR(1000)",
        "offering_type" : "VARCHAR(100)",
        "exterior_space_garden_size" : "VARCHAR(100)",
        "exterior_space_type" : "VARCHAR(100)",
        "exterior_space_garden_orientation" : "VARCHAR(100)",
        "garage_capacity" : "VARCHAR(100)",
        "garage_type" : "VARCHAR(100)",
        "object_type" : "VARCHAR(100)",
        "neighbourhood_inhabitants" : "INTEGER",
        "neighbourhood_avg_askingprice_m2" : "INTEGER",
        "neighbourhood_families_with_children_pct" : "REAL",
        "listing_nr_of_saves": "INTEGER",
        "listing_nr_of_views": "INTEGER",
        "search_query": "VARCHAR(500)",
        "_processing_time": "TIMESTAMP",
        "_run_id": "VARCHAR(100)"
    }


def get_authorization_key():
    # Funda seems to use a basic auth key (base64 encoded) for all anonymous requests
    return "Basic ZjVhMjQyZGIxZmUwOjM5ZDYxMjI3LWQ1YTgtNDIxMi04NDY4LWU1NWQ0MjhjMmM2Zg=="

def get_results(postal_code4: Literal[1000, 9999], km_radius: Literal[1,2,5,10,15,30,50,100,None]=1, publication_date: Literal["now-1d","now-3d", "now-5d", "now-10d", "now-30d", "no_preference"] ="no_preference" , offering_type: Literal["buy", "rent", "all"]="all", start_index: int=0, page_size: int=100):
    base_url = "https://listing-search-wonen-arc.funda.io/listings-wonen-searcher-alias-prod/_reactivesearch?preference=_local&filter_path=-responses.aggregations.results.grid.buckets.global_ids.hits.hits._source%2C-responses._shards%2C-responses.aggregations.results.doc_count%2C-responses.**._index%2C-responses.**._score%2C-responses.**.doc_count_error_upper_bound%2C-responses.**.sum_other_doc_count%2C-responses.**._source.address.identifiers"
    query = {
        "settings": {
            "recordAnalytics": False,
            "enableQueryRules": True,
            "emptyQuery": True,
            "suggestionAnalytics": False,
            "queryParams": {
            "preference": "_local",
            "filter_path": "-responses.aggregations.results.grid.buckets.global_ids.hits.hits._source,-responses._shards,-responses.aggregations.results.doc_count,-responses.**._index,-responses.**._score,-responses.**.doc_count_error_upper_bound,-responses.**.sum_other_doc_count,-responses.**._source.address.identifiers"
            }
        },
        "query": [
            {
            "id": "search_result",
            "type": "search",
            "dataField": [
                "availability"
            ],
            "execute": True,
            "react": {
                "and": [
                "selected_area",
                "offering_type",
                "sort",
                "price",
                "floor_area",
                "plot_area",
                "bedrooms",
                "rooms",
                "exterior_space_garden_size",
                "garage_capacity",
                "publication_date",
                "object_type",
                "availability",
                "construction_type",
                "construction_period",
                "surrounding",
                "garage_type",
                "exterior_space_type",
                "exterior_space_garden_orientation",
                "energy_label",
                "zoning",
                "amenities",
                "type",
                "nvm_open_house_day",
                "free_text_search",
                "agent_id",
                "map_results",
                "object_type",
                "object_type_house_orientation",
                "object_type_house",
                "object_type_apartment_orientation",
                "object_type_apartment",
                "object_type_parking",
                "object_type_parking_capacity",
                "search_result__internal"
                ]
            },
            "size": page_size,
            "from": start_index,
            "defaultQuery": {
                "track_total_hits": True,
                "timeout": "3s",
                "sort": [
                {
                    "publish_date" : "desc"
                },
                {
                    "placement_type": "asc"
                },
                {
                    "relevancy_sort_order": "desc"
                },
                {
                    "id.number": "desc"
                }
                ],
                "_source": {
                "includes": [
                   "availability",
                    "address",
                    "agent",
                    "available_media_types",
                    "placement_type",
                    "construction_date_range",
                    "energy_label",
                    "floor_area",
                    "floor_area_range",
                    "handover_date_range",
                    "id",
                    "name",
                    "number_of_bedrooms",
                    "number_of_rooms",
                    "object_detail_page_relative_url",
                    "offering_type",
                    "open_house_datetime_slot",
                    "plot_area",
                    "plot_area_range",
                    "price",
                    "project",
                    "publish_date",
                    "sale_date_range",
                    "status",
                    "type",
                    "object_type",
                    "selected_area",
                    "description",
                    "offering_type",
                    "exterior_space_garden_size",
                    "garage_capacity",
                    "garage_type",
                    "object_type",
                    "availability",
                    "construction_type",
                    "construction_period",
                    "surrounding",
                    "exterior_space_type",
                    "exterior_space_garden_orientation",
                    "zoning",
                    "amenities",
                    "map_results",
                    "object_type_house_orientation",
                    "object_type_house",
                    "object_type_apartment_orientation",
                    "object_type_apartment",
                    "object_type_parking",
                    "object_type_parking_capacity"
                ]
                }
            }
            },
            {
            "id": "selected_area",
            "type": "term",
            "dataField": [
                "reactive_component_field"
            ],
            "execute": True,
            "customQuery": {
                "id": "location-radius-query-v2",
                "params": {
                "searchField": "location",
                "geoIndex": "geo-wonen-alias-prod",
                "locationIdentifier": f"{postal_code4}-0",
                "radiusField": f"area_with_radius.{km_radius}"
                }
            }
            }
        ]
    }

    if publication_date != "no_preference":
        # One of now-1d, now-3d, now-5d, now-10d, now-30d, no_preference
        query["query"].append({
            "id": "publication_date",
            "type": "term",
            "dataField": [
                        "publish_date_utc"
                    ],
            "execute": False,
            "customQuery": {
                "id": "publish-date-query-v2",
                "params": {
                    "date_to": "now",
                    "date_from": publication_date
                }
            }
        })

    if offering_type != "all":
        # buy or rent
        query["query"].append({
            "id": "offering_type",
            "type": "term",
            "dataField": [
                "offering_type"
            ],
            "execute": False,
            "defaultQuery": {
                "timeout": "500ms"
            },
            "value": offering_type
            })

    headers = {
        'User-Agent': random.choice(user_agent),
        'Authorization': get_authorization_key()
        }
    
    res = requests.post(base_url, json=query, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Failed to get results from funda. Status code: {res.status_code}. Response: {res.text}")

    return res.json()

def get_listing_insights(listing_id):
    url = f"https://marketinsights.funda.io/v1/objectinsights/{listing_id}"

    headers = {
        'User-Agent': random.choice(user_agent),
        'Authorization': get_authorization_key()
        }
    
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()
    if res.status_code == 204:
        # No insights available
        return {}
    else:
        print(f"Failed to get listing insights for {listing_id}. Status code: {res.status_code}. Response: {res.text}")
        return {}
    
def get_neighbourhood_insights(city, neighbourhood):
    global neighbourhood_insights
    neighbourhood = neighbourhood.replace("/", "-").replace(" ", "-").replace("--", "-")
    neighbourhood_key = xxhash.xxh64(f"{city}-{neighbourhood}").hexdigest()
    if neighbourhood_key in neighbourhood_insights:
        return neighbourhood_insights[neighbourhood_key]
    
    url = f"https://marketinsights.funda.io/v2/LocalInsights/preview/{city}/{neighbourhood}"

    headers = {
        'User-Agent': random.choice(user_agent)
        }
    
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        neighbourhood_insights[neighbourhood_key] = res.json()
        return neighbourhood_insights[neighbourhood_key]
    if res.status_code == 204:
        # No insights available
        return {}
    else:
        print(f"Failed to get listing insights for {city} - {neighbourhood}. Status code: {res.status_code}. Response: {res.text}")
        return {}

def parse_funda_results(results_object):
    try:
        listings = results_object["search_result"]["hits"]["hits"]
    except Exception as e:
        raise Exception(f"Failed to parse results. Error: {e} — Got: {results_object}")
    
    print(f"Parsing {len(listings)} listings...")
    parsed_results = []
    for listing in listings:
        try:
            listing_details = listing["_source"]
            listing_parsed = {
                    "listing_id": listing["_id"],
                    "agent_id": listing_details.get("agent", [{}])[0].get("id", ""),
                    "agent_url": listing_details.get("agent", [{}])[0].get("relative_url", ""),
                    "agent_name": listing_details.get("agent", [{}])[0].get("name", ""),
                    "agent_association": listing_details.get("agent", [{}])[0].get("association", ""),
                    "address_country": listing_details["address"]["country"],
                    "address_province": listing_details["address"].get("province", ""),
                    "address_city": listing_details["address"].get("city",""),
                    "address_neighbourhood": listing_details["address"].get("neighbourhood",""),
                    "address_municipality": listing_details["address"].get("municipality",""),
                    "address_house_number": listing_details["address"].get("house_number",""),
                    "address_house_number_suffix": listing_details["address"].get("house_number_suffix",""),
                    "address_postal_code": listing_details["address"]["postal_code"],
                    "address_street_name": listing_details["address"].get("street_name",""),
                    "number_of_bedrooms": listing_details.get("number_of_bedrooms", None),
                    "number_of_rooms": listing_details.get("number_of_rooms", None),
                    "object_type": listing_details.get("object_type", None),
                    "energy_label": listing_details.get("energy_label", None),
                    "floor_area": listing_details.get("floor_area", [None])[0],     
                    "plot_area": listing_details.get("plot_area",[None])[0],
                    "publish_date": listing_details["publish_date"],
                    "url_path": listing_details["object_detail_page_relative_url"],
                    "status": listing_details.get("status",""),
                    "price": listing_details["price"].get("selling_price", [None])[0],
                    "price_type": listing_details["price"].get("selling_price_type", ""),
                    "price_condition": listing_details["price"].get("selling_price_condition", ""),
                    "placement_type": listing_details.get("placement_type", ""),
                    "availability" : listing_details.get("availability", ""),
                    "amenities" : ",".join(listing_details.get("amenities", [])),
                    "construction_date_range" : f'{listing_details.get("construction_date_range", {}).get("gte", "")}~{listing_details.get("construction_date_range", {}).get("lte", "")}',
                    "construction_period" : listing_details.get("construction_period", ""),
                    "construction_type" : listing_details.get("construction_type", ""),
                    "offering_type" : listing_details.get("offering_type", ""),
                    "project" : listing_details.get("project", {}).get("id", ""),
                    "publish_date" : listing_details.get("publish_date", ""),
                    "sale_date_range" : f'{listing_details.get("sale_date_range", {}).get("gte", "")}~{listing_details.get("sale_date_range", {}).get("lte", "")}',
                    "selected_area" : listing_details.get("selected_area", ""),
                    "description" : listing_details.get("description", {}).get("dutch", ""),
                    "description_tags" : listing_details.get("description", {}).get("tags", ""),
                    "zoning" : listing_details.get("zoning", ""),
                    "surrounding" : ",".join(listing_details.get("surrounding", [])),
                    "offering_type" : ",".join(listing_details.get("offering_type", [])),
                    "exterior_space_garden_size" : listing_details.get("exterior_space_garden_size", ""),
                    "exterior_space_type" : listing_details.get("exterior_space_type", ""),
                    "exterior_space_garden_orientation" : listing_details.get("exterior_space_garden_orientation", ""),
                    "garage_capacity" : listing_details.get("garage_capacity", ""),
                    "garage_type" : listing_details.get("garage_type", ""),
                    "object_type" : listing_details.get("object_type", "")
                }
            
            neightbourhood_insights = get_neighbourhood_insights(listing_parsed["address_city"], listing_parsed["address_neighbourhood"])
            listing_parsed["neighbourhood_inhabitants"] = neightbourhood_insights.get("inhabitants", None)
            listing_parsed["neighbourhood_avg_askingprice_m2"] = neightbourhood_insights.get("averageAskingPricePerM2", None)
            listing_parsed["neighbourhood_families_with_children_pct"] = neightbourhood_insights.get("familiesWithChildren", None)

            try:
                listing_insights = get_listing_insights(listing_parsed["listing_id"])
                listing_parsed["listing_nr_of_views"] = listing_insights["nrOfViews"]
                listing_parsed["listing_nr_of_saves"] = listing_insights["nrOfSaves"]
            except:
                pass

            
            parsed_results.append(listing_parsed)
        except Exception as e:
            print(f"Failed to parse listing. Error: {e} — {listing}")
            continue
        
    return parsed_results

def store_results(results, table, conn):
    cursor = conn.cursor()
    print(f"Storing {len(results)} results...")
    for result in results:
        try:
            data = {
                "id" : xxhash.xxh64("~~".join([str(x) for x in result.values()])).hexdigest(),
                **result,
                "_processing_time": str(datetime.datetime.now()),
                "_run_id": run_id,
            }

            query = f"""
                INSERT INTO {table}({", ".join(data.keys())})
                VALUES({", ".join(["%s"]*len(data.keys()))})
                ON CONFLICT (id) DO NOTHING
            """

            cursor.execute(query, tuple(data.values()))

        except Exception as e:
            print(f"Encountered error: {e}")
            print(f"Error storing results for {result['listing_id']} ({result}) \n\n {query}")


def cli():
    global CONNECTION
    CONNECTION = utils.get_database_connection(
        db_name="funda", 
        db_user=os.environ.get("USER"), 
        db_password=os.environ.get("PASSWORD"),
        db_host=os.environ.get("HOST")
    )

    utils.db_setup("funda", funda_schema, CONNECTION)

    parser = argparse.ArgumentParser()

    parser.add_argument("--postal_code", type=int, required=True)
    parser.add_argument("--km_radius", type=int, required=True)
    parser.add_argument("--publication_date", type=str, default="now-30d")

    args = parser.parse_args()

    print(f"Running with args: {args.__dict__}")

    results_processed = 0
    results_total = 1
    page_size = 100
    while results_processed < results_total:
        res = get_results(postal_code4=args.postal_code, km_radius=args.km_radius, publication_date=args.publication_date, start_index=results_processed, page_size=page_size)
        try:
            results_total = res["search_result"]["hits"]["total"]["value"]
        except:
            raise Exception(f"Failed to get results from funda. Got: {res}")

        if results_total == 0:
            print("No results returned.")
            return
        
        print(f"Processing results {results_processed} to {results_processed+100} of {results_total}...")
        
        parsed_results = [{
            **x,
            "search_query": f"{args.postal_code}~{args.km_radius}~{args.publication_date}"
            } for x in parse_funda_results(res) if x]

        store_results(parsed_results, "funda", CONNECTION)

        results_processed += 100

        time.sleep(5)