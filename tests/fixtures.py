"""
Test fixtures for Funda API responses - both old and new formats
"""

# Sample response data for the new API structure
SAMPLE_RESPONSE = {
    "responses": [
        {
            "hits": {
                "total": {"value": 705, "relation": "eq"},
                "hits": [
                    {
                        "_id": "6965113",
                        "_source": {
                            "agent": [
                                {
                                    "logo_type": "new",
                                    "relative_url": "/makelaars/amsterdam/24581-tel-krop-makelaars/",
                                    "is_primary": True,
                                    "logo_id": 141966721,
                                    "name": "Tel Krop Makelaars",
                                    "association": "NVM",
                                    "id": 24581,
                                }
                            ],
                            "number_of_bedrooms": 2,
                            "address": {
                                "country": "NL",
                                "province": "Noord-Holland",
                                "city": "Amsterdam",
                                "neighbourhood": "Landlust",
                                "house_number_suffix": "-I",
                                "municipality": "Amsterdam",
                                "is_bag_address": True,
                                "house_number": "3",
                                "postal_code": "1055EP",
                                "street_name": "Baetostraat",
                            },
                            "object_type": "apartment",
                            "energy_label": "D",
                            "floor_area": [51],
                            "plot_area": [0],
                            "offering_type": ["buy"],
                            "price": {
                                "selling_price": [375000],
                                "selling_price_type": "regular",
                                "selling_price_condition": "kosten_koper",
                            },
                            "publish_date": "2023-11-27T15:50:30.3700000",
                            "object_detail_page_relative_url": "/koop/amsterdam/appartement-42310576-baetostraat-3-i/",
                            "status": "none",
                            "number_of_rooms": 3,
                            "placement_type": "premium",
                            "availability": "available",
                            "amenities": ["balcony", "garden"],
                            "construction_date_range": {"gte": 1980, "lte": 1990},
                            "construction_period": "1980-1990",
                            "construction_type": "resale",
                            "project": {"id": "project123"},
                            "sale_date_range": {
                                "gte": "2023-01-01",
                                "lte": "2023-12-31",
                            },
                            "selected_area": "Amsterdam",
                            "description": {
                                "dutch": "Mooie woning",
                                "tags": ["modern", "central"],
                            },
                            "zoning": "residential",
                            "surrounding": ["park", "school"],
                            "exterior_space_garden_size": "medium",
                            "exterior_space_type": "garden",
                            "exterior_space_garden_orientation": "south",
                            "garage_capacity": "1",
                            "garage_type": "carport",
                        },
                    }
                ],
            }
        }
    ]
}

# Minimal response for testing missing fields
MINIMAL_RESPONSE = {
    "responses": [
        {
            "hits": {
                "hits": [
                    {
                        "_id": "test123",
                        "_source": {
                            "address": {"country": "NL", "postal_code": "1000AA"},
                            "price": {},
                            "publish_date": "2023-01-01T00:00:00",
                            "object_detail_page_relative_url": "/test/path/",
                        },
                    }
                ]
            }
        }
    ]
}

# Empty response for edge case testing
EMPTY_RESPONSE = {"responses": [{"hits": {"hits": []}}]}

# Sample insights responses
SAMPLE_LISTING_INSIGHTS = {"nrOfViews": 150, "nrOfSaves": 25}

SAMPLE_NEIGHBOURHOOD_INSIGHTS = {
    "inhabitants": 50000,
    "averageAskingPricePerM2": 8500,
    "familiesWithChildren": 0.35,
}

# Expected parsed results for validation
EXPECTED_PARSED_OLD_FORMAT = {
    "listing_id": "6965113",
    "agent_id": 24581,
    "agent_name": "Tel Krop Makelaars",
    "agent_association": "NVM",
    "address_city": "Amsterdam",
    "address_neighbourhood": "Landlust",
    "address_country": "NL",
    "address_postal_code": "1055EP",
    "price": 375000,
    "number_of_bedrooms": 2,
    "number_of_rooms": 3,
    "object_type": "apartment",
    "energy_label": "D",
    "floor_area": 51,
    "plot_area": 0,
    "amenities": "balcony,garden",
    "surrounding": "park,school",
    "construction_date_range": "1980~1990",
    "description": "Mooie woning",
}

# Mock responses for external API calls
MOCK_RESPONSES = {
    "listing_insights_success": SAMPLE_LISTING_INSIGHTS,
    "neighbourhood_insights_success": SAMPLE_NEIGHBOURHOOD_INSIGHTS,
    "empty_insights": {},
}

# Test parameters for different scenarios
TEST_SCENARIOS = {
    "default_params": {
        "postal_code4": 1000,
        "km_radius": 5,
        "publication_date": "no_preference",
        "offering_type": "all",
    },
    "filtered_params": {
        "postal_code4": 1000,
        "km_radius": 15,
        "publication_date": "now-3d",
        "offering_type": "buy",
        "start_index": 50,
        "page_size": 25,
    },
}
