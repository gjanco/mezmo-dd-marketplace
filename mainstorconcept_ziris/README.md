# z/IRIS - Mainframe-inclusive observability

## Overview


[z/IRIS](https://www.mainstorconcept.com/mainframe/z-iris-mainframe-observability/z-iris-datadog/?lang=en) is a plug-in software solution, built to provide mainframe-inclusive performance monitoring for the non-mainframe world. 

DevOps teams want to understand how mainframe performs for their business applications and how peak performance can be maintained or achieved.
With z/IRIS, mainframe observability for DevOps is a core concept. Teams can begin assessing the use of mainframe resources, continuously analyze performance, and compare metrics and data across applications using Datadog. 

### Distributed Db2 for z/OS
* Tracing enables JDBC observability with Db2 for z/OS:
	* Smart deadlock alerting and detection
	* Performance monitoring
	* JDBC performance analytics

### z/OS Connect Observability
* Trace REST API requests processed on mainframe:
	* Identify latencies within mainframe systems
	* Perform sophisticated application analysis enabled by metadata
* Additional metrics streaming enables enriched user experience

### z/OS Work observability
* Mainframe batch job observability
* Address spaces and subsystem monitoring
* TSO user activity tracing

### Partners by region

North-American based organizations can contact our partner SEA:
* E-mail: [SEA- Software Engineering of America](mailto:support@seasoft.com)
* Phone: (800) 272-7322 (Voice toll-free)
* Phone: 516-328-7000

EMEA and South American based organization can contact:
* E-mail: [mainstorconcept GmbH](mailto:sales@mainstorconcept.com)
* Phone: +49721790760

### Data Collected

### Trace Tags

|Trace Tag Name                        | Description                    |
|--------------------------------------|--------------------------------|
|zos.connect.api.name                  | API name of z/OS Connect       | 
|zos.connect.api.version               | API Version of z/OS Connect    |
|zos.connect.request.id                | Request ID                     |
|zos.connect.request.timed_out         | Request time out               | 
|zos.connect.request.user_name         | Request user name              | 
|zos.connect.service.name              | Service name                   | 
|zos.connect.service.version           | Service version                | 
|zos.connect.service_provider.name     | Service provider name          | 
|zos.connect.sor.identifier            | SOR identifier                 |  
|zos.connect.sor.reference             | SOR reference                  |  
|zos.connect.sor.request.received_time | SOR request received           |  
|zos.connect.sor.request.sent_time     | SOR request sent time          |  
|zos.connect.sor.resource              | SOR resource                   |  
|zos.job.class                         | z/OS job class                 |  
|ziris.job.identifier                  | z/OS job identifier            |  
|zos.jes.job.correlator                | JES job correlator             |  
|zos.job.step.cpu.units                | z/OS step CPU units            |  
|zos.job.step.program_name             | z/OS job step program name     |  
|zos.job.step.ended                    | z/OS job step ended            |  
|zos.job.step.name                     | z/OS job step name             |  
|zos.job.step.number                   | z/OS job step number           |  
|zos.job.step.cpu.time_ms              | z/OS job step CPU time         |  
|zos.job.step.ziip.time_ms             | z/OS job step ZIIP time        |  
|zos.tape.mounts                       | z/OS tape mounts               |  
|zos.job.step.return_code              | z/OS job step return code      |  
|zos.racf.group.id                     | z/OS RACF group ID             |  
|zos.user.id                           | z/OS user id                   |  
|zos.user.name                         | z/OS user name                 |  
|host.name                             | Host name                      |  
|http.method                           | HTTP method                    |  
|http.response_content_length          | HTTP response content length   |  
|http.request_content_length           | HTTP request content length    |  
|http.status_code                      | HTTP status code               |  
|http.client_ip                        | HTTP client ip                 |  
|db.system                             | DB system                      |  
|net.peer.ip                           | Net peer IP                    |  
|net.peer.port                         | Net peer port                  |  
|enduser.id                            | End user ID                    |  
|db.db2.collection.id                  | Db2 collection ID              |  
|db.db2.instance_name                  | Db2 instance name              |  
|db.user                               | DB user                        |  
|zos.db2.wait.time_ms                  | Db2 wait time                  |  
|zos.db2.unlock.requests               | Db2 unlock request             |  
|zos.db2.sql.storedprocedure.statements| Db2 SQL stored procedure       |  
|zos.db2.start.timestamp               | Db2 start timestamp            |  
|zos.db2.end.timestamp                 | Db2 end timestamp              |  
|zos.db2.response.time_ms              | Db2 response time              |  
|zos.db2.elapsed.time_ms               | Db2 elapsed time               |  
|zos.cpu.time_ms                       | CPU time                       |  
|zos.db2.abort.requests                | Db2 abort request              |  
|zos.db2.su.factor                     | Db2 su factor                  |  
|zos.db2.workload.service.class.name   | Db2 workload service class name|  
|zos.db2.cpu.time_ms                   | Db2 CPU time                   |  
|zos.ziip.time_ms                      | ZIIP time                      |  
|zos.db2.ziip.time_ms                  | Db2 ZIIP time                  |  
|zos.db2.remote.location.name          | Db2 remote location name       |  
|zos.db2.product.id                    | Db2 product ID                 |  
|zos.db2.sent.bytes                    | Db2 sent bytes                 |  
|zos.db2.received.bytes                | Db2 received bytes             |  
|zos.db2.client.application.name       | Db2 client application name    |  
|zos.db2.client.platform               | Db2 client platform            |  
|zos.db2.client.auth.id                | Db2 client auth ID             |  
|zos.db2.sql.prepare.statements        | Db2 SQL prepare statement      |  
|zos.db2.sql.open.statements           | Db2 SQL open statement         |  
|zos.db2.sql.lock.statements           | Db2 SQL lock statement         |  
|zos.db2.connection.id                 | Db2 connection ID              |  
|zos.db2.consistency.token             | Db2 consistency token          | 
|zos.correlation.id                    | Db2 correlation ID             |  
|zos.db2.plan.name                     | Db2 plan name                  |  
|zos.db2.program.name                  | Db2 program name               |  
|zos.db2.lock.state                    | Db2 lock state                 |  
|zos.db2.statement.id                  | Db2 statement ID               |  
|zos.db2.statement.type                | Db2 statement type             |  
|zos.db2.thread.token                  | Db2 thread token               |  
|zos.uow                               | UOW                            |  
|zos.db2.lock.request                  | Db2 lock request               |  
|zos.db2.lock.duration                 | Db2 lock duration              |  
|zos.db2.deadlock.resources            | Db2 deadlock resources         |  
|zos.db2.ace                           | Db2 ACE                        |  
|zos.db2.location.name                 | Db2 location name              |  
|zos.db2.luw.id                        | Db2 LUW ID                     |  
|zos.db2.uniqueness.value              | Db2 uniqueness value           |  
|zos.db2.version                       | Db2 version                    |  
|zos.lu.name                           | LU name                        |  
|zos.network.id                        | z/OS network ID                |  
|zos.subsystem.name                    | z/OS subsystem name            |  


### Mainframe metrics

* [RMF Metrics](https://public.mainstorconcept.com/home/RMF-Metrics-Streaming.636715153.html) 
	* RMF metrics provide resource utilization metrics at customizable intervals and at customizable levels of detail.

* [z/OS Connect Metrics](https://public.mainstorconcept.com/home/z%2FOS-Connect-Metrics-Streaming.641040425.html)
	* z/IRIS streams metrics created using data from IBM's z/OS Connect SMF type 123 version 1 and 2 records. 

* [MQ Metrics](https://public.mainstorconcept.com/home/MQ-Metrics-Streaming.1424359429.html)
	* MQ statistics records (SMF Type 115) contain a multitude of statistics from various resources within the system. z/IRIS introduces z/OS MQ Metrics, focusing on the most vital performance indicators for monitoring, analysis, and alerting purposes.

This isn't the metric you're looking for? Missing a critical feature for your organization? Send us a feature request to [info@mainstorconcept.com](mailto:info@mainstorconcept.com).


## Setup

### Installation

1. z/IRIS server: IronTap
	1. Login Data:
		* username: datadog-trial
		* password: We will provide the password for the repository with the license via email within 24 hours.
	2. [IronTap Image](https://public.mainstorconcept.com/home/IronTap-Image.1121255425.html)
		* Enter the command in your CLI and follow the prompts entering your login data.  
		
		    docker login mainstorconcept.jfrog.io
		
		* Enter the second command to obtain z/IRIS.  		
		
			docker pull mainstorconcept.jfrog.io/ziris-docker-release/irontap:latest-kafka-otel
	
	3. [Configure IronTap server](https://public.mainstorconcept.com/home/Configure-IronTap-container.1121517569.html)
	
2. z/IRIS z/OS Client
	1. [Install z/IRIS z/OS Client](https://public.mainstorconcept.com/home/Install-z%2FIRIS-clients.713228788.html)
	2. [Configure z/IRIS Clients](https://public.mainstorconcept.com/home/Configure-z%2FIRIS-Clients.713228858.html)
	3. [z/IRIS Client Started Task](https://public.mainstorconcept.com/home/z%2FIRIS-Client-Started-Task.713228925.html)

### License application 

After starting your trail period, we will provide your z/IRIS trial license via email within 24 hours. 
 	
### Validation

Verify that the relevant components are available and meet the [minimum requirements](https://public.mainstorconcept.com/home/Troubleshooting-OpenTelemetry-integration.1121812489.html).


## Support

If you have any questions about z/IRIS, please open a [support request](https://service.mainstorconcept.com/mscportal/login)
or contact us at [support@mainstorconcept.com](mailto:support@mainstorconcept.com).

If you want to schedule a demo, please contact [sales@mainstorconcept.com](mailto:sales@mainstorconcept.com).

If you are looking for local support for the North American region, contact our partner [SEA- Software Engineering of America](mailto:support@seasoft.com) per mail or call (800) 272-7322.
