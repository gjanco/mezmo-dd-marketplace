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
### 1. Create your integration.
- Clone the [marketplace repo](https://github.com/DataDog/marketplace)
- pip install version 4.0.0 or higher of the [Developer Toolkit](https://github.com/DataDog/integrations-core/tree/master/datadog_checks_dev)
- Configure `ddev` to look at your cloned marketplace repo. From the marketplace repo, run:
  - `ddev config set repo marketplace`
  - `ddev config set repos.marketplace .`
- Run the `ddev create "<Check Name>"` command. You can find the full documentation for this command [here](https://datadoghq.dev/integrations-core/ddev/cli/#create).

More available configuration options can be found in the [ddev package documentation](https://datadoghq.dev/integrations-core/ddev/configuration/).

For more information on integrations, you can find links to our documentation below: 
- [Introduction to integrations](https://docs.datadoghq.com/getting_started/integrations/)
- [Introduction to Agent-based integrations](https://docs.datadoghq.com/developers/integrations/)
- [Create a new integration](https://docs.datadoghq.com/developers/integrations/new_check_howto/?tab=configurationtemplate).
- [Writing a custom OpenMetrics Check](https://docs.datadoghq.com/developers/prometheus/)

**Note:** The examples in the documentation may use Datadog repos other than the marketplace.

### 2. Create a dashboard and tile.

**Default Dashboard**

All integrations are expected to contain an out-of-the-box dashboard. This dashboard will be loaded by default when users install the integration. It serves as an example of the best way to display relevant metrics for your product. Once you have created a dashboard in your sandbox account that you would like to include with the integration, include the dashboard name with your pull request. 

The pull request will need to include the dashboard payload, and a unique name for the dashboard in the manifest.json file. To accomplish this, you can use the `'ddev export "<Check Name>"` command. Find the full documentation for this command [here](https://datadoghq.dev/integrations-core/ddev/cli/#export).

**Integration Tile**

Each Datadog integration requires a list of assets and metadata for the tile that is displayed on both the Datadog integrations page as well as the documentation page. The Datadog Development Toolkit (“ddev”) allows you to create a scaffolding when you are first developing your integration which highlights the required information. If your integration is via our API and does not contain any Python code, the Development Toolkit also supports a “tile only” option (`ddev create -t tile "<Check Name>"`). This generates a skeleton for the following information required as part of the tile:
- Logos and images 
- Readme.md
- manifest.json
- metadata.csv

More information about the above requirements can be found in the [Integration assets references](https://docs.datadoghq.com/developers/integrations/check_references/).

### 3. Submit a pull request for review.
Please create a Draft PR for any work in progress, and use regular PRs when your changes are ready for Datadog's engineering team to review. If a regular PR has already been submitted, please open a new PR for any future changes.

Datadog reviewers will add the priority of their comments. When all required changes have been addressed, your integration will be published.

**Note:** For new marketplace integrations, once the Integration Tile has been merged in the marketplace repo, we will first enable the tile for just your sandbox account. This will allow you to validate and submit any necessary changes to the tile or documentation before it is enabled for all users. 

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
