"""
Shared categorization logic for all bank parsers.
Works with both Indian UPI-style descriptions and US bank descriptions.
"""

import re

# ── Category rules ──────────────────────────────────────────────────────────
# Each tuple: (category_name, [keywords checked against UPPERCASED description])
# First match wins.

CATEGORY_RULES = [
    ("Food & Dining", [
        # India
        "ZOMATO", "SWIGGY", "BLINKIT", "INSTAMART", "ZEPTO", "DUNZO",
        "RATNADEE", "KALE BER", "ANU WINES", "WEDNESDA",
        # US
        "DOORDASH", "GRUBHUB", "UBER EATS", "INSTACART", "CHIPOTLE",
        "MCDONALD", "STARBUCKS", "CHICK-FIL", "SUBWAY", "TACO BELL",
        "PANERA", "DOMINO", "PIZZA HUT", "WHOLE FOODS", "TRADER JOE",
        "SAFEWAY", "KROGER", "PUBLIX", "ALDI", "SPROUTS",
        # Generic
        "RESTAURANT", "CAFE", "BISTRO", "BURGER", "PIZZA", "SUSHI",
        "BAR & GRILL", "KITCHEN", "DINER", "EATERY",
    ]),
    ("Entertainment", [
        # India
        "PVR", "INOX", "NETFLIX", "SPOTIFY", "HOTSTAR", "DISNEY",
        "YOUTUBE", "PRIME VIDEO", "BOOKMYSHOW", "ANTHM", "ANTHEM",
        # US
        "HULU", "HBO MAX", "PEACOCK", "PARAMOUNT", "AMC THEATRES",
        "REGAL CINEMA", "FANDANGO", "TICKETMASTER", "EVENTBRITE",
        "STEAM GAMES", "PLAYSTATION", "XBOX", "NINTENDO",
        "APPLE TV", "APPLE MUSIC",
    ]),
    ("Fashion & Apparel", [
        # India
        "UNIQLO", "ZARA", "FOREVER 2", "FOREVER2", "H AND M", "HENNES",
        "H&M", "AJIO", "WESTSIDE", "PANTALOONS", "BIBA", "FABINDIA",
        # US
        "GAP", "OLD NAVY", "BANANA REPUBLIC", "J.CREW", "NORDSTROM",
        "MACY", "BLOOMINGDALE", "TJ MAXX", "MARSHALLS", "ROSS STORES",
        "BURLINGTON", "EXPRESS", "FOREVER 21", "URBAN OUTFITTERS",
        "ANTHROPOLOGIE", "FREE PEOPLE", "LULULEMON",
        # Generic
        "LEVI", "NIKE", "ADIDAS", "PUMA", "REEBOK", "UNDER ARMOUR",
        "BOSSDOM", "MANGO", "MASSIMO",
    ]),
    ("Beauty & Wellness", [
        # India
        "NYKAA", "SEPHORA", "MAKEOVER", "SNA STUD", "SAVADIKA",
        "SOVA HEA", "PURPLLE", "MAMAEARTH", "LOTUS", "LAKME",
        "BODYSHOP", "BODY SHOP", "SALOON", "SALON", "SPA", "PARLOUR",
        "BOUNCE", "TPR WELL", "SHOPSENS",
        # US
        "ULTA BEAUTY", "BATH & BODY", "BATH AND BODY", "LUSH",
        "GLOSSIER", "FENTY", "MAC COSMETICS", "CLINIQUE",
        "SUPERCUTS", "GREAT CLIPS", "SPORT CLIPS",
        "GYM", "FITNESS", "YOGA", "PLANET FITNESS", "EQUINOX",
        "24 HOUR FITNESS", "LA FITNESS", "ANYTIME FITNESS",
    ]),
    ("Jewellery", [
        "MALABAR", "CARAT LA", "CARATLANE", "TANISHQ", "KALYAN",
        "KAY JEWELERS", "ZALES", "JARED", "TIFFANY", "PANDORA",
    ]),
    ("Electronics & Tech", [
        "APTRONIX", "APPLE INDIA", "APPLE STORE", "SAMSUNG",
        "CROMA", "RELIANCE DIG", "VIJAY SALES", "GOOGLE CLOUD",
        "BEST BUY", "MICROSOFT STORE", "B&H PHOTO", "NEWEGG",
        "AMAZON WEB SERVICES", "AWS", "DIGITALOCEAN", "GITHUB",
        "ADOBE", "AUTODESK", "DROPBOX",
    ]),
    ("Subscriptions", [
        "NETFLIX", "APPLE ME", "APPLE SE", "AIRTEL P", "AIRTEL B",
        "GOOGLEPLAY", "GOOGLE PLAY", "BIL SIGM", "SIGMA",
        "TATAPLAY", "JIOFIBER", "ACT FIBERNET",
        "HULU", "SPOTIFY", "YOUTUBE PREMIUM", "ICLOUD",
        "MICROSOFT 365", "OFFICE 365", "ADOBE CC",
        "AMAZON PRIME", "AUDIBLE",
    ]),
    ("Shopping", [
        # India
        "AMAZON", "FLIPKART", "MYNTRA", "MEESHO", "SNAPDEAL",
        "TATA CLQ", "RELIANCE",
        # US
        "WALMART", "TARGET", "COSTCO", "HOME DEPOT", "LOWE",
        "DOLLAR GENERAL", "DOLLAR TREE", "FIVE BELOW",
        "BED BATH", "CONTAINER STORE", "IKEA", "WAYFAIR",
        "EBAY", "ETSY",
    ]),
    ("Groceries", [
        # India
        "DMART", "BIGBASKET", "GROFERS", "NATURE BASKE",
        "RELIANCE FRESH", "SPENCERS", "MORE MEGA",
        # US — most US grocery already captured in Food & Dining above
        "SMART & FINAL", "FOOD LION", "MEIJER", "WEGMANS", "HEB",
    ]),
    ("Travel & Transport", [
        # India
        "AIRBNB", "UBER", "METRO", "HYDMETROIN", "RAPIDO",
        "MAKEMYTRIP", "GOIBIBO", "CLEARTRIP", "YATRA", "IXIGO",
        "IRCTC", "RED BUS", "REDBUS", "BOUNCE J", "GMR HOSP",
        # US
        "LYFT", "DELTA", "UNITED AIRLINES", "AMERICAN AIR",
        "SOUTHWEST", "JETBLUE", "SPIRIT AIRLINES", "ALASKA AIR",
        "MARRIOTT", "HILTON", "HYATT", "WYNDHAM", "IHG",
        "EXPEDIA", "BOOKING.COM", "HOTELS.COM", "KAYAK",
        "HERTZ", "ENTERPRISE", "AVIS", "NATIONAL CAR",
        "AMTRAK", "GREYHOUND",
    ]),
    ("Healthcare", [
        # India
        "HOSPITAL", "CLINIC", "PHARMA", "MEDICAL", "APOLLO",
        "PRACTO", "MEDIBUDDY", "NETMEDS", "PHARMEASY", "1MG",
        # US
        "WALGREENS", "CVS PHARMACY", "RITE AID", "KAISER",
        "ANTHEM", "AETNA", "CIGNA", "HUMANA", "UNITED HEALTH",
        "OPTUM", "LABCORP", "QUEST DIAGNOSTICS",
    ]),
    ("Education", [
        "GRADVINE", "UDEMY", "COURSERA", "BYJU", "UNACADEMY",
        "VEDANTU", "UPGRAD", "SIMPLILEARN",
        "SKILLSHARE", "PLURALSIGHT", "LINKEDIN LEARNING",
        "CHEGG", "KHAN ACADEMY", "DUOLINGO",
    ]),
    ("Utilities & Bills", [
        # India
        "AIRTEL", "JIO ", "HATHWAY", "ACT ", "BSNL",
        "ELECTRICITY", "BESCOM", "TSSPDCL", "MSEDCL",
        "LIC ", "HDFC LIFE", "SBI LIFE", "INSURANCE",
        # US
        "AT&T", "VERIZON", "T-MOBILE", "COMCAST", "XFINITY",
        "SPECTRUM", "COX COMMUNICATIONS",
        "PG&E", "PACIFIC GAS", "CON EDISON", "DUKE ENERGY",
        "AMERICAN ELECTRIC",
        "ALLSTATE", "STATE FARM", "GEICO", "PROGRESSIVE",
    ]),
]

# Known merchant UPI IDs → not personal transfers
MERCHANT_UPI_IDS = {
    "netflixupi", "zomatoindi", "appleservi", "billdeskpg",
    "zomato4.pa", "payzomato", "zomatoltd", "zomatoonli",
    "nykaa.payu", "amazonsell", "amazonupi", "malabargol",
    "caratlane", "uniqloin", "zara.payu", "googlepay",
    "airtelpaym", "gedditzept", "bharatpe", "q420398442",
}

PERSONAL_UPI_PATTERN = re.compile(
    r"\b\d{10}\b|@oki|saranyasun|uvssnr|vanivideha"
)


def classify(desc: str) -> str:
    """Return the category name for a transaction description."""
    upper = desc.upper()

    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw.upper() in upper:
                return category

    # UPI-specific personal transfer detection (India)
    if "UPI/DR" in upper or "UPI/CR" in upper:
        parts = desc.split("/")
        upi_id = parts[5].lower() if len(parts) > 5 else ""
        merchant_part = parts[3].upper() if len(parts) > 3 else ""

        for mk in MERCHANT_UPI_IDS:
            if mk in upi_id:
                return "Shopping"

        if PERSONAL_UPI_PATTERN.search(upi_id):
            return "Transfers"

        if re.match(r"^[A-Z\s\.]+$", merchant_part.strip()):
            return "Transfers"

    if "OTHPOS" in upper or "OTHPG" in upper or "SBIPOS" in upper:
        return "Shopping"

    return "Others"
