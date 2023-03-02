# CHANGELOG

## 1.12.0 / 2023-02-27

### Features
All features created in this release culminate in users obtaining end-to-end workflow and performance insights where 
requests depend on IBM MQ for z/OS and CICS transactions. Find out more about these features below.

### MQ for z/OS Trace
Traces are created from SMF 116 type 1 and 2 records to depict tasks/threads that initiated within a z/OS MQ Queue Manager
to process messages in queues or topics. Each MQ for z/OS trace identifies how the task was initiated, the latency of 
the task, and whether the Queue Manager detected any errors. Child spans within the trace each identify an object 
(queue or a topic) that the task used to process messages. The time spent connected to the object is shown through the 
child spans' duration.

### CICS Transaction spans
Spans are created from SMF 110 records to describe CICS transaction executed on z/OS. Each span identifies the 
transaction and it's response time. Also contained within the spans are Resource and Trace attributes. Resource attributes 
identify the CICS subsystem as well as the z/OS LPAR and Sysplex that processed the transaction. Trace attributes 
provide additional performance and resource utilization metrics for the processing of the transaction.

See [CICS Transaction Observability](https://public.mainstorconcept.com/home/cics-transaction-observability) to find out
more about the span design, and refer to 
[CICS Transaction Spans](https://public.mainstorconcept.com/home/cics-transaction-spans) for a detailed list of 
attributes provided.

### Distributed MQ to MQ for z/OS Workflow Tracing (BETA)
A new function enables the correlation of APM traces from distributed IBM MQ clients with 
[MQ for z/OS](https://public.mainstorconcept.com/home/ibm-mq-for-z-os-observability) spans created by z/IRIS. This 
correlation reveals which client applications depend on MQ for z/OS queues and queue managers for digital business 
services. The insight provided by MQ for z/OS spans will help users identify how mainframe resources are consumed and 
how mainframe applications perform for distributed applications.

### Mainframe Workflow Tracing for IBM MQ and CICS spans (BETA)
Users can identify [CICS Transactions](https://public.mainstorconcept.com/home/cics-transaction-observability) that use
[MQ for z/OS](https://public.mainstorconcept.com/home/ibm-mq-for-z-os-observability) in a single logical unit of work. 
This enables visibility into the relationship between these services and enables holistic analysis and monitoring for 
users.

## 1.0.0 / 2022-04-06

* [Added] Initial Release


