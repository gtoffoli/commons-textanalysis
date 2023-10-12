# from django.utils.translation import gettext_lazy as _
# 
bn_domains = [
("ART, ARCHITECTURE, AND ARCHAEOLOGY", "Art (painting, visual arts, sculpture, etc. except for music, dance, poetry, photography and theatre)), architecture (construction, buildings, etc.)), archaeology (sites, finds etc.)), prehistory"),
("BIOLOGY", "Biology; animals, plants and their classifications, microorganisms"),
("BUSINESS, INDUSTRY AND FINANCE", "Business, industry, economy, finance, management, money"),
("CHEMISTRY AND MINERALOGY", "Chemistry, compounds, chemicals, minerals, mineralogy"),
("COMMUNICATION AND TELECOMMUNICATION", "Communication (oral, written, etc.) and telecommunication (telegraph, telephone, TV, radio, fax, Internet, etc.) means"),
("COMPUTING", "Computer science, computing, hardware and software"),
("CRAFT, ENGINEERING AND TECHNOLOGY", "Crafts (handicraft, skilled work, etc.), engineering, technology"),
("CULTURE, ANTHROPOLOGY AND SOCIETY", "Concepts affecting local and global culture and society; social behavior, trends, norms and expectations in human society; anthropology"),
("EDUCATION AND SCIENCE", "Education, teaching, students; science and general scientific concepts (specific concepts go to the various domains: mathematics, physics, astronomy, biology, chemistry, geology, computing, etc.)"),
("EMOTIONS AND FEELINGS", "Feelings, emotions, emotional states and reactions"),
("ENVIRONMENT AND METEOROLOGY", "Natural environment and its preservation; ecology; natural events (fires, rains, typhoons, etc.); meteorology, weather conditions"),
("FARMING, FISHING AND HUNTING", "Farming, agriculture; plant cultivation, livestock raising; fishing; hunting"),
("FOOD, DRINK AND TASTE", "Food, drinks, flavors, sense of taste; eating places (bars, pubs, restaurants), food events"),
("GEOGRAPHY, GEOLOGY AND PLACES", "Geography and geographical concepts (continents, countries, regions, provinces, cities, towns, villages, rivers, hills, mountains, plains, etc.); geology and geological concepts (solid Earth, rocks, geological processes, earthquakes, volcanos, etc.); geophysics; places"),
("HEALTH AND MEDICINE", "Human health and medicine; diseases, drugs and prescriptions; physical, mental and social well-being"),
("HERALDRY, HONORS, AND VEXILLOLOGY", "Armory, vexillology, honors, ranks"),
("HISTORY", "Events of the past occurred after the invention of writing systems (for prehistory, see archaeology)"),
("LANGUAGE AND LINGUISTICS", "Languages, linguistics, idiomatic expressions, phrases"),
("LAW AND CRIME", "Laws, justice, judges, police, crimes, criminal minds and behaviors"),
("LITERATURE AND THEATRE", "Literature, authors, books, novels, poetry, plays, theatre"),
("MATHEMATICS AND STATISTICS", "Mathematics, statistics, numbers, mathematical operations and functions, mathematical and statistical concepts"),
("MEDIA AND PRESS", "Mass media such as print media (news media, newspapers, magazines, etc.), publishing, photography, cinema (films, directors, screenwriters, etc.), broadcasting (radio and television), and advertising"),
("MUSIC, SOUND AND DANCING", "Sound, sounds, hearing; music, songs, music artists, composers; dances, dancing, dancers"),
("NAVIGATION AND AVIATION", "Nautical and aviation concepts: vessels and aircrafts; pilots; sea and air traveling"),
("NUMISMATICS AND CURRENCIES", "Currencies and their study"),
("PHILOSOPHY, PSYCHOLOGY AND BEHAVIOR", "Philosophical concepts, philosophers; psychology, psychological concepts; human behavior"),
("PHYSICS AND ASTRONOMY", "Physics, physical measures and phenomena, matter, its motion and energy; astronomical concepts, celestial objects, space, physical universe"),
("POLITICS, GOVERNMENT AND NOBILITY", "Politics, political leaders and representatives; government; nobility"),
("POSSESSION", "Concepts of possession; items which tend to belong to people"),
("RELIGION, MYSTICISM AND MYTHOLOGY", "Religions, faiths, beliefs, mysticism, mythological creatures, myths"),
("SEX", "Sexual connotation; sexual activities; sexual reproduction; sexology"),
("SMELL AND PERFUME", "Sense of smell; good and bad smells"),
("SOLID, LIQUID AND GAS MATTER", "The states of matter (solid, liquid, gas)"),
("SPACE AND TOUCH", "Concepts of space and the sense of touch; dimensionality, proprioception (sense of position and movement) and haptic perception"),
("SPORT, GAMES AND RECREATION", "Sports, games and video games, recreation (pastimes, hobbies, etc.)"),
("TASKS, JOBS, ROUTINE AND EVALUATION", "Tasks, chores, activities, jobs; evaluation, validation, marking, checking, correcting"),
("TEXTILE, FASHION AND CLOTHING", "Fabric, clothes, clothing, footwear, lifestyle, accessories, makeup, hairstyle, fashion, fashion designers"),
("TIME", "Temporal concepts; time; events"),
("TRANSPORT AND TRAVEL", "Transport, modes of transportation, transportation activities; travels, trips, traveling, travelers, tourism"),
("VISION AND VISUAL", "Visual concepts (visual perception, sight, colors, visibility, except spatial concepts)"),
("WARFARE, VIOLENCE AND DEFENSE", "Wars, battles, warfare, physical violence, personal and country defense, secret agencies"),
]

def BN_slugify(name):
    return name.replace(', ', '_').replace(' ', '_')

def BN_format(domain):
    # return {'name': BN_slugify(domain[0]), 'label': domain[0]}
    return BN_slugify(domain[0])
