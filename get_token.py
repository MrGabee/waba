import time

# Ide tedd be a Waze token lekérdező logikádat (pl. Selenium / kérések)
token_ertek = "ide_kerul_a_token"

# Elmentjük a waze_token.txt fájlba, hogy a GitHub Actions fel tudja dolgozni
with open("waze_token.txt", "w") as f:
    f.write(token_ertek)

print("Token sikeresen elmentve!")