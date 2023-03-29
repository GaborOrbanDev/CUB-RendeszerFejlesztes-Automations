from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import concurrent.futures as cf
import re
import nlp_rake
import random
import pandas as pd
import creds


def scrape_item(url):
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument(f'--proxy-server={creds.proxy_connection}')

    try:
        rake = nlp_rake.Rake()

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) #, chrome_options=chrome_options)

        driver.get(url)
        print("loaded")
        sku = SKU + "_" + re.search(r"productpage\..*?\.", url).group()[len("productpage."):-1]
        title = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.TAG_NAME, "h1")).text
        price_str = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, ".primary-row.product-item-price")).text
        price_regex = re.search(r"[0-9].*?Ft",
                        price_str
                    ).group()
        price = int(price_regex[:-3].replace(" ", ""))
        description = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, ".ProductDescription-module--descriptionText__rKCVH.BodyText-module--preamble__VwE7e")).text
        img = driver.find_element(By.CSS_SELECTOR, ".product-detail-main-image-container img").get_attribute("src")

        driver.quit()
        
        try:
            keywords = rake.apply(title + " " + description)[:10]
            keywords = ", ".join([i[0] for i in keywords])
        except:
            keywords = ""

        result = {
                "SLUG": None,
                'Active': "Yes",
                "Featured": None,
                "SKU": sku,
                "Name": title,
                "Product Type": "Generic" if PRODUCT_TYPE == "" else PRODUCT_TYPE,
                "MSRP": None,
                "Cost": None,
                "Price": price,
                "Manufacture": None,
                "Vendor": None,
                "Image": img,
                "Description": description,
                "Search Keywords": keywords,
                "Meta Description": None,
                "Meta Keywords": None,
                "Tax Schedule": None,
                "Tax Excempt": None,
                "Weight": None,	
                "Length": None,	
                "Width": None,	
                "Height": None,
                "Extra Ship Fee": None,	
                "Ship Mode": None,	
                "Non-Shipping Product": None,	
                "Ships in a Separate Box": None,
                "Allow Rewies": "Yes", 	
                "Minimum Qty": 0,	
                "Inventory Mode": None,	
                "Inventory": random.randint(10, 200),	
                "Stock Out at": 0,	
                "Low Stock at": 5,
                "Roles": None,	
                "Searchable": True
            }
        
        return result
    except:
        driver.quit()
        return None

def collect_urls(url):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get(url)
    lis = WebDriverWait(driver, 10).until(lambda d: d.find_elements(By.CSS_SELECTOR, "li.product-item"))
    urls = []
    for li in lis:
        try:
            u = li.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
            urls.append(u)
        except:
            pass
    driver.quit()   
    return urls

URL = "https://www2.hm.com/hu_hu/noi/vasarlas-termek-szerint/felsok.html?sort=stock&productTypes=P%C3%B3l%C3%B3&image-size=small&image=model&offset=0&page-size=50"
SKU = "shirt_t_women"
PRODUCT_TYPE = ""
WORKERS = 6

if __name__ == "__main__":
    linkek = collect_urls(URL)

    with cf.ProcessPoolExecutor(max_workers=WORKERS) as exec:
        r = exec.map(scrape_item, linkek)

    db = list(r)
    db = list(filter(lambda i: i is not None, db))
    df = pd.DataFrame(db)
    df.drop_duplicates(subset="Name", keep="first", inplace=True)
    df.to_excel(SKU+".xlsx", "Main", index=False)
    print(df)