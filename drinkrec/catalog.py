"""Curated catalog of things that can go in a drink.

Only items in this catalog can ever appear in a recipe. That is the "screen": alcohols, and
non-alcoholic ingredients that are actually used in drinks (juices, syrups, mixers, dairy, bitters,
garnishes and seasonings). Prompts may mention any food (e.g. "basil", "dark chocolate"); those
steer the flavor search but are only used directly if they are also in this catalog.

Each entry:
    key    unique id
    label  display name
    role   spirit | liqueur | fortified | sparkling | beer | sour | sweetener | juice | mixer |
           hot | dairy | bitters | garnish
    node   FlavorGraph ingredient used for recipe-pairing scores and embeddings
    chem   FlavorGraph ingredients whose flavor compounds stand in for this item's chemistry
           (bottled products rarely have compound data; e.g. lime juice -> lime)
    tags   flavor descriptors used by theme words in prompts
    prep   (garnish only) how it goes on the drink
"""

C = []


def add(key, label, role, node, chem=None, tags=(), prep=None):
    C.append(dict(key=key, label=label, role=role, node=node, chem=list(chem or [node]),
                  tags=set(tags), prep=prep))


# --- base spirits ------------------------------------------------------------------------------
add("vodka", "Vodka", "spirit", "vodka", ["vodka"], ["clean", "neutral", "light"])
add("vanilla_vodka", "Vanilla vodka", "spirit", "vanilla_vodka", ["vodka", "vanilla"], ["sweet", "vanilla", "dessert"])
add("gin", "Gin", "spirit", "gin", ["gin", "lemon", "coriander"], ["herbal", "botanical", "floral", "citrus", "crisp"])
add("white_rum", "White rum", "spirit", "white_rum", ["rum"], ["tropical", "light", "sweet"])
add("dark_rum", "Dark rum", "spirit", "dark_rum", ["rum", "molasses"], ["tropical", "rich", "caramel", "warm"])
add("spiced_rum", "Spiced rum", "spirit", "spiced_rum", ["rum", "cinnamon", "vanilla", "clove"], ["warm", "spice", "tropical", "cozy"])
add("coconut_rum", "Coconut rum", "spirit", "coconut_rum", ["rum", "coconut"], ["tropical", "sweet", "coconut"])
add("tequila", "Blanco tequila", "spirit", "tequila", ["agave"], ["agave", "bright", "peppery", "earthy"])
add("mezcal", "Mezcal", "spirit", "mezcal", ["agave", "scotch_whisky"], ["smoky", "agave", "earthy"])
add("bourbon", "Bourbon", "spirit", "bourbon", ["scotch_whisky", "vanilla", "caramel"], ["warm", "caramel", "vanilla", "oak", "cozy", "rich"])
add("rye", "Rye whiskey", "spirit", "rye_whiskey", ["scotch_whisky", "black_pepper"], ["spice", "peppery", "oak", "dry"])
add("scotch", "Scotch whisky", "spirit", "scotch_whisky", ["scotch_whisky"], ["smoky", "oak", "malty", "earthy"])
add("irish_whiskey", "Irish whiskey", "spirit", "irish_whiskey", ["scotch_whisky", "honey"], ["smooth", "malty", "warm"])
add("brandy", "Brandy", "spirit", "brandy", ["brandy", "grape"], ["fruity", "warm", "rich", "oak"])
add("cognac", "Cognac", "spirit", "cognac", ["brandy", "grape"], ["fruity", "rich", "oak", "elegant"])
add("apple_brandy", "Apple brandy (Calvados)", "spirit", "apple_brandy", ["apple_brandy", "apple"], ["apple", "fruity", "autumn", "warm"])
add("cherry_brandy", "Cherry brandy (kirsch)", "spirit", "cherry_brandy", ["cherry_brandy", "cherry"], ["cherry", "fruity", "berry"])
add("pisco", "Pisco", "spirit", "pisco", ["brandy", "grape"], ["floral", "fruity", "bright"])
add("cachaca", "Cachaça", "spirit", "cachaca", ["rum"], ["grassy", "tropical", "bright"])
add("sake", "Sake", "spirit", "sake", ["sake"], ["clean", "floral", "light", "rice"])

# --- liqueurs ----------------------------------------------------------------------------------
add("triple_sec", "Triple sec", "liqueur", "triple_sec", ["orange"], ["citrus", "orange", "sweet"])
add("cointreau", "Cointreau", "liqueur", "cointreau_liqueur", ["orange"], ["citrus", "orange"])
add("grand_marnier", "Grand Marnier", "liqueur", "grand_marnier", ["orange", "brandy"], ["citrus", "orange", "rich"])
add("amaretto", "Amaretto", "liqueur", "amaretto", ["almond", "apricot"], ["nutty", "almond", "sweet", "dessert"])
add("coffee_liqueur", "Coffee liqueur (Kahlúa)", "liqueur", "kahlua", ["coffee", "vanilla"], ["coffee", "rich", "dessert", "sweet"])
add("hazelnut_liqueur", "Hazelnut liqueur (Frangelico)", "liqueur", "frangelico", ["hazelnut"], ["nutty", "dessert", "sweet"])
add("peach_schnapps", "Peach schnapps", "liqueur", "peach_schnapps", ["peach"], ["fruity", "peach", "sweet"])
add("limoncello", "Limoncello", "liqueur", "limoncello", ["lemon"], ["citrus", "lemon", "sweet", "bright"])
add("elderflower", "Elderflower liqueur", "liqueur", "elderflower_liqueur", ["pear", "grape", "lemon"], ["floral", "elegant", "light"])
add("creme_de_cassis", "Crème de cassis", "liqueur", "creme_de_cassis", ["blackberry", "blueberry"], ["berry", "fruity", "rich"])
add("cherry_liqueur", "Cherry liqueur", "liqueur", "cherry_brandy", ["cherry", "sour_cherry", "almond"], ["cherry", "berry", "fruity"])
add("banana_liqueur", "Banana liqueur", "liqueur", "banana_liqueur", ["banana"], ["tropical", "banana", "sweet"])
add("melon_liqueur", "Melon liqueur (Midori)", "liqueur", "midori_melon_liqueur", ["melon"], ["fruity", "melon", "sweet"])
add("campari", "Campari", "liqueur", "campari", ["grapefruit", "orange", "clove"], ["bitter", "aperitif", "citrus"])
add("absinthe", "Absinthe (rinse)", "liqueur", "absinthe", ["anise", "fennel", "star_anise"], ["anise", "herbal", "strong"])
add("benedictine", "Bénédictine", "liqueur", "benedictine", ["honey", "anise", "cardamom"], ["herbal", "honey", "warm"])
add("drambuie", "Drambuie", "liqueur", "drambuie", ["honey", "scotch_whisky"], ["honey", "smoky", "warm"])

# --- fortified & aromatized wines (vermouth etc.) -----------------------------------------------
add("sweet_vermouth", "Sweet vermouth", "fortified", "sweet_vermouth", ["red_wine", "vanilla", "clove"], ["rich", "herbal", "bitter", "aperitif"])
add("dry_vermouth", "Dry vermouth", "fortified", "dry_vermouth", ["white_wine", "thyme"], ["dry", "herbal", "crisp", "aperitif"])
add("dry_sherry", "Dry sherry", "fortified", "dry_sherry", ["white_wine", "almond", "walnut"], ["nutty", "dry", "savory"])
add("port", "Ruby port", "fortified", "port_wine", ["port_wine"], ["berry", "rich", "dessert", "warm"])
add("madeira", "Madeira", "fortified", "madeira_wine", ["port_wine", "walnut"], ["nutty", "caramel", "rich"])
add("red_wine", "Red wine", "fortified", "red_wine", ["red_wine"], ["berry", "rich", "dry"])
add("white_wine", "Dry white wine", "fortified", "dry_white_wine", ["white_wine"], ["crisp", "light", "dry"])
add("rose_wine", "Rosé wine", "fortified", "rose_wine", ["rose_wine"], ["light", "berry", "floral"])

# --- sparkling ----------------------------------------------------------------------------------
add("prosecco", "Prosecco", "sparkling", "prosecco", ["sparkling_wine"], ["bubbly", "light", "celebration", "fruity"])
add("champagne", "Champagne", "sparkling", "champagne", ["champagne"], ["bubbly", "celebration", "elegant", "dry"])

# --- beer & cider ------------------------------------------------------------------------------
add("lager", "Light lager", "beer", "light_beer", ["beer"], ["light", "crisp", "malty"])
add("stout", "Stout", "beer", "guinness_stout", ["beer", "coffee", "cocoa"], ["rich", "coffee", "malty", "dark"])
add("hard_cider", "Hard cider", "beer", "hard_alcoholic_cider", ["cider", "apple"], ["apple", "autumn", "crisp", "bubbly"])

# --- sours (fresh citrus) -----------------------------------------------------------------------
add("lime_juice", "Fresh lime juice", "sour", "fresh_lime_juice", ["lime"], ["citrus", "sour", "bright", "tropical"])
add("lemon_juice", "Fresh lemon juice", "sour", "fresh_lemon_juice", ["lemon"], ["citrus", "sour", "bright"])
add("grapefruit_juice", "Fresh grapefruit juice", "sour", "grapefruit_juice", ["grapefruit"], ["citrus", "bitter", "bright"])
add("yuzu_juice", "Yuzu juice", "sour", "yuzu", ["lemon", "tangerine", "grapefruit"], ["citrus", "floral", "bright"])

# --- sweeteners --------------------------------------------------------------------------------
add("simple_syrup", "Simple syrup (1:1)", "sweetener", "simple_syrup", ["sugar"], ["sweet", "neutral"])
add("honey_syrup", "Honey syrup (2:1)", "sweetener", "honey_syrup", ["honey"], ["honey", "floral", "warm"])
add("maple_syrup", "Maple syrup", "sweetener", "maple_syrup", ["maple_syrup", "molasses"], ["maple", "autumn", "warm", "caramel", "cozy"])
add("agave_syrup", "Agave syrup", "sweetener", "agave_nectar", ["agave"], ["agave", "sweet"])
add("demerara_syrup", "Demerara syrup", "sweetener", "demerara_sugar", ["molasses", "brown_sugar"], ["caramel", "rich", "warm"])
add("grenadine", "Grenadine", "sweetener", "grenadine", ["pomegranate"], ["berry", "fruity", "sweet"])
add("ginger_syrup", "Ginger syrup", "sweetener", "ginger", ["ginger"], ["spicy", "ginger", "warm"])
add("cinnamon_syrup", "Cinnamon syrup", "sweetener", "cinnamon", ["cinnamon"], ["warm", "spice", "cozy", "autumn"])
add("vanilla_syrup", "Vanilla syrup", "sweetener", "vanilla", ["vanilla"], ["vanilla", "sweet", "dessert"])
add("raspberry_syrup", "Raspberry syrup", "sweetener", "raspberry", ["raspberry"], ["berry", "fruity", "sweet"])
add("lavender_syrup", "Lavender syrup", "sweetener", "lavender", ["rosemary", "thyme"], ["floral", "herbal", "elegant"])
add("orgeat", "Orgeat (almond syrup)", "sweetener", "almond", ["almond"], ["nutty", "almond", "tropical"])

# --- juices & purees ---------------------------------------------------------------------------
add("pineapple_juice", "Pineapple juice", "juice", "pineapple_juice", ["pineapple"], ["tropical", "fruity", "sweet"])
add("orange_juice", "Fresh orange juice", "juice", "fresh_orange_juice", ["orange"], ["citrus", "fruity", "brunch"])
add("cranberry_juice", "Cranberry juice", "juice", "cranberry_juice", ["cranberry"], ["tart", "berry", "holiday"])
add("apple_cider", "Fresh apple cider", "juice", "apple_cider", ["apple"], ["apple", "autumn", "cozy"])
add("pomegranate_juice", "Pomegranate juice", "juice", "pomegranate_juice", ["pomegranate"], ["tart", "berry", "fruity"])
add("mango_puree", "Mango purée", "juice", "mango_nectar", ["mango"], ["tropical", "fruity", "sweet"])
add("passion_fruit", "Passion fruit purée", "juice", "passion_fruit_juice", ["guava", "mango", "pineapple"], ["tropical", "tart", "fruity"])
add("peach_puree", "Peach purée", "juice", "peach_nectar", ["peach"], ["fruity", "peach", "summer"])
add("strawberry_puree", "Strawberry purée", "juice", "strawberry", ["strawberry"], ["berry", "fruity", "summer", "romantic"])
add("watermelon_juice", "Watermelon juice", "juice", "watermelon", ["melon"], ["fruity", "summer", "refreshing"])
add("cherry_juice", "Tart cherry juice", "juice", "cherry_juice", ["sour_cherry", "cherry"], ["cherry", "tart", "berry"])
add("coconut_water", "Coconut water", "juice", "coconut_water", ["coconut"], ["tropical", "light", "refreshing"])
add("tomato_juice", "Tomato juice", "juice", "tomato_juice", ["tomato"], ["savory", "brunch", "umami"])
add("cucumber_juice", "Cucumber juice", "juice", "cucumber", ["cucumber"], ["fresh", "green", "refreshing", "summer"])

# --- mixers / lengtheners ----------------------------------------------------------------------
add("club_soda", "Club soda", "mixer", "club_soda", ["club_soda"], ["bubbly", "light", "refreshing"])
add("tonic", "Tonic water", "mixer", "tonic_water", ["lemon", "grapefruit"], ["bitter", "bubbly", "crisp"])
add("ginger_beer", "Ginger beer", "mixer", "ginger_beer", ["ginger", "lemon"], ["spicy", "ginger", "bubbly"])
add("ginger_ale", "Ginger ale", "mixer", "ginger_ale", ["ginger"], ["ginger", "bubbly", "light"])
add("cola", "Cola", "mixer", "cola", ["vanilla", "cinnamon", "lime"], ["sweet", "bubbly", "caramel"])
add("lemonade", "Lemonade", "mixer", "lemonade", ["lemon"], ["citrus", "sweet", "summer"])
add("grapefruit_soda", "Grapefruit soda", "mixer", "grapefruit", ["grapefruit"], ["citrus", "bitter", "bubbly"])

# --- hot / long non-carbonated -------------------------------------------------------------------
add("hot_black_tea", "Hot black tea", "hot", "black_tea", ["black_tea", "tea"], ["warm", "earthy", "cozy"])
add("hot_green_tea", "Hot green tea", "hot", "green_tea", ["green_tea", "tea"], ["warm", "green", "earthy"])
add("hot_coffee", "Hot brewed coffee", "hot", "brewed_coffee", ["coffee"], ["coffee", "warm", "morning"])
add("espresso", "Espresso", "hot", "espresso", ["coffee"], ["coffee", "rich", "bitter"])
add("hot_cider", "Hot apple cider", "hot", "apple_cider", ["apple", "cinnamon"], ["apple", "autumn", "warm", "cozy"])
add("hot_water", "Hot water", "hot", "water", ["lemon"], ["warm", "neutral"])

# --- dairy & texture ---------------------------------------------------------------------------
add("heavy_cream", "Heavy cream", "dairy", "heavy_cream", ["cream", "milk"], ["creamy", "rich", "dessert"])
add("whole_milk", "Whole milk", "dairy", "whole_milk", ["milk"], ["creamy", "light"])
add("coconut_cream", "Coconut cream", "dairy", "coconut_milk", ["coconut"], ["creamy", "tropical", "coconut"])
add("egg_white", "Egg white (for foam)", "dairy", "egg_white", ["egg"], ["silky", "foam"])

# --- bitters -----------------------------------------------------------------------------------
add("aromatic_bitters", "Aromatic bitters", "bitters", "clove", ["clove", "cinnamon", "cardamom", "orange"], ["spice", "bitter", "warm"])
add("orange_bitters", "Orange bitters", "bitters", "orange_peel", ["orange", "cardamom"], ["citrus", "orange", "bitter"])
add("chocolate_bitters", "Chocolate bitters", "bitters", "cocoa", ["cocoa"], ["chocolate", "bitter", "dessert"])
add("celery_bitters", "Celery bitters", "bitters", "celery", ["celery"], ["savory", "green", "herbal"])

# --- garnishes & seasonings (encouraged) --------------------------------------------------------
G = "garnish"
add("lime_wheel", "Lime wheel", G, "lime", tags=["citrus", "tropical", "bright"], prep="a lime wheel on the rim")
add("lemon_twist", "Lemon twist", G, "lemon_peel", ["lemon"], ["citrus", "bright"], prep="a lemon twist, oils expressed over the top")
add("orange_peel", "Orange peel", G, "orange_peel", ["orange"], ["citrus", "orange", "warm"], prep="an orange peel, oils expressed over the top")
add("grapefruit_peel", "Grapefruit peel", G, "grapefruit_peel", ["grapefruit"], ["citrus", "bitter"], prep="a grapefruit peel, oils expressed over the top")
add("cinnamon_stick", "Cinnamon", G, "cinnamon", tags=["warm", "spice", "cozy", "autumn", "holiday"], prep="a cinnamon stick (or a pinch of ground cinnamon on top)")
add("nutmeg", "Nutmeg", G, "nutmeg", tags=["warm", "spice", "holiday", "dessert", "creamy"], prep="freshly grated nutmeg on top")
add("star_anise", "Star anise", G, "star_anise", tags=["anise", "warm", "spice", "holiday"], prep="one star anise pod floated on top")
add("clove", "Clove", G, "clove", tags=["warm", "spice", "holiday"], prep="2-3 whole cloves studded into the citrus garnish")
add("cardamom", "Cardamom", G, "cardamom", tags=["warm", "spice", "floral"], prep="a pinch of ground cardamom on top")
add("black_pepper", "Black pepper", G, "black_pepper", ["black_pepper", "cardamom"], ["peppery", "spice", "savory"], prep="a few grinds of black pepper on top")
add("chili_salt_rim", "Chili-lime salt rim", G, "cayenne", ["lime", "paprika"], ["spicy", "savory", "agave"], prep="a chili-lime salt rim (half the glass)")
add("salt_rim", "Flaky sea salt", G, "sea_salt", ["lime"], ["savory", "agave", "citrus"], prep="a pinch of flaky sea salt on top (or a half salt rim)")
add("jalapeno", "Jalapeño", G, "jalapeno", ["jalapeno", "bell_pepper", "cucumber"], ["spicy", "green", "savory"], prep="2 thin jalapeño slices (muddle one for more heat)")
add("ginger_slice", "Fresh ginger", G, "ginger", tags=["spicy", "ginger", "warm"], prep="a thin coin of fresh ginger")
add("mint_sprig", "Mint", G, "mint", ["mint", "spearmint"], ["herbal", "fresh", "green", "refreshing", "summer"], prep="a big mint sprig, slapped to release the aroma")
add("basil_leaf", "Basil", G, "basil", tags=["herbal", "green", "fresh", "summer"], prep="a fresh basil leaf")
add("rosemary_sprig", "Rosemary", G, "rosemary", tags=["herbal", "earthy", "smoky", "winter"], prep="a rosemary sprig (lightly torched for a smoky aroma)")
add("thyme_sprig", "Thyme", G, "thyme", tags=["herbal", "earthy", "savory"], prep="a fresh thyme sprig")
add("sage_leaf", "Sage", G, "sage", tags=["herbal", "earthy", "autumn"], prep="a fresh sage leaf")
add("lavender", "Lavender", G, "lavender", ["rosemary", "thyme"], ["floral", "elegant"], prep="a small lavender sprig")
add("cucumber_ribbon", "Cucumber", G, "cucumber", tags=["fresh", "green", "refreshing", "summer"], prep="a long cucumber ribbon inside the glass")
add("brandied_cherry", "Brandied cherry", G, "cherry", tags=["cherry", "rich", "berry"], prep="a brandied cherry on a pick")
add("fresh_berries", "Fresh berries", G, "raspberry", ["raspberry", "blackberry", "strawberry"], ["berry", "fruity", "summer"], prep="a few fresh berries on a pick")
add("pineapple_wedge", "Pineapple wedge", G, "pineapple", tags=["tropical", "fruity"], prep="a pineapple wedge (and fronds) on the rim")
add("apple_slice", "Apple slice", G, "apple", tags=["apple", "autumn", "crisp"], prep="a thin apple fan")
add("cocoa_dust", "Cocoa powder", G, "cocoa_powder", ["cocoa"], ["chocolate", "dessert", "rich"], prep="a light dusting of cocoa powder")
add("coffee_beans", "Coffee beans", G, "espresso_bean", ["coffee"], ["coffee", "rich"], prep="three coffee beans floated on top")
add("toasted_coconut", "Toasted coconut", G, "coconut", tags=["tropical", "coconut", "nutty"], prep="a toasted coconut rim")
add("edible_flower", "Edible flower", G, "rose_water", ["strawberry", "raspberry"], ["floral", "romantic", "elegant"], prep="an edible flower (rose petal or viola)")
add("vanilla_bean", "Vanilla bean", G, "vanilla_bean", ["vanilla"], ["vanilla", "dessert", "warm"], prep="a split vanilla bean")
add("smoked_paprika", "Smoked paprika", G, "smoked_paprika", ["paprika"], ["smoky", "savory", "spicy"], prep="a pinch of smoked paprika on top")

CATALOG = {c["key"]: c for c in C}
ROLES = sorted({c["role"] for c in C})
