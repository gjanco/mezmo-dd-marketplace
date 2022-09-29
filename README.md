# Contact
Please reach out to marketplace@datadoghq.com with any questions.

<p>&nbsp;</p> 

# Marketplace
The [Datadog Marketplace](https://www.datadoghq.com/blog/datadog-marketplace/) is a digital marketplace where [Datadog partners](https://www.datadoghq.com/partner/) can sell their third-party applications and professional services to Datadog customers. 

Backed by strict vetting standards and a fully managed billing system, the Marketplace introduces new ways for partners to extend the Datadog platform.

![An screenshot of the Marketplace from the Datadog application with a list of integration tiles](https://imgix.datadoghq.com/img/blog/datadog-marketplace/marketplace-cover-2.png?fit=max)

### Benefits

- **Increased product visibility.**
Thousands of customers who are logged into the Datadog platform will be able to see and enable your integration tile. Your tile will also be discoverable to the general public on our corporate and documentation websites. 

- **Co-marketing opportunities.**
Once the pull-request for your offering is submitted and reviewed, a representative from Datadog will reach out to scope a go-to-market strategy.

- **Revenue opportunities.**
The Marketplace ecosystem opens up new sales channels for Datadog partners.

<p>&nbsp;</p> 

# Getting Started

Please follow the instructions in [the Marketplace documentation](https://docs.datadoghq.com/developers/marketplace/) to get started with creating your Marketplace listing and drafting your pull request. 

### Pull request review process
Please create a *draft* PR for any work in progress, and use *regular* PRs when your changes are ready for Datadog's Engineering team to review.

Datadog reviewers will add the priority of their comments and whether or not they are blocking. When all required changes have been addressed, your listing will be published.

**Note:** For new Marketplace listings, we can enable the tile in your partner sandbox account at your request. This will allow you to review and approve your tile before it is enabled for all users. 

<p>&nbsp;</p> 

# FAQ

**Where is the Marketplace located?**\
The [Marketplace](https://app.datadoghq.com/marketplace) can be accessed from the Integrations tab in the Datadog app.

### PRICING

**How does pricing work?**\
All Marketplace listings must be a commercial offering with an associated monthly price. Datadog Partners can list their offering in the Marketplace using one of the following pricing options. 

**Note**: Only Pro, Enterprise, and Developer Sandbox Datadog accounts can purchase Marketplace listings. If you have a potential customer interested in your offering that's currently in a Datadog trial or free account, please contact [marketplace@datadog.com](mailto:marketplace@datadog.com).

All Marketplace purchases begin with a 14-day free trial. A customer automatically converts to a paying subscriber after their 14-day free trial ends. 

Customers who have subscribed to the default monthly price, are invoiced within the two weeks following the close of the monthly billing period. For example, a customer would typically receive an invoice by February 15th for their subscription in the previous month of January.

The Datadog Marketplace supports three types of pricing models:

- **one_time:** Charges a single fee at the time of purchase, and no additional charges in the future. No metering/usage metric is required.

- **flat_fee:** Charges a recurring flat fee per month regardless of a customer's usage. For example, a partner may charge a customer $100/month. No metering/usage metric is required.

- **Tag_count:** Allows partners to charge based on a customer's usage. For example, vendors can charge per unique user, device, or database. A metering metric is required for tracking usage. The `tag_count` metering metric must be in the manifest.json to appear in a partner's Marketplace tile. For `tag_count`, Datadog calculates the top 99% of hourly usage for the billing cycle.

Example JSON:
```
"pricing": [{
    "billing_type": "tag_count",
    "unit_price": 1,
    "metric": “datadog.marketplace.partner_name.integration_name",
    "tag": "user",
    “unit_label": "Integration Name User",
    "product_id": "product_name",
    "includes_assets": true,
    "short_description": "Short description."
}]
```

| Element | Description | Type | Required | Notes |
| ---- | ---- | ---- | ---- | ---- |
| pricing | Top level | array | Required | |
| billing_type | The billing type for your Marketplace offering. | string | Required | Limited to "one_time", "flat_fee", or "tag_count". Only one billing type can be selected. |
| unit_price | The default price for your offering. | number | Required | All numbers are translated to US dollars. The one time price is charged once. The flat fee price is charged monthly, regardless of usage. The tag count price is charged monthly based on the unique combination of the metering metric and tags, for example, per user. |
| metric | The metering metric sent by the partner used to calculate a customer's usage. | string | Only Required for "tag_count" billing type | Required format: “datadog.marketplace.partner_name.integration_name”. |
| tag | The tag added to the metering metric sent by the partner to determine unique units. | string | Only Required for "tag_count" billing type | The tag should return unique values per unit. For example, if you are charging per user, the metering metric must be tagged with a unique user ID. |
| unit_label | The label that will display in the "Pricing" section of your Marketplace tile. | string | Required | Example: "Price per [unit_label] per month". |
| product_id | The second half of your app_id that contains your product name. | string | Required | Kebab case (e.g., my-integration-name) is required. Comment on your pull-request or email marketplace@datadog.com with questions. |
| includes_assets | Denotes whether your offering comes with out-of-the-box assets like dashboards. | boolean | Required | Always set to true. |
| short_description | Briefly describes or adds color to your pricing model. | string | Required | **Note**: this element is not displayed on the front-end today, but may be in the future. |

**What is a Private Offer?**\
A Private Offer is a custom contract between a partner and a customer. Any deviations from the listed pricing plan such as volume discounts or specific contract lengths must be purchased through a Private Offer. Customers must first click purchase in the Marketplace before Datadog can invoice them for any Private Offer pricing. 

To kick off a Private Offer, the partner must send a copy of the signed contract to [marketplace@datadog.com](mailto:marketplace@datadog.com) with the following information included:
* Customer and Partner Legal Names
* Customer and Partner Contacts
* Start Date
* End Date
* Itemized price
* Total price
* Overage price (if usage-based)
* Committed Amount (if usage-based)
* Billing Contact
* Billing Address
* Billing cycle: upfront, annually, monthly
* Auto-renewal clause (if you want the agreement to auto-renew) - Please note that renewals can only take place in 1-month, 12-month, 24-month, 36-month, 48-month, and 60-month intervals


**What is a Marketplace drawdown?**\
A Marketplace Drawdown is a dedicated fund set up by customers, where the signed agreements are between the customer and Datadog rather than the Partner. Note: this fund is entirely separate from any existing Datadog Drawdown. Dedicated Marketplace Drawdown funds can only be used specifically to make purchases within the Datadog Marketplace and any purchases and usage are deducted from that account. 

**How does Datadog calculate billing for SaaS licenses customers?**\
*Note: This only applies to usage-based pricing plans.* 

Partners are required to send the Datadog team a monthly report of customer usage, since software licenses currently cannot submit a metering metric and Datadog does not have insight into this usage. The billing information in the report should match the pricing defined in the `manifest.json` file. The Datadog team will create an invoice for each customer based on a number of factors including when the free-trial ended and whether there is a Private Offer in place. 

Please include the following information in the report:
* Customer Name
* Customer Email 
* Usage for the last month

Send a copy of the report every month to [marketplace@datadog.com](mailto:marketplace@datadog.com). 

The Datadog team is currently developing an automated billing endpoint that is currently in alpha. This endpoint allows partners to send custom metering metrics to Datadog to automatically calculate usage. If interested in participating in our alpha program, please reach out to the Datadog Marketplace team.

### SUBSCRIPTIONS
 
**How do I know if someone signed up for a subscription?**\
When a new customer trials an offering, an email notification will be sent to the email address listed under the `sales_email` field in the `manifest.json` file. This email will include the customer’s name, organization name, contact email, the offering they purchased, and the start time of the trial. 

**How do I know if someone canceled a subscription?**\
Similarly to when a customer signs up for a subscription, a corresponding notification is sent to the email address under the `sales_email` field in the `manifest.json` file with the date of cancellation. 

**What happens when a customer signs up for a SaaS license?**\
Once a customer purchases a subscription to a SaaS license in the Datadog Marketplace, an email will be sent to the email address under the `sales_email` field listed in the `manifest.json` file with the customer’s name, organization name, contact email, and start time of the trial. 

Partners should provide information in the “Setup” section of the README file about what will occur after the user purchases the offering in the Datadog Marketplace. Commonly, partners either inform the customer that a member of the team will reach out directly to help set up a new account, or provide a sign-up link to create an account.

### FEEDBACK

**What is the Marketplace's review and release cadence?**\
Datadog's Documentation, Product, and Engineering teams will review pull requests as they are submitted. If our team leaves comments, we will re-review once those comments have been fully addressed.

Note: a pull-request must be passing all validations for our teams to begin their reviews. If your pull-request is failing validations, please check for automated messaging, or run `ddev validate all` locally. 

Datadog Marketplace practices CI/CD, so all merged pull-requests typically will go live within an hour. However, a variety of factors may delay a release, including temporary production freezes. 

**If I have a feature request or I have discovered a bug, who should I reach out to?**\
Please open an [issue](https://github.com/DataDog/marketplace/issues) to report a bug or submit a feature request. You can also always reach out to [marketplace@datadog.com](mailto:marketplace@datadog.com) with any questions.
