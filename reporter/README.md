# Datadog Reporter

## Overview

[![Reporter Introduction](https://raw.githubusercontent.com/DataDog/marketplace/master/reporter/images/video.png)](https://www.youtube.com/watch?v=GK5cGDUr1CA)

Datadog Reporter allows you to schedule reports and email them out on a set interval. You can pick any of your existing dashboards, add the URL to the reporter web application, and set the mailing interval to send it out. The report will be emailed to your users as an attachment that they can open to view.  There is currently no limit to the number of reports you can generate and send, but this will likely change in the future.

This integration will setup a new dashboard in your Datadog instance, that will simply show an iFrame to our application.  The application can be accessed directly by going to https://ddreporter.rapdev.io, and you can login with the same credentials as signing up from withing the Datadog iFrame.  *Your Datadog account will NOT work in the DD Reporter application.  You must register a seperate account*

---
*This isn't the integration you're looking for? Missing a critical feature for your organization? Drop us a [note](mailto:integrations@rapdev.io) and we'll build it!!*

## Setup
Below are some screenshots of the reporter application and how to get setup.

![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/reporter/images/1.png)
1. Paste the link to any public Datadog dashboard
2. Add the list of emails you want to send the report to
3. Select the frequency and timeframe for your dashboards
4. Click save and send

You will see a loading screen for a few seconds, then get redirected to your dashboard where you will find a list of your reporting jobs.

![Screenshot1](ihttps://raw.githubusercontent.com/DataDog/marketplace/master/reporter/images/2.png)

Once the job is saved, you'll get a confirmation.

![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/reporter/images/3.png)
Your reports will be sent by email as an attachement as shown above.

## Support

For support or feature requests please contact RapDev.io through the following channels: 

 - Email: integrations@rapdev.io 
 - Chat: [RapDev.io/products](https://rapdev.io/products)
 - Phone: 855-857-0222 

## Pricing

$250/month for unlimited reports

## Vendor Information

[RapDev.io](http://rapdev.io)

Made with ❤️ in Boston
