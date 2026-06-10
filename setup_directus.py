import urllib.request
import json
import time

BASE = "http://localhost:8055"

def api(path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    except Exception:
        return None

def ensure_permission(token, policy_id, collection):
    r = api(f"/permissions?filter[collection][_eq]={collection}&filter[policy][_eq]={policy_id}", token=token)
    permission = (r.get("data") or [None])[0] if r else None

    desired = {
        "policy": policy_id,
        "collection": collection,
        "action": "read",
        "fields": "*"
    }

    if permission:
        perm_id = permission["id"]
        if permission.get("fields") == "*" or permission.get("fields") == ["*"]:
            print(f"✔ Разрешение на {collection} уже есть")
            return
        print(f"Обновляю разрешение на {collection}...")
        resp = api(f"/permissions/{perm_id}", "PATCH", desired, token=token)
        if resp and resp.get("data"):
            print(f"✔ Разрешение на {collection} обновлено")
        else:
            print(f"✗ Ошибка обновления {collection}")
    else:
        print(f"Создаю публичное разрешение на {collection}...")
        resp = api("/permissions", "POST", desired, token=token)
        if resp and resp.get("data"):
            print(f"✔ Разрешение на {collection} создано")
        else:
            print(f"✗ Ошибка создания {collection}")

def main():
    print("Ожидание Directus...")
    for attempt in range(1, 21):
        r = api("/server/health")
        if r and r.get("status") == "ok":
            print("Directus готов")
            break
        print(f"Попытка {attempt}/20")
        time.sleep(3)
    else:
        print("Directus не запустился вовремя")
        return

    print("Вход в Directus...")
    r = api("/auth/login", "POST", {"email": "admin@arctic.ru", "password": "admin123"})
    if not r or "data" not in r:
        print("Ошибка авторизации")
        return
    token = r["data"]["access_token"]
    print("Успешно авторизован")

    r = api("/policies", token=token)
    public_policy = next((p for p in (r.get("data") or []) if "public" in p.get("name","").lower()), None)
    if not public_policy:
        print("Публичная политика не найдена")
        return
    policy_id = public_policy["id"]
    print(f"Найдена политика: {public_policy['name']} (id={policy_id})")

    ensure_permission(token, policy_id, "news")
    ensure_permission(token, policy_id, "sources")

    print("\nГотово. Теперь фронтенд сможет читать источники.")

if __name__ == "__main__":
    main()