import sys, time, json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://YOUR-IP").rstrip("/")
HOLD_SECONDS = 20          # browser aakhir me itni der khula rahega (process screenshot ke liye)

UNIQUE = "selenium-" + str(int(time.time()))   # har run ka apna unique task
EDITED = UNIQUE + "-edited"

def task_row(driver, text):
    rows = driver.find_elements(By.XPATH, f"//ul[@id='notes']/li[contains(., '{text}')]")
    return rows[0] if rows else None

driver = webdriver.Chrome()
try:
    # Test 1: heading verify
    driver.get(URL)
    title = driver.find_element(By.ID, "title").text
    assert title == "Daily Task Manager", f"Unexpected heading: {title}"
    print("PASS 1: heading verified ->", title)

    # Test 2: task add (priority High + due date) aur list me verify
    driver.find_element(By.ID, "note-input").send_keys(UNIQUE)
    Select(driver.find_element(By.NAME, "priority")).select_by_visible_text("High")
    date_box = driver.find_element(By.NAME, "due_date")
    driver.execute_script("arguments[0].value = '2030-12-31';", date_box)
    driver.find_element(By.ID, "add-btn").click()
    row = task_row(driver, UNIQUE)
    assert row is not None, "Task not found after adding"
    assert "High" in row.text, "Priority High not shown"
    assert "31 Dec 2030" in row.text, "Due date not shown"
    print("PASS 2: task added with priority and due date")

    # Test 3: search
    driver.get(f"{URL}/?q={UNIQUE}")
    items = driver.find_elements(By.CSS_SELECTOR, "#notes li")
    assert len(items) >= 1 and all(UNIQUE in li.text for li in items), "Search results wrong"
    driver.get(f"{URL}/?q=no-such-task-xyz")
    assert len(driver.find_elements(By.CSS_SELECTOR, "#notes li")) == 0, "Search should be empty"
    print("PASS 3: search filter works")

    # Test 4: task ko done mark karna
    driver.get(URL)
    task_row(driver, UNIQUE).find_element(By.CSS_SELECTOR, ".check").click()
    badge = task_row(driver, UNIQUE).find_element(By.CSS_SELECTOR, ".badge").text
    assert badge == "COMPLETED", f"Expected COMPLETED, got {badge}"
    print("PASS 4: task marked completed")

    # Test 5: task edit
    task_row(driver, UNIQUE).find_element(By.CSS_SELECTOR, ".edit").click()
    box = driver.find_element(By.NAME, "text")
    box.clear()
    box.send_keys(EDITED)
    driver.find_element(By.TAG_NAME, "button").click()
    assert task_row(driver, EDITED) is not None, "Edited task not found"
    print("PASS 5: task edited")

    # Test 6: /api/tasks JSON
    driver.get(URL + "/api/tasks")
    data = json.loads(driver.find_element(By.TAG_NAME, "body").text)
    assert any(t["text"] == EDITED for t in data), "Task missing in API"
    print("PASS 6: /api/tasks returns task as JSON")

    # Test 7: task delete
    driver.get(URL)
    task_row(driver, EDITED).find_element(By.CSS_SELECTOR, ".del").click()
    assert task_row(driver, EDITED) is None, "Task still present after delete"
    print("PASS 7: task deleted")

    # Test 8: /health (Load Balancer isi ko check karta hai)
    driver.get(URL + "/health")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert body.strip() == "OK", f"Health check failed: {body}"
    print("PASS 8: /health endpoint returned OK")

    print(f"ALL TESTS PASSED. Browser {HOLD_SECONDS} second khula rahega...")
    time.sleep(HOLD_SECONDS)
finally:
    driver.quit()