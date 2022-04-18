## Overview

This integration monitors email mailboxes and measures full send-receive synthetic messages deliveries. The integration uses three geographical source locations for the synthetic email deliveries: Virginia (US), Frankfurt (EU) and Sydney (AP). The check works by sending a test email from the address `probe@synth-rapdev.io` and then waiting for a auto-reply from your mailbox back to us.  The integration measures the number of hops, round-trip-time, and the test results (pass/fail).

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

## Setup

### Integration Install

Linux:
* `sudo -u dd-agent datadog-agent integration install --third-party datadog-syntheticemail==1.1.0`

Windows:
* `"C:\Program Files\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-syntheticemail==1.1.0`

### Mailbox Configuration

1. Create a mailbox for receiving synthetic email probes. The mailbox should not be used for other message activity because the forwarding rule of the mailbox is used for round-trip synthetic measurements.
2. Configure the target email address mailbox to auto-forward emails to `probe@synth-rapdev.io`. Optionally configure your email forwarding configuration to disable copies of the forwarded email.
3. Set the target email address configured in steps 1 and 2 by updating `email_address: {your@email.address}` in the syntheticemail.d/syntheticemail.yaml.
4. [Restart the Agent](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7).

### Validation

[Run the Agent's status subcommand](https://docs.datadoghq.com/agent/guide/agent-commands/?tab=agentv6v7#agent-status-and-information) and look for `syntheticemail` under the Checks section.

## Support
For support or feature requests please contact RapDev.io through the following channels: 

 - Email: datadog-engineering@rapdev.io 
 - Chat: [rapdev.io](https://www.rapdev.io/#Get-in-touch)
 - Phone: 855-857-0222 

### Pricing
Interested in using multiple RapDev integrations? Contact [ddsales@rapdev.io](mailto:ddsales@rapdev.io) for packaged pricing offers.

---
Made with ❤️ in Boston

*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:datadog-engineering@rapdev.io) and we'll build it!!*

---
This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here](https://app.datadoghq.com/marketplace/app/rapdev-syntheticemail/pricing) to purchase this application.
