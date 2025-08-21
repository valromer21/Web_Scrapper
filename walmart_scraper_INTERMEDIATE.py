from bs4 import BeautifulSoup
import requests
import json

walmart_url = "https://www.walmart.com/ip/ADVTSPRS-Automatic-Self-Cleaning-Cat-Litter-Box-with-App-Control-Support-WiFi-Intelligent-Radar-Smart-Auto-Litter-Box-with-Liner-Blue/5122120300?classType=VARIANT&from=/search"

HEADERS = {
    "accept" : "*/*",
    "accept-encoding" : "gzip, deflate, br, zstd",
    "accept-language" : "es-ES,es;q=0.9",
    "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

def get_product_links(query, page_number=1):
    search_url = f"https://www.walmart.com/search?q={query}"

    response = requests.get(search_url, headers=HEADERS)

    soup = BeautifulSoup(response.text,"html.parser")

    links = soup.find_all('a', href=True)

    product_links = []

    #ciclo que revisa si el termino ip esta en el link
    for link in links:
        link_href = link['href']
        if "/ip/" in link_href:
            if "https" in link_href:
                full_url = link_href
            else:
                full_url = "https://www.walmart.com" + link_href
            
            product_links.append(full_url)

    return product_links

def extract_product_info(product_url):
    response = requests.get(product_url, headers=HEADERS)

    soup = BeautifulSoup(response.text, 'html.parser')

    script_tag = soup.find("script", id="__NEXT_DATA__")

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
    OUTPUT_FILE = "product_info.jsonl"

    with open(OUTPUT_FILE, 'w') as file:
        page_number = 1
        while True:
            links = get_product_links("robot litter box", page_number)
            if not links or page_number > 99:
                break

            for link in links:
                try:
                    product_info = extract_product_info(link)
                    if product_info:
                        file.write(json.dumps(product_info) + "\n")
                except Exception as e:
                    print(f"Fallo procesando URL {link}. Error: {e}")
            
            page_number += 1
            print(f"Pagina de busqueda {page_number}.")


if __name__ == "__main__":
    main()