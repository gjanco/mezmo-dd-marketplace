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

**How does pricing work?**\
Datadog Partners can list their integration in the Marketplace using one of the following pricing options. **Note**: Only Pro, Enterprise, and Developer Sandbox Datadog accounts can purchase Marketplace listings. If you have a potential customer interested in your offering that's currently in a Datadog trial or free account, please contact marketplace@datadog.com.

All Marketplace purchases begin with a 14-day free trial.

- **one_time:** Charges a single fee at the time of purchase, and no additional charges in the future. No metering/usage metric is required.

- **flat_fee:** Charges a recurring flat fee per month regardless of a customer's usage. For example, a partner may charge a customer $100/month. No metering/usage metric is required.

- **Tag_count:** Allows partners to charge based on a customer's usage. For example, vendors can charge per unique user, device, or database. A metering metric is required for tracking usage. The `tag_count` metering metric must be in the manifest.json to appear in a partner's Marketplace tile, and in the metadata.csv to register the metric in Datadog's backend. For `tag_count`, Datadog calculates the top 99% of hourly usage for the billing cycle.

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

**What is the Marketplace's release cadence?**\
Datadog Marketplace practices CI/CD. Datadog's engineering team will review pull requests as they are submitted.

**If I have feature request or I have discovered a bug, who should I reach out to?**\
Please open an [issue](https://github.com/DataDog/marketplace/issues) to report a bug or submit a feature request. You can also always reach out to marketplace@datadoghq.com with any questions.
