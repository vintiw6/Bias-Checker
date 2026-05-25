import os
import csv
import json
import hashlib
from datetime import datetime

# Base fallback scored dataset
DEMO_ARTICLES = [
    {
        "outlet": "The Hindu",
        "headline": "Supreme Court requests Central Government response on new environment guidelines",
        "url": "https://www.thehindu.com/sci-tech/energy-and-environment/supreme-court-requests-central-government-response-on-new-environment-guidelines/article99218210.ece",
        "body": "The Supreme Court on Monday requested a response from the Central Government regarding the implementation of the new environment guidelines. The bench, led by the Chief Justice, was hearing petitions challenging the regulatory framework. Critics argue the new rules dilute protection measures, while the government maintains they streamline operations and reduce bureaucratic delays. The Court has scheduled the next hearing for three weeks from now.",
        "published_at": "2026-05-24T12:00:00Z",
        "lean": "center-left",
        "emotion": 0.15,
        "clickbait": 12.5,
        "entity_json": '{"Opposition": -0.1, "BJP": 0.0}'
    },
    {
        "outlet": "Scroll",
        "headline": "Opposition slams government as SC issues notice on environment guidelines",
        "url": "https://scroll.in/article/109281/opposition-slams-government-as-sc-issues-notice-on-environment-guidelines",
        "body": "The Opposition parties on Tuesday launched a scathing attack on the Central Government after the Supreme Court issued a notice regarding the controversial new environment guidelines. Spokespersons for the Congress argued that the government is catering to corporate interests at the cost of public health and ecological safety. They demanded immediate suspension of the guidelines pending a thorough judicial audit.",
        "published_at": "2026-05-24T13:15:00Z",
        "lean": "left",
        "emotion": 0.72,
        "clickbait": 48.0,
        "entity_json": '{"Congress": 0.6, "Opposition": 0.7, "BJP": -0.85, "Modi": -0.8}'
    },
    {
        "outlet": "Indian Express",
        "headline": "SC issues notice to Centre on new environmental norms",
        "url": "https://indianexpress.com/article/india/sc-issues-notice-to-centre-on-new-environmental-norms-998231/",
        "body": "The Supreme Court has issued a notice to the Centre on petitions contesting the newly notified environmental norms. Petitions filed by environmental groups claim the changes will lead to deforestation and destruction of ecologically sensitive areas. The Central Government defended the guidelines, stating they incorporate modern mitigation tech and strengthen enforcement mechanisms. The court has given the government four weeks to reply.",
        "published_at": "2026-05-24T11:45:00Z",
        "lean": "center",
        "emotion": 0.18,
        "clickbait": 8.5,
        "entity_json": '{"BJP": 0.1, "Opposition": -0.1}'
    },
    {
        "outlet": "The Print",
        "headline": "Activists welcome SC notice to Centre on environmental regulations",
        "url": "https://theprint.in/india/governance/activists-welcome-sc-notice-to-centre-on-environmental-regulations/2091811/",
        "body": "Environmental activists and civil society organizations have welcomed the Supreme Court decision to issue a notice to the Centre on environmental regulations. Activists stated that the judicial intervention provides a crucial check on unchecked industrial expansion. The BJP spokesperson countered that the rules balance sustainable growth with economic expansion, asserting that the party remains committed to conservation.",
        "published_at": "2026-05-24T14:30:00Z",
        "lean": "center",
        "emotion": 0.35,
        "clickbait": 22.0,
        "entity_json": '{"BJP": -0.2, "Modi": -0.1}'
    },
    {
        "outlet": "OpIndia",
        "headline": "Historic digital transformation as Modi government launches rural tech drive",
        "url": "https://www.opindia.com/2026/05/historic-digital-transformation-as-modi-government-launches-rural-tech-drive/",
        "body": "In a landmark decision, Prime Minister Narendra Modi launched a massive digital infrastructure drive for rural India. The BJP hailed the initiative as a historic turning point that will empower millions of rural citizens. The digital transformation program is set to provide high-speed connectivity to over 250,000 villages, bridging the technology gap and boosting local economies. Supporters call it a visionary move.",
        "published_at": "2026-05-23T08:00:00Z",
        "lean": "right",
        "emotion": 0.68,
        "clickbait": 55.0,
        "entity_json": '{"Modi": 0.9, "BJP": 0.8, "Opposition": -0.7}'
    },
    {
        "outlet": "OpIndia",
        "headline": "PM Modi launches massive tech infrastructure initiative for rural India",
        "url": "https://www.opindia.com/2026/05/pm-modi-launches-massive-tech-infrastructure-initiative-for-rural-india/",
        "body": "Prime Minister Modi has unveiled a monumental rural tech infrastructure initiative, aiming to provide high-speed internet and e-governance to every village. The BJP leadership praised Modi for his unwavering dedication to rural upliftment, pointing out that previous Congress-led administrations ignored digital access for villages. Citizens across rural districts expressed immense joy and gratitude.",
        "published_at": "2026-05-23T09:10:00Z",
        "lean": "right",
        "emotion": 0.82,
        "clickbait": 68.0,
        "entity_json": '{"Modi": 0.95, "BJP": 0.9, "Congress": -0.85, "Opposition": -0.8}'
    },
    {
        "outlet": "The Wire",
        "headline": "Concerns grow over digital divide as government pushes rural digital program",
        "url": "https://thewire.in/government/concerns-grow-over-digital-divide-as-government-pushes-rural-digital-program",
        "body": "As the Central Government pushes its ambitious rural digital program, tech policy experts and opposition leaders are raising concerns over a widening digital divide. The Wire's analysis reveals that most rural schools lack power supply, making digital access a distant dream. Congress leaders accused the government of running a public relations campaign instead of addressing core infrastructure failures.",
        "published_at": "2026-05-23T10:30:00Z",
        "lean": "left",
        "emotion": 0.55,
        "clickbait": 35.0,
        "entity_json": '{"Modi": -0.75, "BJP": -0.7, "Congress": 0.5, "Opposition": 0.6}'
    },
    {
        "outlet": "Newslaundry",
        "headline": "New rural tech initiative fails to address digital divide, critics say",
        "url": "https://www.newslaundry.com/2026/05/23/new-rural-tech-initiative-fails-to-address-digital-divide-critics-say",
        "body": "Critics and independent analysts have cast doubt on the newly announced rural tech initiative, saying it fails to address structural barriers in connectivity. A detailed study shows that internet penetration remains low in tribal areas, and local leaders say the government's plans are detached from ground reality. The BJP administration has denied these claims, asserting that the rollouts are on track.",
        "published_at": "2026-05-23T11:45:00Z",
        "lean": "left",
        "emotion": 0.48,
        "clickbait": 42.0,
        "entity_json": '{"BJP": -0.6, "Opposition": 0.4}'
    },
    {
        "outlet": "Swarajya",
        "headline": "Union Budget 2026 wins praise for pro-growth reforms amidst economic headwinds",
        "url": "https://swarajyamag.com/economy/union-budget-2026-wins-praise-for-pro-growth-reforms-amidst-economic-headwinds",
        "body": "The recently presented Union Budget 2026 has won widespread acclaim from industry captains and financial analysts for its bold pro-growth reforms. Swarajya editors note that the budget successfully tackles inflation while offering strong incentives for local manufacturing under the Modi government's Make in India initiative. Supporters call it a masterclass in macroeconomic management.",
        "published_at": "2026-05-22T06:30:00Z",
        "lean": "right",
        "emotion": 0.70,
        "clickbait": 50.0,
        "entity_json": '{"Modi": 0.85, "BJP": 0.8, "Opposition": -0.5}'
    },
    {
        "outlet": "The Print",
        "headline": "Budget 2026: A balanced approach to growth amid global inflation concerns",
        "url": "https://theprint.in/economy/budget-2026-a-balanced-approach-to-growth-amid-global-inflation-concerns/208810/",
        "body": "Finance Minister presented Budget 2026 with a balanced blueprint to drive growth while keeping a firm lid on inflation. Industry associations welcomed the capital expenditure increase, though some economists caution that tax relief for the middle class is marginal. Congress and other opposition parties slammed the budget as a document of high promises with little allocation for agriculture.",
        "published_at": "2026-05-22T07:15:00Z",
        "lean": "center",
        "emotion": 0.28,
        "clickbait": 15.0,
        "entity_json": '{"Opposition": -0.2, "Congress": -0.2, "BJP": 0.2, "Modi": 0.1}'
    },
    {
        "outlet": "Scroll",
        "headline": "Economists raise concerns over inflation as new budget overlooks welfare spending",
        "url": "https://scroll.in/article/109110/economists-raise-concerns-over-inflation-as-new-budget-overlooks-welfare-spending",
        "body": "Several prominent economists have raised alarm bells over inflation risks in the Union Budget 2026. The budget has come under fire for cutting spending on critical social welfare programs like MGNREGA. Opposition leaders including Rahul Gandhi accused the Prime Minister of catering to billionaires while leaving the rural poor to struggle against skyrocketing food prices.",
        "published_at": "2026-05-22T08:00:00Z",
        "lean": "left",
        "emotion": 0.65,
        "clickbait": 45.0,
        "entity_json": '{"Rahul Gandhi": 0.75, "Congress": 0.6, "Modi": -0.85, "Opposition": 0.7}'
    },
    {
        "outlet": "NDTV",
        "headline": "Budget 2026: Key takeaways for industry, middle class, and taxpayers",
        "url": "https://www.ndtv.com/business/budget-2026-key-takeaways-for-industry-middle-class-and-taxpayers-9872120",
        "body": "The Union Budget 2026, presented by the Finance Minister, outlines a vision for infrastructure expansion and fiscal consolidation. Key highlights include income tax rebate adjustments, increased allocation for digital systems, and capital expenditures. While the BJP hailed the budget as forward-looking, Opposition parties termed it disappointing for the common man.",
        "published_at": "2026-05-22T06:00:00Z",
        "lean": "center",
        "emotion": 0.20,
        "clickbait": 18.0,
        "entity_json": '{"BJP": 0.2, "Opposition": -0.2}'
    },
    {
        "outlet": "NDTV",
        "headline": "State elections: EC announces new guidelines for candidates and parties",
        "url": "https://www.ndtv.com/india-news/state-elections-ec-announces-new-guidelines-for-candidates-and-parties-9872134",
        "body": "The Election Commission has announced a fresh set of guidelines for the upcoming state assembly elections. The rules focus on keeping campaign spending in check, regulating digital advertisements, and ensuring security at all polling booths. Representatives of the BJP, Congress, and AAP stated they are reviewing the guidelines and will ensure full compliance during campaigning.",
        "published_at": "2026-05-21T10:00:00Z",
        "lean": "center",
        "emotion": 0.12,
        "clickbait": 10.0,
        "entity_json": '{"BJP": 0.0, "Congress": 0.0, "AAP": 0.0}'
    },
    {
        "outlet": "Newslaundry",
        "headline": "Elections 2026: AAP alleges BJP utilizing official machinery in state campaigns",
        "url": "https://www.newslaundry.com/2026/05/21/elections-2026-aap-alleges-bjp-utilizing-official-machinery-in-state-campaigns",
        "body": "The Aam Aadmi Party has formally written to the Election Commission, alleging that the ruling BJP is using official state machinery to boost its assembly election campaign. Kejriwal claimed that government offices are being decorated with party advertisements, in direct violation of the model code of conduct. The BJP has rubbished the allegations, calling them a stunt by AAP.",
        "published_at": "2026-05-21T11:15:00Z",
        "lean": "left",
        "emotion": 0.58,
        "clickbait": 46.0,
        "entity_json": '{"AAP": 0.5, "Kejriwal": 0.6, "BJP": -0.75}'
    },
    {
        "outlet": "Swarajya",
        "headline": "BJP launches door-to-door micro-campaigning to outpace rivals in assembly polls",
        "url": "https://swarajyamag.com/politics/bjp-launches-door-to-door-micro-campaigning-to-outpace-rivals-in-assembly-polls",
        "body": "The BJP has deployed thousands of grassroot karyakartas for an intensive door-to-door campaign in preparation for the upcoming assembly elections. The party aims to showcase Amit Shah's security achievements and Modi's developmental benefits directly to families. Political analysts note that the BJP's organizational machine is running at peak efficiency, far ahead of a fragmented Opposition.",
        "published_at": "2026-05-21T09:30:00Z",
        "lean": "right",
        "emotion": 0.52,
        "clickbait": 30.0,
        "entity_json": '{"BJP": 0.8, "Amit Shah": 0.75, "Modi": 0.8, "Opposition": -0.6}'
    },
    {
        "outlet": "The Hindu",
        "headline": "Opposition parties hold joint meeting to coordinate campaign strategies",
        "url": "https://www.thehindu.com/news/national/opposition-parties-hold-joint-meeting-to-coordinate-campaign-strategies/article99216742.ece",
        "body": "Leaders of major opposition parties, including the Congress and TMC, held a joint meeting in New Delhi to finalize their coordination strategy for the upcoming assembly elections. Mamata Banerjee and Rahul Gandhi stressed the need for a unified front to take on the BJP machinery. They agreed to coordinate joint rallies and divide candidate configurations to avoid vote splits.",
        "published_at": "2026-05-21T14:30:00Z",
        "lean": "center-left",
        "emotion": 0.25,
        "clickbait": 12.0,
        "entity_json": '{"Congress": 0.4, "TMC": 0.4, "Mamata": 0.5, "Rahul Gandhi": 0.5, "BJP": -0.2}'
    }
]

def generate_id(url: str) -> str:
    """Generates a unique MD5 hash for the given URL."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()

def generate_demo_scraped():
    """Generates scraped_articles.csv in the data directory."""
    os.makedirs("data", exist_ok=True)
    scraped_csv = os.path.join("data", "scraped_articles.csv")
    
    with open(scraped_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "outlet", "headline", "url", "body", "published_at", "scraped_at", "lean"])
        writer.writeheader()
        for art in DEMO_ARTICLES:
            writer.writerow({
                "id": generate_id(art["url"]),
                "outlet": art["outlet"],
                "headline": art["headline"],
                "url": art["url"],
                "body": art["body"],
                "published_at": art["published_at"],
                "scraped_at": datetime.utcnow().isoformat(),
                "lean": art["lean"]
            })
    print(f"Generated {len(DEMO_ARTICLES)} fallback scraped articles in {scraped_csv}")

def generate_demo_scored():
    """Generates scored_articles.csv in the data directory."""
    os.makedirs("data", exist_ok=True)
    scored_csv = os.path.join("data", "scored_articles.csv")
    
    with open(scored_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "outlet", "headline", "url", "body", "published_at", "scraped_at", "lean", "emotion", "clickbait", "entity_json"
        ])
        writer.writeheader()
        for art in DEMO_ARTICLES:
            writer.writerow({
                "id": generate_id(art["url"]),
                "outlet": art["outlet"],
                "headline": art["headline"],
                "url": art["url"],
                "body": art["body"],
                "published_at": art["published_at"],
                "scraped_at": datetime.utcnow().isoformat(),
                "lean": art["lean"],
                "emotion": art["emotion"],
                "clickbait": art["clickbait"],
                "entity_json": art["entity_json"]
            })
    print(f"Generated {len(DEMO_ARTICLES)} fallback scored articles in {scored_csv}")

if __name__ == "__main__":
    generate_demo_scraped()
    generate_demo_scored()
