# Contact
Please reach out to marketplace@datadoghq.com with any questions.

<p>&nbsp;</p> 

# Marketplace
The [Datadog Marketplace](https://www.datadoghq.com/blog/datadog-marketplace/) is a digital marketplace where [Datadog partners](https://www.datadoghq.com/partner/) can sell their third-party applications to Datadog users. 

Backed by strict vetting standards and a fully managed billing system, the Marketplace introduces new ways for developers to build and trade tools on the Datadog platform.

![An screenshot of the Marketplace from the Datadog application with a list of integration tiles](https://imgix.datadoghq.com/img/blog/datadog-marketplace/marketplace-cover-2.png?fit=max)

### Benefits

- **Increased product visibility.**
Thousands of users who are logged into the Datadog platform will be able to see and enable your integration tile.

- **Co-marketing opportunities.**
Once the integration is complete, a representative from Datadog will reach out to scope a go-to-market strategy.

- **Revenue opportunities.**
The Marketplace ecosystem opens up new sales channels for Datadog partners.

<p>&nbsp;</p> 

# Getting Started

Please follow the instructions in [the Marketplace documentation](https://docs.datadoghq.com/developers/marketplace/) to get started with creating your Marketplace listing and drafting your pull request. 

### Pull request review process
Please create a Draft PR for any work in progress, and use regular PRs when your changes are ready for Datadog's engineering team to review. If a regular PR has already been submitted, please open a new PR for any future changes.

Datadog reviewers will add the priority of their comments. When all required changes have been addressed, your listing will be published.

**Note:** For new marketplace listings, once the pull request has been merged in the marketplace repo, we are able to first enable the tile for just your sandbox account. This will allow you to validate and submit any necessary changes to the tile or documentation before it is enabled for all users. 

<p>&nbsp;</p> 

# FAQ

**Where is the Marketplace located?**\
The [Marketplace](https://app.datadoghq.com/marketplace) can be accessed from the Integrations tab in the Datadog app.

**How does pricing work?**\
Datadog Partners can list their integration in the Marketplace using one of the following pricing options. **Note**: All integration purchases begin with a 14-day free trial. 

- **one_time:** Charges a single fee at the time of purchase, and no additional charges in the future. No metering/usage metric is required.

- **flat_fee:** Charges a recurring flat fee per month regardless of a customer's usage. For example, a partner may charge a customer $100/month. No metering/usage metric is required.

- **Tag_count:** Allows partners to charge based on a customer's usage. For example, vendors can charge per unique user, device, or database. A metering metric is required for tracking usage. The `tag_count` metering metric must be in the manifest.json to appear in a partner's Marketplace tile, and in the metadata.csv to register the metric in Datadog's backend. For `tag_count`, Datadog calculates the top 99% of hourly usage for the billing cycle.

Example JSON:
```
"pricing": [{
    "billing_type": "tag_count",
    "unit_price": 1,
    “metric”: “datadog.marketplace.partner_name.integration_name”,
    “tag”: ”user”
    “unit_label”: “Integration Name User”,
}]
```

**What is the Marketplace's release cadence?**\
Datadog Marketplace practices CI/CD. Datadog's engineering team will review pull requests as they are submitted.

**If I have feature request or I have discovered a bug, who should I reach out to?**\
Please open an [issue](https://github.com/DataDog/marketplace/issues) to report a bug or submit a feature request. You can also always reach out to marketplace@datadoghq.com with any questions.
