from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re

def clean_name(name):
    #remove [number] at the start of the name, e.g. "[2] " or "[10] "
    name = re.sub(r'^\[\d+\]\s*', '', name)
    #remove country code in parentheses with exactly 3 uppercase letters, e.g. "(IND)"
    name = re.sub(r'\([A-Z]{3}\)', '', name)
    name = name.strip()
    return name

start = time.time()

driver = webdriver.Chrome()
driver.get("https://squashref.app/live/scores/psa")

# wait for at least one tournament element to be visible
WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "tournament")))

tournament_divs = driver.find_elements(By.CLASS_NAME, "tournament")

for tournament in tournament_divs:
    data_id = tournament.get_attribute("data-id")

    if data_id == "0":
        continue

    name = tournament.find_element(By.CLASS_NAME, "tournament_name").text
    location = tournament.find_element(By.CLASS_NAME, "tournament_location").text
    dates = tournament.find_element(By.CLASS_NAME, "tournament_dates").text

    # Sanitize the tournament name for file usage
    tournament_filename_base = re.sub(r'\s+', '_', name)

    # Click the tournament and wait for the results to load
    tournament.click()
    time.sleep(0.05)

    results = {}
    for result in driver.find_elements(By.CLASS_NAME, "result"):
        if result.get_attribute("style") == "display: block;":
            result_round = result.find_element(By.XPATH, ".//div[contains(@class, 'result_round')]")
            if result_round.get_attribute("style") == "display: block;":
                round_text = result_round.find_element(By.XPATH, ".//span[contains(@class, 'result_round_text')]").text
                results[round_text] = []

            names_text = result.find_element(By.XPATH, ".//span[contains(@class, 'result_match_text')]").text
            scores = result.find_element(By.XPATH, ".//span[contains(@class, 'result_scores_text')]").text

            # Split "Name1 bt. Name2" into winner and loser
            if " bt. " in names_text:
                winner_name_raw, loser_name_raw = names_text.split(" bt. ")
            else:
                # If no "bt." found, skip this match
                continue

            # Clean the names
            winner_name = clean_name(winner_name_raw)
            loser_name = clean_name(loser_name_raw)

            # Extract data
            match_data = {
                "winner": winner_name,
                "loser": loser_name,
                "gamescore": scores.partition(":")[0].strip(),
                "points": scores.split(": ")[1].split(" (")[0].strip(),
                "time": scores.split("(")[1].split(")")[0].strip()
            }
            results[round_text].append(match_data)

    # For each round in this tournament, create a CSV file
    for round_name, match_list in results.items():
        round_filename = re.sub(r'\s+', '_', round_name)
        filename = f"{tournament_filename_base}_{round_filename}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["winner", "loser", "gamescore", "points", "time"])
            writer.writeheader()
            for match in match_list:
                writer.writerow(match)

    # Re-click the tournament to close it before moving on to the next one
    tournament.click()

driver.quit()

end = time.time()
print(f"Total time taken: {end - start}'s")
