import os
import sys
import unittest
from unittest.mock import Mock, patch

from fundatracker import funda
from tests.fixtures import (
    EMPTY_RESPONSE,
    MINIMAL_RESPONSE,
    SAMPLE_RESPONSE,
)

# Add the src directory to the path to import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestFundaFunctions(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""

        self.sample_response = SAMPLE_RESPONSE
        self.minimal_response = MINIMAL_RESPONSE
        self.empty_response = EMPTY_RESPONSE

        funda.get_listing_insights.cache_clear()

    def test_get_funda_schema(self):
        """Test that get_funda_schema returns expected schema structure."""
        schema = funda.get_funda_schema()

        # Test that it returns a dictionary
        self.assertIsInstance(schema, dict)

        # Test some key fields exist
        expected_fields = [
            "id",
            "agent_id",
            "listing_id",
            "address_country",
            "address_city",
            "price",
            "number_of_bedrooms",
            "number_of_rooms",
        ]

        for field in expected_fields:
            self.assertIn(field, schema)

        # Test that id field is primary key
        self.assertIn("PRIMARY KEY", schema["id"])

        # Test that integer fields are defined correctly
        self.assertEqual(schema["number_of_bedrooms"], "INTEGER")
        self.assertEqual(schema["price"], "INTEGER")

    @patch("fundatracker.funda.requests.post")
    @patch("fundatracker.funda.USER_AGENT", "Mozilla/5.0 Test Agent")
    def test_get_results_success(self, mock_post):
        """Test get_results function with successful response."""

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_response
        mock_post.return_value = mock_response

        result = funda.get_results(postal_code4=1000, km_radius=5)

        # Check that requests.post was called
        mock_post.assert_called_once()

        # Check the result
        self.assertEqual(result, self.sample_response)

        # Check headers were set correctly for new API
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        self.assertIn("User-Agent", headers)
        self.assertIn("accept", headers)
        self.assertIn("content-type", headers)
        self.assertIn("Referer", headers)
        self.assertEqual(headers["User-Agent"], "Mozilla/5.0 Test Agent")
        self.assertEqual(headers["accept"], "application/x-ndjson")
        self.assertEqual(headers["content-type"], "application/x-ndjson")
        self.assertEqual(headers["Referer"], "https://www.funda.nl/")

    @patch("fundatracker.funda.requests.post")
    def test_get_results_failure(self, mock_post):
        """Test get_results function with failed response."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as context:
            funda.get_results(postal_code4=1000, km_radius=5)

        self.assertIn("Failed to get results from funda", str(context.exception))
        self.assertIn("400", str(context.exception))

    @patch("fundatracker.funda.requests.post")
    def test_get_results_parameters(self, mock_post):
        """Test get_results function parameter validation and query building."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_response
        mock_post.return_value = mock_response

        # Test with different parameters
        funda.get_results(
            postal_code4=1000,
            km_radius=15,
            publication_date="now-3d",
            offering_type="buy",
            start_index=50,
        )

        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check that the request uses NDJSON format (data instead of json)
        self.assertIn("data", call_args[1])
        request_body = call_args[1]["data"]

        # Parse the NDJSON format (two lines)
        lines = request_body.strip().split("\n")
        self.assertEqual(len(lines), 2)

        import json

        index_line = json.loads(lines[0])
        query_line = json.loads(lines[1])

        # Check index specification
        self.assertEqual(index_line["index"], "listings-wonen-searcher-alias-prod")

        # Check query parameters
        params = query_line["params"]
        self.assertEqual(params["radius_search"]["path"], "area_with_radius.15")
        self.assertEqual(params["radius_search"]["id"], "1000-0")
        self.assertEqual(params["offering_type"], "buy")
        self.assertEqual(params["publication_date"], {"3": True})
        self.assertEqual(params["page"]["from"], 50)

    @patch("fundatracker.funda.get_neighbourhood_insights")
    def test_parse_funda_results(self, mock_neighbourhood_insights):
        """Test parse_funda_results with the new API format."""
        # Mock neighbourhood insights
        mock_neighbourhood_insights.return_value = {
            "inhabitants": 50000,
            "averageAskingPricePerM2": 8500,
            "familiesWithChildren": 0.35,
        }

        result = funda.parse_funda_results(
            self.sample_response, use_listing_insights=False
        )

        # Check that we got results
        self.assertEqual(len(result), 1)

        # Check key fields in parsed result
        parsed_listing = result[0]
        self.assertEqual(parsed_listing["listing_id"], "6965113")
        self.assertEqual(parsed_listing["agent_id"], 24581)
        self.assertEqual(parsed_listing["agent_name"], "Tel Krop Makelaars")
        self.assertEqual(parsed_listing["address_city"], "Amsterdam")
        self.assertEqual(parsed_listing["address_neighbourhood"], "Landlust")
        self.assertEqual(parsed_listing["price"], 375000)
        self.assertEqual(parsed_listing["number_of_bedrooms"], 2)
        self.assertEqual(parsed_listing["number_of_rooms"], 3)
        self.assertEqual(parsed_listing["object_type"], "apartment")
        self.assertEqual(parsed_listing["energy_label"], "D")
        self.assertEqual(parsed_listing["floor_area"], 51)
        self.assertEqual(parsed_listing["plot_area"], 0)

        # Check neighbourhood insights were added
        self.assertEqual(parsed_listing["neighbourhood_inhabitants"], 50000)
        self.assertEqual(parsed_listing["neighbourhood_avg_askingprice_m2"], 8500)
        self.assertEqual(
            parsed_listing["neighbourhood_families_with_children_pct"], 0.35
        )

        # Check key fields in parsed result
        parsed_listing = result[0]
        self.assertEqual(parsed_listing["listing_id"], "6965113")
        self.assertEqual(parsed_listing["agent_id"], 24581)
        self.assertEqual(parsed_listing["agent_name"], "Tel Krop Makelaars")
        self.assertEqual(parsed_listing["address_city"], "Amsterdam")
        self.assertEqual(parsed_listing["address_neighbourhood"], "Landlust")
        self.assertEqual(parsed_listing["price"], 375000)
        self.assertEqual(parsed_listing["number_of_bedrooms"], 2)
        self.assertEqual(parsed_listing["number_of_rooms"], 3)
        self.assertEqual(parsed_listing["object_type"], "apartment")
        self.assertEqual(parsed_listing["energy_label"], "D")
        self.assertEqual(parsed_listing["floor_area"], 51)
        self.assertEqual(parsed_listing["plot_area"], 0)

        # Check neighbourhood insights were added
        self.assertEqual(parsed_listing["neighbourhood_inhabitants"], 50000)
        self.assertEqual(parsed_listing["neighbourhood_avg_askingprice_m2"], 8500)
        self.assertEqual(
            parsed_listing["neighbourhood_families_with_children_pct"], 0.35
        )

    def test_parse_funda_results_invalid_format(self):
        """Test parse_funda_results with invalid data format."""
        invalid_data = {"invalid": "structure"}

        with self.assertRaises(Exception) as context:
            funda.parse_funda_results(invalid_data)

        self.assertIn("Failed to parse results", str(context.exception))

    @patch("fundatracker.funda.requests.get")
    def test_get_listing_insights_success(self, mock_get):
        """Test get_listing_insights with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nrOfViews": 150, "nrOfSaves": 25}
        mock_get.return_value = mock_response

        result = funda.get_listing_insights("12345")

        self.assertEqual(result["nrOfViews"], 150)
        self.assertEqual(result["nrOfSaves"], 25)
        mock_get.assert_called_once()

        # Check URL construction
        call_args = mock_get.call_args
        expected_url = "https://marketinsights.funda.io/v1/objectinsights/12345"
        self.assertEqual(call_args[0][0], expected_url)

    @patch("fundatracker.funda.requests.get")
    def test_get_listing_insights_no_content(self, mock_get):
        """Test get_listing_insights with 204 response."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_get.return_value = mock_response

        result = funda.get_listing_insights("12345")

        self.assertEqual(result, {})

    @patch("fundatracker.funda.requests.get")
    def test_get_listing_insights_error(self, mock_get):
        """Test get_listing_insights with error response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result = funda.get_listing_insights("12345")

        # Should return empty dict on error
        self.assertEqual(result, {})

    @patch("fundatracker.funda.requests.get")
    @patch("fundatracker.funda.xxhash.xxh64")
    def test_get_neighbourhood_insights_success(self, mock_xxhash, mock_get):
        """Test get_neighbourhood_insights with successful response."""
        # Mock hash function
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_xxhash.return_value = mock_hash

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "inhabitants": 50000,
            "averageAskingPricePerM2": 8500,
            "familiesWithChildren": 0.35,
        }
        mock_get.return_value = mock_response

        result = funda.get_neighbourhood_insights("Amsterdam", "Landlust")

        self.assertEqual(result["inhabitants"], 50000)
        self.assertEqual(result["averageAskingPricePerM2"], 8500)
        mock_get.assert_called_once()

        # Check URL construction
        call_args = mock_get.call_args
        expected_url = "https://marketinsights.funda.io/v2/LocalInsights/preview/Amsterdam/Landlust"
        self.assertEqual(call_args[0][0], expected_url)

    @patch("fundatracker.funda.get_neighbourhood_insights")
    def test_parse_funda_results_missing_optional_fields(self, mock_insights):
        """Test parse_funda_results handles missing optional fields gracefully."""
        mock_insights.return_value = {}

        result = funda.parse_funda_results(
            self.minimal_response, use_listing_insights=False
        )

        # Should still parse without errors
        self.assertEqual(len(result), 1)
        parsed = result[0]
        self.assertEqual(parsed["listing_id"], "test123")
        self.assertEqual(parsed["address_country"], "NL")
        self.assertEqual(parsed["url_path"], "/test/path/")

        # Check that missing fields are handled gracefully
        self.assertIsNone(parsed["price"])
        self.assertEqual(parsed["agent_name"], "")
        self.assertIsNone(parsed["floor_area"])

    @patch("fundatracker.funda.get_neighbourhood_insights")
    @patch("fundatracker.funda.get_listing_insights")
    def test_parse_funda_results_with_listing_insights(
        self, mock_listing_insights, mock_neighbourhood_insights
    ):
        """Test parse_funda_results with listing insights enabled."""
        # Mock insights
        mock_neighbourhood_insights.return_value = {"inhabitants": 50000}
        mock_listing_insights.return_value = {"nrOfViews": 100, "nrOfSaves": 20}

        result = funda.parse_funda_results(
            self.sample_response, use_listing_insights=True
        )

        # Check that listing insights were fetched and added
        parsed_listing = result[0]
        self.assertEqual(parsed_listing["listing_nr_of_views"], 100)
        self.assertEqual(parsed_listing["listing_nr_of_saves"], 20)

        # Verify the insights function was called with correct ID
        mock_listing_insights.assert_called_once_with("6965113")

    def test_parse_funda_results_edge_cases(self):
        """Test parse_funda_results with edge cases and unusual data structures."""
        with patch("fundatracker.funda.get_neighbourhood_insights") as mock_insights:
            mock_insights.return_value = {}
            result = funda.parse_funda_results(
                self.empty_response, use_listing_insights=False
            )
            self.assertEqual(len(result), 0)

    @patch("fundatracker.funda.get_neighbourhood_insights")
    def test_parse_funda_results_complex_fields(self, mock_insights):
        """Test parsing of complex fields like amenities, surrounding, etc."""
        mock_insights.return_value = {}

        result = funda.parse_funda_results(
            self.sample_response, use_listing_insights=False
        )
        parsed = result[0]

        # Check complex field parsing
        self.assertEqual(parsed["amenities"], "balcony,garden")
        self.assertEqual(parsed["surrounding"], "park,school")
        self.assertEqual(parsed["construction_date_range"], "1980~1990")
        self.assertEqual(parsed["description"], "Mooie woning")


if __name__ == "__main__":
    # Run tests with more verbose output
    unittest.main(verbosity=2)
