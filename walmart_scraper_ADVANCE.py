import requests
from bs4 import BeautifulSoup
import json
import queue

BASE_URL = "https://www.walmart.com"
OUTPUT_FILE = "product_info.jsonl"

# Headers para simular un navegador real
BASE_HEADERS = {
    "accept" : "*/*",
    "accept-encoding" : "gzip, deflate, br, zstd",
    "accept-language" : "es-ES,es;q=0.9",
    "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

#Lista de busqueda
search_queries = ["robot litter box", "smart litter box", "automatic litter box", "self cleaning litter box", "automatic cat litter box", "self cleaning cat litter box", "smart cat litter box"]

# Se inicia la cola para los productos y un set para las URLs ya vistas
product_queue = queue.Queue()
seen_urls = set()

def get_product_links_from_search_page(query, page_number):
    search_url = f"https://www.walmart.com/search?q={query}-&page={page_number}"
    response = requests.get(search_url, headers=BASE_HEADERS)
    soup = BeautifulSoup(response.text,"html.parser")
    product_links = []

    found = False
    for a_tag in soup.find_all('a', href=True):
        if "/ip/" in a_tag['href']:
            found = True
            if "https" in a_tag['href']:
                full_url = a_tag['href']
            else:
                full_url = BASE_URL + a_tag['href']
            
            if full_url not in seen_urls:
                product_links.append(full_url)
            
    if not found:
        print("\n\n\nSOUP WHERE NOT FOUND", soup)

    return product_links

def extract_product_info(product_url):
    print("Procesando URL:", product_url)
    response = requests.get(product_url, headers=BASE_HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find("script", id="__NEXT_DATA__")

    if script_tag is None:
        return None

    data = json.loads(script_tag.string)
    initial_data = data["props"]["pageProps"]["initialData"]["data"]
    product_data = initial_data["product"]
    reviews_data = initial_data.get("reviews", {})

    product_info = {
        "price": product_data["priceInfo"]["currentPrice"]["price"],
        "review_count": reviews_data.get("totalReviewCount", 0),
        "item_id": product_data["usItemId"],
        "avg_rating": reviews_data.get("averageOverallRating", 0),
        "product_name": product_data["name"],
        "brand": product_data.get("brand",""),
        "availability": product_data["availabilityStatus"],
        "image_url": product_data["imageInfo"]["thumbnailUrl"],
        "short_description": product_data.get("shortDescription","")
    }

    return product_info

def main():
    with open(OUTPUT_FILE, 'w') as file:
        while search_queries:
            current_query = search_queries.pop(0)
            print("\n\nCURRENT QUERY:", current_query, "\n\n")
            page_number = 1

            while True:
                product_links = get_product_links_from_search_page(current_query, page_number)
                if not product_links or page_number > 99:
                    break

                for link in product_links:
                    if link not in seen_urls:
                        product_queue.put(link)
                        seen_urls.add(link)

                while not product_queue.empty():
                    product_url = product_queue.get()
                    try:
                        product_info = extract_product_info(product_url)
                        if product_info:
                            file.write(json.dumps(product_info) + "\n")
                    except Exception as e:
                        print(f"Fallo procesando URL {product_url}. Error: {e}")
            
                page_number += 1
                print(f"Pagina de busqueda {page_number}.")


if __name__ == "__main__":
    main()