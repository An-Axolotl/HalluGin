"""Theme words -> seed ingredients (FlavorGraph names), flavor tags, and preferred drink styles.

This replaces an LLM: words in the prompt are matched here, against the drink catalog, and against
every FlavorGraph ingredient name. Seeds drive the chemical/pairing search; tags add a small bonus
for catalog items described the same way; styles bias which cocktail structure is used.
"""

THEMES = {
    "smoky":      (["scotch_whisky", "smoked_paprika", "rosemary"], ["smoky", "oak", "earthy"], ["stirred", "sour"]),
    "citrus":     (["lemon", "lime", "grapefruit", "orange"], ["citrus", "bright"], ["sour", "highball"]),
    "tropical":   (["pineapple", "coconut", "mango", "banana", "lime"], ["tropical", "coconut"], ["tiki", "highball"]),
    "autumn":     (["apple", "cinnamon", "maple_syrup", "pear", "nutmeg"], ["autumn", "apple", "warm", "cozy", "spice"], ["sour", "stirred", "toddy"]),
    "winter":     (["cinnamon", "clove", "star_anise", "cranberry", "orange", "ginger"], ["warm", "spice", "holiday", "cozy"], ["toddy", "stirred", "flip"]),
    "summer":     (["cucumber", "mint", "lime", "watermelon", "strawberry"], ["summer", "refreshing", "fresh", "light"], ["highball", "spritz", "mule"]),
    "spring":     (["strawberry", "mint", "lemon", "rose_water", "cucumber"], ["floral", "fresh", "light"], ["spritz", "sour", "highball"]),
    "refreshing": (["cucumber", "mint", "lime", "lemon"], ["refreshing", "fresh", "light", "bubbly"], ["highball", "mule", "spritz"]),
    "spicy":      (["jalapeno", "ginger", "cayenne", "black_pepper"], ["spicy", "peppery", "ginger"], ["sour", "mule"]),
    "floral":     (["rose_water", "lavender", "orange_flower_water", "pear"], ["floral", "elegant"], ["sour", "spritz"]),
    "herbal":     (["basil", "mint", "rosemary", "thyme", "sage"], ["herbal", "green", "botanical"], ["sour", "highball"]),
    "berry":      (["strawberry", "raspberry", "blackberry", "blueberry"], ["berry", "fruity"], ["sour", "spritz"]),
    "fruity":     (["peach", "strawberry", "mango", "pineapple", "raspberry"], ["fruity"], ["sour", "tiki", "spritz"]),
    "sweet":      (["vanilla", "caramel", "honey"], ["sweet", "dessert", "vanilla"], ["flip", "sour"]),
    "dessert":    (["vanilla", "chocolate", "caramel", "cream", "cinnamon"], ["dessert", "creamy", "chocolate", "vanilla"], ["flip"]),
    "creamy":     (["cream", "coconut", "vanilla"], ["creamy", "rich", "silky"], ["flip"]),
    "coffee":     (["coffee", "cocoa", "vanilla"], ["coffee", "rich"], ["flip", "stirred"]),
    "chocolate":  (["cocoa", "chocolate", "vanilla", "cherry"], ["chocolate", "dessert", "rich"], ["flip", "stirred"]),
    "bitter":     (["grapefruit", "orange", "campari", "sweet_vermouth"], ["bitter", "aperitif"], ["stirred", "spritz"]),
    "nutty":      (["almond", "hazelnut", "walnut", "pecan"], ["nutty", "almond"], ["sour", "flip", "stirred"]),
    "earthy":     (["black_tea", "walnut", "beet", "mushroom", "sage"], ["earthy", "oak", "herbal"], ["stirred", "sour"]),
    "romantic":   (["strawberry", "raspberry", "rose_water", "chocolate", "champagne"], ["romantic", "berry", "floral", "bubbly"], ["spritz", "sour"]),
    "celebration": (["champagne", "strawberry", "lemon", "peach"], ["celebration", "bubbly", "elegant"], ["spritz", "sour"]),
    "brunch":     (["orange", "peach", "tomato", "grapefruit", "coffee"], ["brunch", "bubbly", "citrus"], ["spritz", "highball"]),
    "strong":     ([], ["oak", "rich"], ["stirred"]),
    "light":      (["cucumber", "lemon", "mint"], ["light", "refreshing", "bubbly"], ["highball", "spritz"]),
    "sour":       (["lemon", "lime", "cranberry", "sour_cherry"], ["sour", "tart", "citrus"], ["sour"]),
    "warm":       (["cinnamon", "honey", "ginger", "clove"], ["warm", "cozy", "spice"], ["toddy", "stirred"]),
    "savory":     (["tomato", "celery", "black_pepper", "olive"], ["savory", "umami", "peppery"], ["highball", "stirred"]),
    "bubbly":     (["champagne", "lemon"], ["bubbly", "celebration"], ["spritz", "highball"]),
    "elegant":    (["champagne", "pear", "lemon", "rose_water"], ["elegant", "floral", "dry"], ["stirred", "spritz", "sour"]),
    "cozy":       (["cinnamon", "vanilla", "maple_syrup", "apple"], ["cozy", "warm", "spice"], ["toddy", "flip", "stirred"]),
    "beach":      (["coconut", "pineapple", "lime", "mango"], ["tropical", "refreshing"], ["tiki", "highball"]),
    "green":      (["cucumber", "basil", "mint", "green_tea", "lime"], ["green", "herbal", "fresh"], ["highball", "sour"]),
    "dry":        (["lemon", "grapefruit"], ["dry", "crisp"], ["stirred", "spritz"]),
    "tart":       (["cranberry", "sour_cherry", "lime", "pomegranate"], ["tart", "sour"], ["sour"]),
    "peppery":    (["black_pepper", "ginger"], ["peppery", "spice"], ["sour", "stirred"]),
    "morning":    (["coffee", "orange", "grapefruit"], ["coffee", "brunch", "citrus"], ["highball", "flip"]),
}

# synonyms / related words -> theme
ALIASES = {
    "smoke": "smoky", "smoked": "smoky", "peaty": "smoky", "campfire": "smoky", "bonfire": "smoky", "charred": "smoky",
    "citrusy": "citrus", "zesty": "citrus", "bright": "citrus", "zingy": "citrus", "tangy": "sour",
    "tiki": "tropical", "island": "tropical", "vacation": "tropical", "hawaii": "tropical", "caribbean": "tropical",
    "fall": "autumn", "thanksgiving": "autumn", "harvest": "autumn", "halloween": "autumn", "pumpkin": "autumn",
    "christmas": "winter", "holiday": "winter", "holidays": "winter", "snow": "winter", "cold": "winter", "festive": "winter",
    "hot": "spicy", "heat": "spicy", "fiery": "spicy", "kick": "spicy",
    "poolside": "summer", "sunny": "summer", "patio": "summer", "bbq": "summer", "picnic": "summer",
    "fresh": "refreshing", "crisp": "refreshing", "cool": "refreshing", "cooling": "refreshing", "thirst": "refreshing",
    "flowery": "floral", "perfumed": "floral", "garden": "herbal", "herby": "herbal", "botanical": "herbal",
    "berries": "berry", "jammy": "berry", "fruit": "fruity", "juicy": "fruity",
    "sugary": "sweet", "candy": "sweet", "indulgent": "dessert", "decadent": "dessert", "rich": "dessert",
    "milky": "creamy", "velvety": "creamy", "smooth": "creamy", "espresso": "coffee", "caffeinated": "coffee",
    "cocoa": "chocolate", "chocolatey": "chocolate", "aperitif": "bitter", "aperitivo": "bitter", "italian": "bitter",
    "nut": "nutty", "nuts": "nutty", "woody": "earthy", "mossy": "earthy",
    "date": "romantic", "valentine": "romantic", "valentines": "romantic", "love": "romantic", "anniversary": "romantic",
    "party": "celebration", "birthday": "celebration", "wedding": "celebration", "toast": "celebration", "newyear": "celebration",
    "boozy": "strong", "stiff": "strong", "spirit-forward": "strong", "nightcap": "strong",
    "easy": "light", "sessionable": "light", "low": "light", "airy": "light",
    "warming": "warm", "warmer": "warm", "warmers": "warm", "comforting": "cozy", "fireside": "cozy", "rainy": "cozy",
    "umami": "savory", "salty": "savory", "fizzy": "bubbly", "sparkling": "bubbly", "effervescent": "bubbly",
    "sophisticated": "elegant", "classy": "elegant", "fancy": "elegant",
    "sunrise": "morning", "breakfast": "brunch", "mimosa": "brunch",
}

STYLE_WORDS = {
    "sour": "sour", "highball": "highball", "collins": "highball", "tall": "highball", "long": "highball",
    "stirred": "stirred", "manhattan": "stirred", "negroni": "stirred", "martini": "stirred", "old-fashioned": "stirred",
    "spritz": "spritz", "flip": "flip", "toddy": "toddy", "mulled": "toddy", "mug": "toddy",
    "tiki": "tiki", "punch": "tiki", "mule": "mule", "buck": "mule",
}
