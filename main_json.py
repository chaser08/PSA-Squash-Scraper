from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

start = time.time()

data = []  # list of dictionaries, each dict is a tournament

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
                
            names = result.find_element(By.XPATH, ".//span[contains(@class, 'result_match_text')]").text
            scores =  result.find_element(By.XPATH, ".//span[contains(@class, 'result_scores_text')]").text
            match_data = {
                "names": names,
                "gamescore": scores.partition(":")[0],
                "points": scores.split(": ")[1].split(" (")[0],
                "winner": names.partition(" bt.")[0],
                "time": scores.split("(")[1].split(")")[0]
            }
            results[round_text].append(match_data)

    data.append({
        "name": name,
        "location": location,
        "dates": dates,
        "results": results
    })
    
    # reclick the tournament to close it before moving on to the next one
    tournament.click()

driver.quit()

with open("data.json", "w", encoding="utf-8") as json_file:
    # Use ensure_ascii=False to preserve special characters correctly
    json.dump(data, json_file, indent=4, ensure_ascii=False)

end = time.time()
print(f"Total time taken: {end-start}'s")
