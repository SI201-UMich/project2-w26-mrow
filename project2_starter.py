# SI 201 HW4 (Library Checkout System)
# Your name:
# Your student id:
# Your email:
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# e.g.:
# Asked ChatGPT for hints on debugging and for suggestions on overall code structure
#
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
#
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    with open(html_path, "r") as file:
        soup = BeautifulSoup(file, "html.parser")

    results = []

    titles = soup.find_all(attrs={"data-testid": "listing-card-title"})

    for title in titles:
        title_text = title.get_text()
        node_id = title.get("id", "")

        if not title_text or not node_id.startswith("title_"):
            continue

        listing_id = node_id.replace("title_", "", 1)
        results.append((title_text, listing_id))

    return results
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    html_path = os.path.join("html_files", f"listing_{listing_id}.html")

    with open(html_path, "r") as file:
        soup = BeautifulSoup(file, "html.parser")

    text = soup.get_text("\n")
    lines = [" ".join(line.split()) for line in text.split("\n") if line.strip()]

    clean_text = "\n".join(lines)

    policy_match = re.search(r"Policy number:\s*\n?\s*([^\n]+)", clean_text)
    policy_number = policy_match.group(1).strip() if policy_match else ""
    if policy_number.lower() == "pending":
        policy_number = "Pending"
    elif policy_number.lower() == "exempt":
        policy_number = "Exempt"

    host_type = "Superhost" if re.search(r"Superhost", clean_text) else "regular"

    subtitle_match = re.search(r"([^\n]*hosted by[^\n]*)", clean_text)
    subtitle = subtitle_match.group(1) if subtitle_match else ""

    host_name = ""
    host_from_subtitle = re.search(r"hosted by\s*([^\n]+)", subtitle)
    if host_from_subtitle:
        host_name = host_from_subtitle.group(1).strip()
    else:
        host_line_match = re.search(r"Hosted by\s*([^\n]+)", clean_text)
        if host_line_match:
            host_name = host_line_match.group(1).strip()

    host_name = host_name.split("·")[0].strip()

    if re.search(r"Private", subtitle):
        room_type = "Private Room"
    elif re.search(r"Shared", subtitle):
        room_type = "Shared Room"
    else:
        room_type = "Entire Room"

    location_match = re.search(r"Location\s*\n\s*([0-5]\.[0-9])", clean_text)
    location_rating = float(location_match.group(1)) if location_match else 0.0

    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating,
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    results = load_listing_results(html_path)
    database = []

    for listing_title, listing_id in results:
        details = get_listing_details(listing_id)[listing_id]
        row = (
            listing_title,
            listing_id,
            details["policy_number"],
            details["host_type"],
            details["host_name"],
            details["room_type"],
            details["location_rating"],
        )
        database.append(row)

    return database
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """
    sorted_data = sorted(data, key=lambda row: row[6], reverse=True)

    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Listing Title",
                "Listing ID",
                "Policy Number",
                "Host Type",
                "Host Name",
                "Room Type",
                "Location Rating",
            ]
        )
        writer.writerows(sorted_data)


def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """
    totals = {}
    counts = {}

    for row in data:
        room_type = row[5]
        location_rating = row[6]

        if location_rating == 0.0:
            continue

        totals[room_type] = totals.get(room_type, 0.0) + location_rating
        counts[room_type] = counts.get(room_type, 0) + 1

    averages = {}
    for room_type in totals:
        averages[room_type] = totals[room_type] / counts[room_type]

    return averages


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")

        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)

    def test_load_listing_results(self):
        self.assertEqual(len(self.listings), 18)
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]
        details_list = [get_listing_details(listing_id) for listing_id in html_list]

        self.assertEqual(details_list[0]["467507"]["policy_number"], "STR-0005349")
        self.assertEqual(details_list[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(details_list[2]["1944564"]["room_type"], "Entire Room")
        self.assertEqual(details_list[2]["1944564"]["location_rating"], 4.9)

    def test_create_listing_database(self):
        for row in self.detailed_data:
            self.assertEqual(len(row), 7)

        self.assertEqual(
            self.detailed_data[-1],
            ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8),
        )

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        output_csv(self.detailed_data, out_path)

        rows = []
        with open(out_path, "r") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)

        self.assertEqual(
            rows[1],
            ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"],
        )

        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        avg_ratings = avg_location_rating_by_room_type(self.detailed_data)
        self.assertEqual(avg_ratings["Private Room"], 4.9)

    def test_validate_policy_numbers(self):
        # TODO: Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
        # TODO: Check that the list contains exactly "16204265" for this dataset.
        pass


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)
