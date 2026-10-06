"""Small reviewed catalogue. No web browsing, prices, addresses, or live claims."""

# Each item is: identifier, display name, interest, neighbourhood/area.
# Area labels help keep a day's stops together. They are not route estimates.
PLACES = {
    "Jaipur": [
        ("amber", "Amber Fort", "history", "Amber"),
        ("jal", "Jal Mahal photo stop", "photography", "Amber"),
        ("city", "City Palace", "history", "Old City"),
        ("jantar", "Jantar Mantar", "history", "Old City"),
        ("hawa", "Hawa Mahal", "photography", "Old City"),
        ("bazaar", "Old-city market walk", "shopping", "Old City"),
        ("albert", "Albert Hall Museum", "history", "Central Jaipur"),
        ("gate", "Patrika Gate", "photography", "Jawahar Circle"),
        ("food", "Rajasthani thali and local food", "food", "Near your stay"),
    ],
    "Udaipur": [
        ("palace", "City Palace", "history", "Old City"),
        ("pichola", "Lake Pichola lakeside walk", "nature", "Old City"),
        ("jagdish", "Jagdish Temple", "culture", "Old City"),
        ("bagore", "Bagore Ki Haveli", "history", "Old City"),
        ("market", "Old-city market walk", "shopping", "Old City"),
        ("fateh", "Fateh Sagar Lake", "nature", "Fateh Sagar"),
        ("garden", "Saheliyon Ki Bari", "nature", "Fateh Sagar"),
        ("photo", "Lakeside photography", "photography", "Old City"),
        ("food", "Rajasthani vegetarian meal", "food", "Near your stay"),
    ],
    "Mysuru": [
        ("palace", "Mysore Palace", "history", "City Centre"),
        ("market", "Devaraja Market", "shopping", "City Centre"),
        ("church", "St. Philomena's Church", "culture", "Central Mysuru"),
        ("chamundi", "Chamundi Hill", "culture", "Chamundi Hill"),
        ("karanji", "Karanji Lake", "nature", "East Mysuru"),
        ("rail", "Rail Museum", "history", "Central Mysuru"),
        ("photo", "Palace-area photography", "photography", "City Centre"),
        ("food", "South Indian meal and Mysore pak", "food", "Near your stay"),
    ],
    "Goa": [
        ("bom", "Basilica of Bom Jesus", "history", "Old Goa"),
        ("se", "Se Cathedral", "history", "Old Goa"),
        ("fontainhas", "Fontainhas walk", "culture", "Panaji"),
        ("panaji", "Panaji market walk", "shopping", "Panaji"),
        ("miramar", "Miramar Beach walk", "nature", "Panaji"),
        ("aguada", "Fort Aguada", "history", "Candolim"),
        ("candolim", "Candolim Beach walk", "nature", "Candolim"),
        ("photo", "Fontainhas photography", "photography", "Panaji"),
        ("food", "Goan meal with vegetarian options", "food", "Near your stay"),
    ],
    "Delhi": [
        ("red", "Red Fort", "history", "Old Delhi"),
        ("chandni", "Chandni Chowk market walk", "shopping", "Old Delhi"),
        ("jama", "Jama Masjid", "culture", "Old Delhi"),
        ("humayun", "Humayun's Tomb", "history", "South-East Delhi"),
        ("lodhi", "Lodhi Garden", "nature", "Central Delhi"),
        ("india", "India Gate", "photography", "Central Delhi"),
        ("qutub", "Qutub Minar", "history", "South Delhi"),
        ("cp", "Connaught Place walk", "shopping", "Central Delhi"),
        ("food", "Local meal with vegetarian options", "food", "Near your stay"),
    ],
    "Agra": [
        ("taj", "Taj Mahal", "history", "Taj Area"),
        ("fort", "Agra Fort", "history", "Central Agra"),
        ("mehtab", "Mehtab Bagh", "nature", "Across the Yamuna"),
        ("itmad", "Itimad-ud-Daulah", "history", "Across the Yamuna"),
        ("sadar", "Sadar Bazaar", "shopping", "Central Agra"),
        ("photo", "Monument photography from permitted areas", "photography", "Taj Area"),
        ("food", "Local vegetarian meal and petha", "food", "Near your stay"),
    ],
}

INTERESTS = ("history", "food", "culture", "nature", "photography", "shopping")
REST = ("rest", "Free time / rest near your accommodation", "nature", "Near your stay")


def catalogue(destination):
    return {item[0]: item for item in [*PLACES[destination], REST]}
