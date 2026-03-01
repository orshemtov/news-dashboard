"""Curated catalog of Telegram news channels for suggestion engine.

Each entry has a username, display name, description (used for embedding),
language, and category tags. Descriptions should be rich enough for the
embedding model to compute meaningful similarity against user article vectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CatalogChannel:
    username: str
    name: str
    description: str
    language: str  # primary language: he, ar, en, ru, ...
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Catalog — ~80 channels covering Middle-East security, geopolitics,
# Israeli news, Arab world, international affairs, tech, and more.
# ---------------------------------------------------------------------------

CHANNEL_CATALOG: list[CatalogChannel] = [
    # ── Israeli Security & Military ────────────────────────────────────
    CatalogChannel(
        username="abualiexpress",
        name="Abu Ali Express",
        description="Real-time security and military updates from Israel and the Middle East. Covers IDF operations, rocket alerts, border incidents, and breaking security developments in Hebrew and Arabic.",
        language="he",
        tags=["security", "military", "israel", "breaking"],
    ),
    CatalogChannel(
        username="salehdesk1",
        name="Saleh Desk",
        description="Security and military news desk covering Israel, Gaza, Lebanon, and regional conflicts. Arabic and Hebrew language intelligence and field reports.",
        language="he",
        tags=["security", "military", "intelligence"],
    ),
    CatalogChannel(
        username="intikihabat",
        name="Intikihabat",
        description="Israeli intelligence and security analysis. OSINT reports on military operations, defense technology, and regional threat assessments.",
        language="he",
        tags=["intelligence", "osint", "security"],
    ),
    CatalogChannel(
        username="aboramisrael",
        name="Abu Rami Israel",
        description="Israeli military and security news. Real-time updates on IDF operations, rocket attacks, and security incidents along Israel's borders.",
        language="he",
        tags=["security", "military", "breaking"],
    ),
    CatalogChannel(
        username="red_alert_israel",
        name="Red Alert Israel",
        description="Automated rocket alert notifications for Israel. Real-time missile and drone warnings, Iron Dome interceptions, and shelter alerts by region.",
        language="he",
        tags=["alerts", "rockets", "security", "realtime"],
    ),
    CatalogChannel(
        username="cumtaofficial",
        name="CUMTA",
        description="Community of unified military threat analysis. Tracking armed groups, militia movements, and threat intelligence across the Middle East.",
        language="en",
        tags=["military", "threat-analysis", "osint"],
    ),
    CatalogChannel(
        username="IsraelWarUpdates",
        name="Israel War Updates",
        description="Comprehensive English-language coverage of Israel's military operations, conflict developments, casualty reports, and ceasefire negotiations.",
        language="en",
        tags=["war", "military", "israel", "conflict"],
    ),
    CatalogChannel(
        username="SouthFirstResponders",
        name="South First Responders",
        description="First responder updates from southern Israel. Emergency incidents, rescue operations, and community alerts from the Gaza border region.",
        language="he",
        tags=["emergency", "first-responders", "south-israel"],
    ),
    # ── Israeli Politics & General News ────────────────────────────────
    CatalogChannel(
        username="amitsegal",
        name="Amit Segal",
        description="Leading Israeli political journalist. Breaking political news, coalition dynamics, Knesset developments, and government policy analysis in Hebrew.",
        language="he",
        tags=["politics", "israel", "commentary"],
    ),
    CatalogChannel(
        username="rotter_HaMadlif",
        name="Rotter HaMadlif",
        description="Breaking news leaks and early reports from Israel. Unfiltered news updates covering politics, security, crime, and society.",
        language="he",
        tags=["breaking", "leaks", "israel"],
    ),
    CatalogChannel(
        username="yinonews",
        name="Yinon News",
        description="Israeli news and current affairs magazine. Covers politics, economy, social issues, and investigative journalism in Hebrew.",
        language="he",
        tags=["news", "politics", "society"],
    ),
    CatalogChannel(
        username="kann11",
        name="Kann News",
        description="Israel's public broadcasting corporation. Official news updates covering politics, economy, defense, and cultural affairs.",
        language="he",
        tags=["news", "broadcast", "official"],
    ),
    CatalogChannel(
        username="newsaborN12",
        name="N12 News",
        description="Channel 12 Israeli news network. Breaking news, political analysis, investigative reports, and major national stories.",
        language="he",
        tags=["news", "broadcast", "breaking"],
    ),
    CatalogChannel(
        username="News_Ynet",
        name="Ynet News",
        description="Ynet digital news platform. Comprehensive Israeli news coverage including security, politics, economy, health, and entertainment.",
        language="he",
        tags=["news", "digital", "comprehensive"],
    ),
    CatalogChannel(
        username="waborisa13",
        name="Channel 13 News",
        description="Reshet 13 Israeli television news. Political coverage, defense reporting, economic analysis, and investigative journalism.",
        language="he",
        tags=["news", "broadcast", "politics"],
    ),
    CatalogChannel(
        username="iaborisrai24",
        name="Israel 24 News",
        description="24/7 Israeli news channel covering politics, security, economy, technology, and cultural developments in real time.",
        language="he",
        tags=["news", "24-7", "comprehensive"],
    ),
    CatalogChannel(
        username="calcalistnews",
        name="Calcalist",
        description="Israel's leading business and financial news. Stock market updates, startup ecosystem, tech industry, real estate, and economic policy analysis.",
        language="he",
        tags=["business", "finance", "tech", "economy"],
    ),
    CatalogChannel(
        username="globaborses",
        name="Globes",
        description="Israeli business news and financial analysis. Corporate news, market trends, banking, investment, and macroeconomic reporting.",
        language="he",
        tags=["business", "finance", "markets"],
    ),
    CatalogChannel(
        username="WallaNews",
        name="Walla News",
        description="Walla! News portal. Broad Israeli news coverage including breaking news, politics, sports, entertainment, and lifestyle.",
        language="he",
        tags=["news", "portal", "comprehensive"],
    ),
    CatalogChannel(
        username="haboraaretz",
        name="Haaretz",
        description="Haaretz newspaper. In-depth political analysis, investigative journalism, opinion columns, and coverage of Israeli-Palestinian affairs.",
        language="he",
        tags=["news", "investigative", "opinion", "politics"],
    ),
    # ── Arab World & Regional ──────────────────────────────────────────
    CatalogChannel(
        username="arabworld301news",
        name="301 Arab World",
        description="Arab world news and analysis in Hebrew. Covers political developments, conflicts, and social changes across the Arab Middle East and North Africa.",
        language="he",
        tags=["arab-world", "mena", "analysis"],
    ),
    CatalogChannel(
        username="AlJaboritazeerArabic",
        name="Al Jazeera Arabic",
        description="Al Jazeera Arabic news network. International and Middle Eastern news coverage, investigative reports, and political analysis in Arabic.",
        language="ar",
        tags=["news", "international", "arab-world"],
    ),
    CatalogChannel(
        username="AlArabiya",
        name="Al Arabiya",
        description="Al Arabiya news network. Pan-Arab and international news, business reports, and cultural coverage in Arabic.",
        language="ar",
        tags=["news", "pan-arab", "business"],
    ),
    CatalogChannel(
        username="BBCArabic",
        name="BBC Arabic",
        description="BBC Arabic service. International news, analysis, and features covering the Middle East, Africa, and world events in Arabic.",
        language="ar",
        tags=["news", "international", "bbc"],
    ),
    CatalogChannel(
        username="syria_updates",
        name="Syria Updates",
        description="Coverage of the Syrian civil war and reconstruction. Military operations, humanitarian issues, refugee crisis, and political negotiations.",
        language="ar",
        tags=["syria", "conflict", "humanitarian"],
    ),
    CatalogChannel(
        username="YemenNews24",
        name="Yemen News",
        description="Yemen conflict and political updates. Houthi developments, coalition operations, humanitarian crisis, and peace process coverage.",
        language="ar",
        tags=["yemen", "conflict", "houthi"],
    ),
    CatalogChannel(
        username="IraqiNewsNet",
        name="Iraqi News Network",
        description="Iraqi political and security news. Parliament updates, militia activities, oil economy, and reconstruction efforts.",
        language="ar",
        tags=["iraq", "politics", "security"],
    ),
    CatalogChannel(
        username="LebanonDebate",
        name="Lebanon Debate",
        description="Lebanese political debate and news. Hezbollah coverage, economic crisis, sectarian politics, and Beirut society updates.",
        language="ar",
        tags=["lebanon", "hezbollah", "politics"],
    ),
    CatalogChannel(
        username="EgyptForward",
        name="Egypt Forward",
        description="Egyptian news and political analysis. Sisi government policies, economy, Suez Canal, military developments, and social movements.",
        language="ar",
        tags=["egypt", "politics", "economy"],
    ),
    # ── Iran & Proxies ─────────────────────────────────────────────────
    CatalogChannel(
        username="IranIntl",
        name="Iran International",
        description="Iran International news. Coverage of Iranian politics, protests, IRGC activities, nuclear program, and sanctions impact.",
        language="en",
        tags=["iran", "politics", "nuclear", "sanctions"],
    ),
    CatalogChannel(
        username="IranPressNews",
        name="Iran Press",
        description="Iranian state-adjacent media. Government statements, military parades, proxy activities, and Persian Gulf security developments.",
        language="en",
        tags=["iran", "state-media", "military"],
    ),
    CatalogChannel(
        username="PressTV",
        name="Press TV",
        description="Iranian English-language state broadcaster. Official Iranian perspective on international affairs, Middle East conflicts, and Western politics.",
        language="en",
        tags=["iran", "state-media", "international"],
    ),
    CatalogChannel(
        username="HezbollahWatch",
        name="Hezbollah Watch",
        description="Monitoring Hezbollah activities in Lebanon and the region. Military capabilities, political influence, Iranian support networks, and conflict escalation.",
        language="en",
        tags=["hezbollah", "lebanon", "proxy", "monitoring"],
    ),
    # ── OSINT & Intelligence ───────────────────────────────────────────
    CatalogChannel(
        username="inabortelligence_faborusion",
        name="Intel Fusion",
        description="Open source intelligence fusion. Military movements, geopolitical analysis, satellite imagery analysis, and conflict mapping.",
        language="en",
        tags=["osint", "intelligence", "geopolitics", "satellite"],
    ),
    CatalogChannel(
        username="osaborintechnical",
        name="OSINT Technical",
        description="Technical open-source intelligence. Digital forensics, geolocating military assets, verification methods, and OSINT tools and techniques.",
        language="en",
        tags=["osint", "technical", "forensics"],
    ),
    CatalogChannel(
        username="GeoConfirmed",
        name="GeoConfirmed",
        description="Geolocation verification of conflict events. Visual evidence analysis, mapping combat footage, and verifying military claims worldwide.",
        language="en",
        tags=["osint", "geolocation", "verification"],
    ),
    CatalogChannel(
        username="militaaborryosint",
        name="Military OSINT",
        description="Military open-source intelligence tracking global armed forces. Equipment identification, troop deployments, and defense industry developments.",
        language="en",
        tags=["osint", "military", "equipment"],
    ),
    CatalogChannel(
        username="ConflictZone_News",
        name="Conflict Zone News",
        description="Real-time conflict zone reporting from active war zones worldwide. Frontline updates, casualty reports, and humanitarian situation monitoring.",
        language="en",
        tags=["conflict", "war", "frontline", "humanitarian"],
    ),
    # ── Geopolitics & International Affairs ────────────────────────────
    CatalogChannel(
        username="MyGPLANET",
        name="MyGPLANET",
        description="Geopolitical news and analysis. Global power dynamics, diplomatic developments, trade wars, international security, and foreign policy analysis.",
        language="en",
        tags=["geopolitics", "diplomacy", "international"],
    ),
    CatalogChannel(
        username="raborussia_intaborel",
        name="Russia Intel",
        description="Russian military and intelligence analysis. Ukraine war coverage, Kremlin politics, Wagner Group, NATO-Russia tensions, and Arctic security.",
        language="en",
        tags=["russia", "ukraine", "military", "intelligence"],
    ),
    CatalogChannel(
        username="UkraineNaborow",
        name="Ukraine Now",
        description="Ukraine war real-time updates. Frontline movements, drone strikes, Western aid deliveries, casualty reports, and ceasefire negotiations.",
        language="en",
        tags=["ukraine", "war", "frontline", "realtime"],
    ),
    CatalogChannel(
        username="ChinaPowerWatch",
        name="China Power Watch",
        description="China's military modernization and geopolitical influence. Taiwan strait tensions, South China Sea, Belt and Road, and US-China competition.",
        language="en",
        tags=["china", "taiwan", "geopolitics", "military"],
    ),
    CatalogChannel(
        username="NATOPressChannel",
        name="NATO Press",
        description="NATO alliance news and press releases. Joint exercises, defense spending, member state commitments, and collective security updates.",
        language="en",
        tags=["nato", "defense", "alliance", "europe"],
    ),
    CatalogChannel(
        username="DiplomaticBriefs",
        name="Diplomatic Briefs",
        description="International diplomacy and UN affairs. Security council resolutions, peace negotiations, sanctions regimes, and multilateral agreements.",
        language="en",
        tags=["diplomacy", "un", "international-law"],
    ),
    # ── US & Western Politics ──────────────────────────────────────────
    CatalogChannel(
        username="politaborico_us",
        name="Politico US",
        description="American politics and policy. White House, Congress, elections, lobbying, and legislative analysis from Washington DC.",
        language="en",
        tags=["us-politics", "congress", "elections"],
    ),
    CatalogChannel(
        username="BBCWorld",
        name="BBC World",
        description="BBC World Service. Global news, analysis, and features covering international affairs, science, culture, and business in English.",
        language="en",
        tags=["news", "international", "bbc", "world"],
    ),
    CatalogChannel(
        username="reuters_world",
        name="Reuters World",
        description="Reuters global news wire. Breaking international news, financial markets, political developments, and enterprise reporting worldwide.",
        language="en",
        tags=["news", "wire", "international", "finance"],
    ),
    CatalogChannel(
        username="AFP_en",
        name="AFP English",
        description="Agence France-Presse English service. International news, photo journalism, fact-checking, and investigative reports from global bureaus.",
        language="en",
        tags=["news", "wire", "international", "fact-check"],
    ),
    # ── Russian-language (Israel & region) ─────────────────────────────
    CatalogChannel(
        username="israelaborru",
        name="Israel in Russian",
        description="Israeli news in Russian language. Immigration, community affairs, security updates, and political analysis for Russian-speaking Israelis.",
        language="ru",
        tags=["israel", "russian", "community"],
    ),
    CatalogChannel(
        username="detaborector_ru",
        name="Detektор",
        description="Russian-language investigative news. Corruption investigations, political analysis, and in-depth reporting on Russian and post-Soviet affairs.",
        language="ru",
        tags=["investigative", "russia", "corruption"],
    ),
    CatalogChannel(
        username="medaboruza_live",
        name="Meduza Live",
        description="Independent Russian journalism. Kremlin politics, war coverage, civil liberties, and analysis of Russian state propaganda.",
        language="ru",
        tags=["russia", "independent", "politics"],
    ),
    # ── Technology & Cyber ─────────────────────────────────────────────
    CatalogChannel(
        username="CyberSecIsrael",
        name="CyberSec Israel",
        description="Israeli cybersecurity industry news. Startup ecosystem, threat research, vulnerability disclosures, and national cyber defense updates.",
        language="en",
        tags=["cybersecurity", "israel", "tech", "startups"],
    ),
    CatalogChannel(
        username="HackeraborNews",
        name="Hacker News Feed",
        description="Technology and startup news. Software engineering, AI/ML developments, Silicon Valley, venture capital, and tech industry analysis.",
        language="en",
        tags=["tech", "startups", "ai", "engineering"],
    ),
    CatalogChannel(
        username="TheRecaborord",
        name="The Record",
        description="Cybersecurity news by Recorded Future. Data breaches, ransomware attacks, nation-state hacking, and cyber policy developments.",
        language="en",
        tags=["cybersecurity", "breaches", "hacking"],
    ),
    CatalogChannel(
        username="AIandDefense",
        name="AI & Defense",
        description="Artificial intelligence applications in defense and military. Autonomous weapons, drone AI, battlefield analytics, and defense tech innovation.",
        language="en",
        tags=["ai", "defense", "military-tech", "drones"],
    ),
    # ── Economy & Energy ───────────────────────────────────────────────
    CatalogChannel(
        username="OilPriceNet",
        name="Oil Price News",
        description="Global oil and energy market news. OPEC decisions, crude oil prices, natural gas, renewable energy, and energy geopolitics.",
        language="en",
        tags=["energy", "oil", "opec", "markets"],
    ),
    CatalogChannel(
        username="CryptoMidEast",
        name="Crypto Middle East",
        description="Cryptocurrency and blockchain developments in the Middle East. Bitcoin regulation, digital assets, fintech innovation, and Gulf state crypto adoption.",
        language="en",
        tags=["crypto", "blockchain", "fintech", "middle-east"],
    ),
    CatalogChannel(
        username="GulfBizNews",
        name="Gulf Business News",
        description="Business news from the Gulf states. Saudi Vision 2030, UAE economy, Qatari investments, and Persian Gulf trade and commerce.",
        language="en",
        tags=["gulf", "business", "saudi", "uae"],
    ),
    # ── Humanitarian & NGO ─────────────────────────────────────────────
    CatalogChannel(
        username="ABORUNRWA",
        name="UNRWA Updates",
        description="United Nations Relief and Works Agency. Palestinian refugee services, Gaza humanitarian aid, West Bank education, and agency funding updates.",
        language="en",
        tags=["humanitarian", "un", "palestine", "refugees"],
    ),
    CatalogChannel(
        username="ICRCaborChannel",
        name="ICRC Updates",
        description="International Committee of the Red Cross. Humanitarian law, conflict zone aid, prisoner of war visits, and disaster relief operations worldwide.",
        language="en",
        tags=["humanitarian", "icrc", "aid", "law"],
    ),
    CatalogChannel(
        username="MSFupdates",
        name="MSF / Doctors Without Borders",
        description="Medecins Sans Frontieres updates. Medical humanitarian aid in war zones, disease outbreaks, refugee health, and emergency response missions.",
        language="en",
        tags=["humanitarian", "medical", "msf", "health"],
    ),
    # ── Turkish & Broader Region ───────────────────────────────────────
    CatalogChannel(
        username="TurkeyAffairs",
        name="Turkey Affairs",
        description="Turkish politics and foreign policy. Erdogan government, Kurdish issue, Syria operations, NATO membership, and Turkey-EU relations.",
        language="en",
        tags=["turkey", "politics", "nato", "kurds"],
    ),
    CatalogChannel(
        username="NorthAfricaPost",
        name="North Africa Post",
        description="North African politics and society. Libya conflict, Tunisia democracy, Morocco diplomacy, Algeria energy, and Sahel security.",
        language="en",
        tags=["north-africa", "libya", "sahel", "politics"],
    ),
    CatalogChannel(
        username="AfricaSecWatch",
        name="Africa Security Watch",
        description="African security and conflict monitoring. Sahel jihadism, East Africa terrorism, peacekeeping operations, and continental defense cooperation.",
        language="en",
        tags=["africa", "security", "terrorism", "peacekeeping"],
    ),
    # ── Niche / Specialty ──────────────────────────────────────────────
    CatalogChannel(
        username="NukeWatch",
        name="Nuclear Watch",
        description="Nuclear weapons and nonproliferation monitoring. Iran nuclear deal, North Korea missiles, arms control treaties, and nuclear security policy.",
        language="en",
        tags=["nuclear", "nonproliferation", "arms-control"],
    ),
    CatalogChannel(
        username="MaritimeSecAlert",
        name="Maritime Security Alert",
        description="Maritime security and naval affairs. Houthi Red Sea attacks, shipping disruptions, piracy, naval deployments, and Strait of Hormuz tensions.",
        language="en",
        tags=["maritime", "shipping", "naval", "houthi"],
    ),
    CatalogChannel(
        username="DroneWarfare",
        name="Drone Warfare Watch",
        description="UAV and drone warfare developments. Military drone strikes, counter-drone technology, autonomous systems, and drone proliferation tracking.",
        language="en",
        tags=["drones", "uav", "military-tech", "autonomy"],
    ),
    CatalogChannel(
        username="SanctionsTracker",
        name="Sanctions Tracker",
        description="International sanctions monitoring. US, EU, and UN sanctions regimes, designated entities, compliance updates, and sanctions evasion tracking.",
        language="en",
        tags=["sanctions", "compliance", "policy"],
    ),
    CatalogChannel(
        username="RefugeeWatch",
        name="Refugee Watch",
        description="Global refugee and migration crisis monitoring. Displacement statistics, asylum policies, border developments, and resettlement programs.",
        language="en",
        tags=["refugees", "migration", "humanitarian"],
    ),
    CatalogChannel(
        username="ClimateSecDaily",
        name="Climate Security Daily",
        description="Climate change and security nexus. Water scarcity conflicts, climate migration, extreme weather impacts on stability, and green defense initiatives.",
        language="en",
        tags=["climate", "security", "environment"],
    ),
    CatalogChannel(
        username="SpaceDefenseNet",
        name="Space Defense Network",
        description="Space militarization and defense. Satellite warfare, anti-satellite weapons, space force developments, and orbital security threats.",
        language="en",
        tags=["space", "defense", "satellite", "military-tech"],
    ),
]


def get_catalog_excluding(existing_usernames: set[str]) -> list[CatalogChannel]:
    """Return catalog channels that are not already in the user's sources."""
    existing_lower = {u.lower() for u in existing_usernames}
    return [ch for ch in CHANNEL_CATALOG if ch.username.lower() not in existing_lower]
