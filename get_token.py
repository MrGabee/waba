import time

def generate_waze_token():
    # IDE jön a te Waze / Selenium / Playwright logikád, ami megszerzi a tokent
    # Példa helyettesítő:
    friss_token = "waze_token_pelda_ertek_12345"
    
    return friss_token

if __name__ == "__main__":
    token = generate_waze_token()
    
    # Elmentjük a fájlba, amit a GitHub Actions automatikusan visszaküld a repóba
    with open("waze_token.txt", "w") as f:
        f.f.write(token) if hasattr(f, 'f') else f.write(token)
        
    print("Token sikeresen elmentve!")
