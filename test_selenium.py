import sys
from selenium import webdriver
from selenium.webdriver.common.by import By

URL = sys.argv[1] if len(sys.argv) > 1 else "http://YOUR-IP"

driver = webdriver.Chrome()
try:
    # Test 1: heading verify
    driver.get(URL)
    title = driver.find_element(By.ID, "title").text
    assert title == "Daily Task Manager", f"Unexpected heading: {title}"
    print("PASS 1: heading verified ->", title)

    # Test 2: task add karke verify
    driver.find_element(By.ID, "note-input").send_keys("selenium-test-task")
    driver.find_element(By.ID, "add-btn").click()
    items = [li.text for li in driver.find_elements(By.CSS_SELECTOR, "#notes li")]
    assert any("selenium-test-task" in i for i in items), "Task not found"
    print("PASS 2: task added and verified")

    # Test 3: /health endpoint verify (Load Balancer isi ko check karta hai)
    driver.get(URL.rstrip("/") + "/health")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert body.strip() == "OK", f"Health check failed: {body}"
    print("PASS 3: /health endpoint returned OK")
finally:
    driver.quit()