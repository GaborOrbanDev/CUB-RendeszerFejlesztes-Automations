from dataclasses import dataclass, asdict
import asyncio
import httpx
from selectolax.parser import HTMLParser
import re
import pandas as pd
import random
import creds

SKU = "woman-shirts" #SKU kategória
URL = "https://www.carhartt-wip.com/en/women-shirts" #A scrapelni kívánt rovat url-je
EUR_HUF = 378.47 #Euró - Forint átváltási konstans

db = []

@dataclass
class Ruha:
    #active: str
    sku: str
    name: str
    price: int
    description: str
    img: str
    #allow_reviews: str
    inventory: int
    #searchable: bool
    #category: list


async def fetch_item(sem: asyncio.Semaphore, session: httpx.AsyncClient, url: str) -> None:
    try:
        response = await session.get(url)

        if response.status_code < 400:
            doc = HTMLParser(response.text)
            print(response.url)

            sku = SKU + re.sub("/|-|[a-z]", "", str(response.url)[-20:])
            title = doc.css_first("h1").text().strip()
            price = int(float(doc.css_first("span.price.country_eur").text().strip()) * EUR_HUF)
            description = doc.css_first(".inner.productDescription").text().strip()
            try:
                img = doc.css_first(".slides img").attributes['data-desktop']
            except:
                img = ""

            item = Ruha(
                #active="YES",
                sku=sku,
                name=title,
                price=price,
                description=description,
                img=img,
                #allow_reviews="YES",
                inventory=random.randint(10,100),
                #searchable=True
            )

            db.append(asdict(item))
        else:
            sem.release()

    except Exception as ex:
        print(ex)

async def fetch_with_sem(sem: asyncio.Semaphore, session: httpx.AsyncClient, url: str) -> None:
    async with sem:
        await fetch_item(sem, session, url)

async def collect_urls(session: httpx.AsyncClient, url: str) -> list[str]:
    response = await session.get(url)
    doc = HTMLParser(response.text)

    items = doc.css(".content article a")
    urls = ['https://www.carhartt-wip.com' + url.attributes["href"] for url in items]
    return urls

async def main():
    semaphore = asyncio.Semaphore(10)

    async with httpx.AsyncClient(proxies=creds.proxy_connection) as client:
        urls = await collect_urls(client, URL)
        tasks = [fetch_with_sem(semaphore, client, url) for url in urls]
        await asyncio.gather(*tasks)

    df = pd.DataFrame(db)
    #df.columns = ["Active", "SKU", "Name", "Price", "Description", "Image", "Allow Rewies", "Inventory", "Searchable"]
    df.columns = ["SKU", "Name", "Price", "Description", "Image", "Inventory"]
    df.drop_duplicates(subset="Name", keep="first", inplace=True)
    df.to_excel(SKU+".xlsx", "Main", index=False)
    print(df)

if __name__ == "__main__":
    asyncio.run(main())

