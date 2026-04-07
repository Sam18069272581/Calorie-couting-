import requests

def search_german_food(keyword: str):
    """
    通过 Open Food Facts API 搜索德国区食物数据
    """
    # 限制搜索区域为德国 (de)，并要求返回 JSON
    url = f"https://de.openfoodfacts.org/cgi/search.pl"

    headers = {
        "User-Agent": "MacroTracker - StudentProject - Version 1.0 (Bielefeld)"
    }

    params = {
        "search_terms": keyword,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10  # 每次只取前 5 个最相关的，避免数据爆炸
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if response.status_code != 200:
            return[]
        
        data = response.json()
        products = data.get("products", [])

        results = []
        for product in data.get("products", []):
            # 提取宏量营养素 (OFF 的单位默认是每 100g)
            nutriments = product.get("nutriments", {})
            
            # 过滤掉没有营养数据的无效条目
            if "proteins_100g" not in nutriments:
                continue
                
            results.append({
                "name": product.get("product_name_de") or product.get("product_name", "未知名称"),
                "brand": product.get("brands", ""),
                "protein_100g": float(nutriments.get("proteins_100g", 0)),
                "fat_100g": float(nutriments.get("fat_100g", 0)),
                "carbs_100g": float(nutriments.get("carbohydrates_100g", 0)),
                "calories_100g": float(nutriments.get("energy-kcal_100g", 0))
            })
        return results
        
    except Exception as e:
        print(f"API 请求失败: {e}")
        return []