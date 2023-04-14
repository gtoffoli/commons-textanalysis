from django.utils.translation import gettext_lazy as _

bn_domains = [
("ART, ARCHITECTURE, AND ARCHAEOLOGY", _("Art (painting, visual arts, sculpture, etc. except for music, dance, poetry, photography and theatre)), architecture (construction, buildings, etc.)), archaeology (sites, finds etc.)), prehistory")),
("BIOLOGY", _("Biology; animals, plants and their classifications, microorganisms")),
("BUSINESS, INDUSTRY AND FINANCE", _("Business, industry, economy, finance, management, money")),
("CHEMISTRY AND MINERALOGY", _("Chemistry, compounds, chemicals, minerals, mineralogy")),
("COMMUNICATION AND TELECOMMUNICATION", _("Communication (oral, written, etc.) and telecommunication (telegraph, telephone, TV, radio, fax, Internet, etc.) means")),
("COMPUTING", _("Computer science, computing, hardware and software")),
("CRAFT, ENGINEERING AND TECHNOLOGY", _("Crafts (handicraft, skilled work, etc.)), engineering, technology")),
("CULTURE, ANTHROPOLOGY AND SOCIETY", _("Concepts affecting local and global culture and society; social behavior, trends, norms and expectations in human society; anthropology")),
("EDUCATION AND SCIENCE", _("Education, teaching, students; science and general scientific concepts (specific concepts go to the various domains: mathematics, physics, astronomy, biology, chemistry, geology, computing, etc.)")),
("EMOTIONS AND FEELINGS", _("Feelings, emotions, emotional states and reactions")),
("ENVIRONMENT AND METEOROLOGY", _("Natural environment and its preservation; ecology; natural events (fires, rains, typhoons, etc.); meteorology, weather conditions")),
("FARMING, FISHING AND HUNTING", _("Farming, agriculture; plant cultivation, livestock raising; fishing; hunting")),
("FOOD, DRINK AND TASTE", _("Food, drinks, flavors, sense of taste; eating places (bars, pubs, restaurants)), food events")),
("GEOGRAPHY, GEOLOGY AND PLACES", _("Geography and geographical concepts (continents, countries, regions, provinces, cities, towns, villages, rivers, hills, mountains, plains, etc.); geology and geological concepts (solid Earth, rocks, geological processes, earthquakes, volcanos, etc.); geophysics; places")),
("HEALTH AND MEDICINE", _("Human health and medicine; diseases, drugs and prescriptions; physical, mental and social well-being")),
("HERALDRY, HONORS, AND VEXILLOLOGY", _("Armory, vexillology, honors, ranks")),
("HISTORY", _("Events of the past occurred after the invention of writing systems (for prehistory, see archaeology)")),
("LANGUAGE AND LINGUISTICS", _("Languages, linguistics, idiomatic expressions, phrases")),
("LAW AND CRIME", _("Laws, justice, judges, police, crimes, criminal minds and behaviors")),
("LITERATURE AND THEATRE", _("Literature, authors, books, novels, poetry, plays, theatre")),
("MATHEMATICS AND STATISTICS", _("Mathematics, statistics, numbers, mathematical operations and functions, mathematical and statistical concepts")),
("MEDIA AND PRESS", _("Mass media such as print media (news media, newspapers, magazines, etc.)), publishing, photography, cinema (films, directors, screenwriters, etc.)), broadcasting (radio and television)), and advertising")),
("MUSIC, SOUND AND DANCING", _("Sound, sounds, hearing; music, songs, music artists, composers; dances, dancing, dancers")),
("NAVIGATION AND AVIATION", _("Nautical and aviation concepts: vessels and aircrafts; pilots; sea and air traveling")),
("NUMISMATICS AND CURRENCIES", _("Currencies and their study")),
("PHILOSOPHY, PSYCHOLOGY AND BEHAVIOR", _("Philosophical concepts, philosophers; psychology, psychological concepts; human behavior")),
("PHYSICS AND ASTRONOMY", _("Physics, physical measures and phenomena, matter, its motion and energy; astronomical concepts, celestial objects, space, physical universe")),
("POLITICS, GOVERNMENT AND NOBILITY", _("Politics, political leaders and representatives; government; nobility")),
("POSSESSION", _("Concepts of possession; items which tend to belong to people")),
("RELIGION, MYSTICISM AND MYTHOLOGY", _("Religions, faiths, beliefs, mysticism, mythological creatures, myths")),
("SEX", _("Sexual connotation; sexual activities; sexual reproduction; sexology")),
("SMELL AND PERFUME", _("Sense of smell; good and bad smells")),
("SOLID, LIQUID AND GAS MATTER", _("The states of matter (solid, liquid, gas)")),
("SPACE AND TOUCH", _("Concepts of space and the sense of touch; dimensionality, proprioception (sense of position and movement) and haptic perception")),
("SPORT, GAMES AND RECREATION", _("Sports, games and video games, recreation (pastimes, hobbies, etc.)")),
("TASKS, JOBS, ROUTINE AND EVALUATION", _("Tasks, chores, activities, jobs; evaluation, validation, marking, checking, correcting")),
("TEXTILE, FASHION AND CLOTHING", _("Fabric, clothes, clothing, footwear, lifestyle, accessories, makeup, hairstyle, fashion, fashion designers")),
("TIME", _("Temporal concepts; time; events")),
("TRANSPORT AND TRAVEL", _("Transport, modes of transportation, transportation activities; travels, trips, traveling, travelers, tourism")),
("VISION AND VISUAL", _("Visual concepts (visual perception, sight, colors, visibility, except spatial concepts)")),
("WARFARE, VIOLENCE AND DEFENSE", _("Wars, battles, warfare, physical violence, personal and country defense, secret agencies")),
]

def BN_slugify(name):
    return name.replace(', ', '_').replace(' ', '_')

def BN_format(domain):
    # return {'name': BN_slugify(domain[0]), 'label': domain[0]}
    return BN_slugify(domain[0])
