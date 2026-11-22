# First-revenue market validation — DataPilot AI

## Decision

Start with a narrow service, not a self-serve SaaS launch:

**A human-reviewed monthly sales-export analysis for small Shopify / ecommerce operators who still use spreadsheets for reporting.**

The job is not to promise "AI insights" or profit calculations. It is to turn an existing CSV/XLSX export into a transparent, evidence-backed report and a clean workbook, while clearly identifying missing definitions.

## Evidence observed (22 November 2026)

1. In a Shopify Community thread dated 27 August 2026, a small-store operator described copying orders, fixing stock and rebuilding weekly sales reports in Sheets before month-end. The thread asks what report takes longest and what tools are being used: https://community.shopify.com/t/stuck-in-sheets-for-sales-reports-how-are-you-handling-this/673334
2. A June 2025 Reddit discussion from a small Shopify store owner asked how peers track top products, best customers, weekday sales, monthly revenue and units per order, including whether they export CSVs and use Excel: https://www.reddit.com/r/shopify/comments/1lm6qit/how_do_you_guys_track_analytics_in_your_small/
3. A recent ecommerce operations report (Q4 2026) reports spreadsheet fragility and manual data entry among interviewed operators. It is directional evidence only, not a representative census: https://www.sku.io/research/ecommerce-ops-pain-index/
4. Shopify's own 2026 reporting guide lists product/category/channel sales, average order value, discounts, returns, repeat purchases and channel efficiency among common ecommerce reporting questions: https://www.shopify.com/blog/ecommerce-reporting

These sources show that reporting and spreadsheet workflows are real discussion topics. They do **not** prove willingness to pay for this exact service or validate the $49 price. The first paid pilot must test both.

## Initial customer profile

- Owner/operator of a small ecommerce store.
- Exports orders or sales to CSV/XLSX.
- Has no dedicated analyst and periodically rebuilds reports in spreadsheets.
- Has a concrete decision: what products/categories are moving, how sales change over time, or whether the export is reliable enough for a monthly review.
- Can share a sanitized export and explain what each row and key numeric field means.

Avoid stores that need reconciled profit, ad attribution, inventory forecasting, tax/accounting conclusions or multi-platform integration. Those require source systems and definitions DataPilot does not currently have.

## Offer and experiment

- One sanitized dataset, one human-reviewed HTML report and XLSX workbook.
- Introductory test price: US$49.
- No free custom analysis. A fictional sample report is the demonstration asset.
- First validation target: secure one paid pilot and learn which sections the customer values; do not forecast revenue from prospect counts.
- After 3 paid pilots, compare time spent, revision requests and customer feedback before setting a recurring package.

## Outreach policy

- Prioritize direct, individually relevant outreach to store owners and ecommerce consultants / small agencies.
- Use public business contact channels and respect each site's contact rules.
- Do not scrape private personal data, bulk spam, or post unsolicited sales pitches in communities that prohibit solicitation.
- A community thread is a research signal, not permission to message its author.
- No email is sent and no prospect is represented as contacted until the relevant account is connected and the user authorizes sending.

## Payment constraints — Morocco

- Stripe's official global availability list does not currently list Morocco. Do not build a Stripe checkout around a Moroccan business account: https://stripe.com/global
- PayPal's developer documentation lists Morocco as a country where account holders can send, receive and withdraw, but PayPal says features vary by market/account. Confirm receiving and withdrawal options inside the actual account before promising a payment route: https://developer.paypal.com/payouts/supported-features
- Do not ask for a card or pay for a workaround. For the pilot, agree a lawful, traceable payment method before accepting work; check applicable Moroccan tax and foreign-exchange requirements.

## Current product constraints

- Streamlit session workspaces are not persistent accounts.
- No native checkout or payment processing.
- No automated scheduled reporting.
- No guarantee that every uploaded file supports revenue, margin, refund, inventory or customer-retention analysis.
- The analysis must be reviewed by a human and grounded in the customer's definitions.

## Next execution steps

1. Merge the documentation correction and pilot offer after reviewing the PR.
2. Create a fictional sample report from the built-in synthetic dataset and label it prominently as synthetic.
3. Build a researched, small prospect list from public business/agency contact pages (not community users).
4. Prepare individually relevant outreach drafts; send only after the sender account is connected and sending is authorized.
5. Record replies, objections, agreed scope, payment and delivery status. Count only cleared paid work as revenue.
