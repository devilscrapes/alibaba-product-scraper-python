<p align="center"><a href="https://apify.com/DevilScrapes/alibaba-products-scraper"><img src="assets/banner.svg" alt="Alibaba Products Scraper — Python example" width="100%"></a></p>

# Alibaba Product Scraper in Python: supplier search results to JSON and CSV

<p align="center">
<a href="https://apify.com/DevilScrapes/alibaba-products-scraper"><img alt="Run on Apify" src="https://img.shields.io/badge/Run%20on-Apify-DC2626?logo=apify&logoColor=white"></a>
<img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
<a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-0A0606"></a>
<a href="https://github.com/devilscrapes/alibaba-product-scraper-python/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/devilscrapes/alibaba-product-scraper-python/actions/workflows/ci.yml/badge.svg"></a>
</p>

This repository is a small, tested Python client for the **[Alibaba Products Scraper](https://apify.com/DevilScrapes/alibaba-products-scraper)** on Apify. Give it one or more search phrases such as `bluetooth speaker` and it returns a clean table of matching Alibaba.com offers: what the product is called, what it costs per unit, how many units the supplier wants you to buy, who the supplier is, and the link to the listing. The scraping itself runs in the cloud on Apify, so your script stays short and your machine never touches Alibaba directly. You keep the data in plain JSON and CSV, ready for pandas, a spreadsheet or your own database.

> **Actor:** [Alibaba Products Scraper](https://apify.com/DevilScrapes/alibaba-products-scraper) · **Publisher:** [Devil Scrapes](https://apify.com/DevilScrapes) · **Also in JavaScript:** [alibaba-product-scraper-javascript](https://github.com/devilscrapes/alibaba-product-scraper-javascript)

## 🔥 What you get

- **One row per unique product**, carrying the offer's title, its unit price or price band, the MOQ, the seller's company name, the main image and a link to the listing.
- **Many keywords per run**: every search term is paginated on its own, up to the limit you set.
- **No repeat rows**: sponsored offers that reappear on later result pages are removed across the whole run, so you are not billed twice for one product.
- **One bad term never sinks the run**: a term that fails is skipped and logged while the other terms finish.
- **Blocking handled for you**: the Actor detects Alibaba's challenge pages and retries on a fresh session instead of returning an empty page as "no results".
- **Honest zero results**: a term with no matching products succeeds with zero rows instead of failing the run.

## 🎯 Use cases

### Build a sourcing shortlist before you order samples

Run a handful of product phrases, load `results.json` into a DataFrame and sort by the lowest unit price. In a few minutes you have a ranked list of suppliers with their minimum order quantities next to each price, which is the comparison buyers usually do by hand across dozens of browser tabs.

### Track wholesale price movement for a category

Schedule the script with cron or a CI job, write each day's CSV to a dated file and compare the price ranges over time. Because every row carries the search term and a UTC timestamp, a simple `groupby` shows when a category gets cheaper or when new suppliers appear.

### Feed product research into your own tools

Agencies and e-commerce teams can pipe the rows straight into an internal catalog, a PIM or an ERP import job. The output fields are stable, so a mapping written once keeps working from run to run.

### Size a niche for dropshipping or private label

Count how many distinct suppliers list a product, how wide the price spread is and how high the typical MOQ sits. Those three numbers tell you quickly whether a niche is crowded, cheap to enter or locked behind large order sizes.

## ⚡ Quick start

You need an Apify account and an API token from [Console → Settings → Integrations](https://console.apify.com/settings/integrations). Apify's free plan includes monthly usage credit; this Actor's event prices are listed under Pricing below.

```bash
git clone https://github.com/devilscrapes/alibaba-product-scraper-python.git
cd alibaba-product-scraper-python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export APIFY_TOKEN=your_token_here
python main.py                      # uses input.json
python main.py my-input.json --out data --max-charge 2
```

The script starts the [Alibaba Products Scraper](https://apify.com/DevilScrapes/alibaba-products-scraper), waits for it to finish, prints a link to the run in Apify Console and saves every result to `results.json` and `results.csv`. It exits with code 1 and the run's status message if the run fails.

## 🧩 The core call

If you only need the essentials, this is the whole integration. The official `apify-client` package starts the Actor, waits for it to finish and pages through the results for you.

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("DevilScrapes/alibaba-products-scraper").call(run_input={'searchTerms': ['bluetooth speaker'], 'maxResultsPerTerm': 20, 'proxyConfiguration': {'useApifyProxy': True}})
for item in client.dataset(run.default_dataset_id).iterate_items():
    print(item)
```

## 📥 Input

The script sends `input.json` to the Actor unchanged. The bundled file searches one term and stops at 20 products, which keeps a first test run cheap. Add more phrases to `searchTerms` to cover a whole category in a single run.

```json
{
  "searchTerms": [
    "bluetooth speaker"
  ],
  "maxResultsPerTerm": 20,
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

| Field | Type | Required | Default | Allowed values |
|---|---|---|---|---|
| `searchTerms` | array | no | `["bluetooth speaker", "led strip light"]` | — |
| `maxResultsPerTerm` | integer | no | `100` | — |
| `proxyConfiguration` | object | no | `{"useApifyProxy": true}` | — |

## 📤 Output

Every dataset row describes one product offer. Prices are kept exactly as Alibaba shows them, including ranges like `$3.50-5.20`, so nothing is lost in a currency or rounding conversion; parse them in your own code when you need numbers.

| Field | Type | Always present |
|---|---|---|
| `product_id` | string | yes |
| `search_term` | string | yes |
| `title` | string | yes |
| `price` | string or null | no |
| `moq` | string or null | no |
| `supplier_name` | string or null | no |
| `image_url` | string or null | no |
| `product_url` | string | yes |
| `page_number` | integer | yes |
| `scraped_at` | string | yes |

## 💰 Pricing

| Event | Price (USD) |
|---|---|
| Actor start | $0.2 |
| Result item | $0.006 |

Prices as configured on 2026-09-17. The [Actor page](https://apify.com/DevilScrapes/alibaba-products-scraper) always shows the current price. Runs are billed to the Apify account that owns the token. Use `--max-charge` to cap what a single run can cost.

## 🛠️ Working with the data in Python

Here is a starting point for turning the raw rows into a supplier shortlist with pandas (`pip install pandas`). It extracts the lowest price from each price string and the first number from the MOQ, then saves the 20 cheapest offers.

```python
import json
import re

import pandas as pd

rows = pd.DataFrame(json.load(open("results.json", encoding="utf-8")))


def first_number(text):
    match = re.search(r"\d[\d,]*(?:\.\d+)?", text or "")
    return float(match.group().replace(",", "")) if match else None


rows["price_from"] = rows["price"].map(first_number)
rows["moq_units"] = rows["moq"].map(first_number)
shortlist = rows.dropna(subset=["price_from"]).sort_values(["price_from", "moq_units"]).head(20)
shortlist[["title", "supplier_name", "price", "moq", "product_url"]].to_csv("shortlist.csv", index=False)
print(shortlist[["supplier_name", "price", "moq"]].to_string(index=False))
```

## ❓ FAQ

### Do I need an Alibaba account or an Alibaba API key?

No. You only need an Apify API token. The Actor reads Alibaba's public search results, so there is no Alibaba login, partner program or API approval involved.

### Why did a term return fewer products than `maxResultsPerTerm`?

Alibaba repeats many sponsored offers from page to page. The Actor drops those repeats across the entire run and stops paging a term once new pages add nothing new. A smaller count means you reached the real number of distinct offers for that phrase.

### Can I run it from a notebook or a scheduler?

Yes. Import `main` and call `main.main(["input.json", "--out", "data"])` from a notebook, or run `python main.py` from cron, Airflow or a CI job. The exit code is 0 on success and 1 on a failed run, so schedulers can alert on it.

### Does it scrape supplier contact details or product detail pages?

No. It returns what Alibaba shows on its search results pages. Supplier contact data, reviews and login-only buyer prices are out of scope, and 1688.com is a separate site that this Actor does not cover.

## 🧯 Troubleshooting

- **`Set APIFY_TOKEN first`**: export the token in the same shell, or put it in a local `.env` file your shell loads. Never commit it.
- **Run finished with `FAILED` or `ABORTED`**: open the printed Console link; the run log says why. Input validation errors name the field.
- **Fewer rows than expected**: a `--max-charge` cap also limits how many results can be charged. Raise the cap or lower the limits in your input.
- **Something looks wrong in the data**: open an issue on the [Actor page](https://apify.com/DevilScrapes/alibaba-products-scraper) so the maintainers see it.

## 🔗 More from Devil Scrapes

- [Alibaba Products Scraper on Apify Store](https://apify.com/DevilScrapes/alibaba-products-scraper)
- [JavaScript version of this example](https://github.com/devilscrapes/alibaba-product-scraper-javascript)
- [All Devil Scrapes Actors](https://apify.com/DevilScrapes)
- [Apify web scraping cookbook](https://github.com/devilscrapes/apify-web-scraping-cookbook)

Related Actors:

- [AliExpress Products Scraper](https://apify.com/DevilScrapes/aliexpress-products-scraper) — retail prices and orders for the same products on AliExpress.
- [ImportYeti Alternative Scraper](https://apify.com/DevilScrapes/importyeti-alternative-scraper) — check which suppliers actually ship to US importers.
- [DirectIndustry Industrial Suppliers Scraper](https://apify.com/DevilScrapes/directindustry-industrial-suppliers-scraper) — industrial equipment suppliers outside the Alibaba ecosystem.

---

MIT licensed example code. The Actor itself runs on [Apify](https://apify.com/DevilScrapes/alibaba-products-scraper) and is maintained by [Devil Scrapes](https://apify.com/DevilScrapes). Not affiliated with Alibaba.com or Alibaba Group.
