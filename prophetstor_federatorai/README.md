# Federator.ai

## Overview

[ProphetStor Federator.ai][1] is an AI-based solution that helps enterprises manage, optimize, and auto-scale resources for any applications on Kubernetes. Using advanced machine learning algorithms to predict application workload, Federator.ai scales the right amount of resources at the right time for optimized application performance.

* AI-based workload prediction for containerized applications in Kubernetes clusters and VMs in VMware clusters 
* Resource recommendations based on workload prediction, application, Kubernetes, and other related metrics 
* Automatic scaling of application containers 
* Multicloud cost analysis and recommendations based on workload predictions for Kubernetes clusters and VM clusters 
* Actual cost and potential savings based on recommendations for clusters, Kubernetes applications, VMs, and Kubernetes namespaces

With a ProphetStor Federator.ai license, you can apply an AI-based solution to track and predict the resource usages of Kubernetes containers, namespaces, and cluster nodes to make the right recommendations to prevent costly over-provisioning or performance-impacting under-provisioning. Utilizing application workload predictions, Federator.ai auto-scales application containers at the right time and optimizes performance with the right number of container replicas through Kubernetes HPA or [Datadog Watermark Pod Autoscaling (WPA)][3].

Separate from this Federator.ai license, an official [Datadog Integration][9] with out-the-box dashboards and recommended monitors is available. For additional information on Federator.ai, you can view the [ProphetStor Federator.ai Feature Demo][2] video.

## Setup

* Follow the instructions below to download and set up Federator.ai.

### Installation

1. Log in to your OpenShift/Kubernetes cluster.
2. Install Federator.ai for OpenShift/Kubernetes using the following command:

   ```shell
   $ curl https://raw.githubusercontent.com/containers-ai/prophetstor/master/deploy/federatorai-launcher.sh | bash
   ```

   ```shell
   $ curl https://raw.githubusercontent.com/containers-ai/prophetstor/master/deploy/federatorai-launcher.sh | bash
   ...
   Please enter Federator.ai version tag [default: latest]:datadog
   Please enter the path of Federator.ai directory [default: /opt]:
   
   Downloading v4.5.1-b1562 tgz file ...
   Done
   Do you want to use a private repository URL? [default: n]:
   Do you want to launch Federator.ai installation script? [default: y]:
   
   Executing install.sh ...
   Checking environment version...
   ...Passed
   Enter the namespace you want to install Federator.ai [default: federatorai]:
   .........
   Downloading Federator.ai alamedascaler sample files ...
   Done
   ========================================
   Which storage type you would like to use? ephemeral or persistent?
   [default: persistent]:
   Specify log storage size [e.g., 2 for 2GB, default: 2]:
   Specify AI engine storage size [e.g., 10 for 10GB, default: 10]:
   Specify InfluxDB storage size [e.g., 100 for 100GB, default: 100]:
   Specify storage class name: managed-nfs-storage
   Do you want to expose dashboard and REST API services for external access? [default: y]:
   
   ----------------------------------------
   install_namespace = federatorai
   storage_type = persistent
   log storage size = 2 GB
   AI engine storage size = 10 GB
   InfluxDB storage size = 100 GB
   storage class name = managed-nfs-storage
   expose service = y
   ----------------------------------------
   Is the above information correct [default: y]:
   Processing...
   
   (snipped)
   .........
   All federatorai pods are ready.
   
   ========================================
   You can now access GUI through https://<YOUR IP>:31012
   Default login credential is admin/admin
   
   Also, you can start to apply alamedascaler CR for the target you would like to monitor.
   Review administration guide for further details. 
   ========================================
   ========================================
   You can now access Federatorai REST API through https://<YOUR IP>:31011
   The default login credential is admin/admin
   The REST API online document can be found in https://<YOUR IP>:31011/apis/v1/swagger/index.html
   ========================================
   
   Install Federator.ai v4.5.1-b1562 successfully
   
   Downloaded YAML files are located under /opt/federatorai/installation
   
   Downloaded files are located under /opt/federatorai/repo/v4.5.1-b1562
   ```

3. Verify Federator.ai pods are running properly.

   ```shell
   $ kubectl get pod -n federatorai
   ```
4. Log in to the Federator.ai GUI. Find the URL and login credentials in the output of Step 2.

5. Complete the steps of the [Federator.ai - Installation and Configuration Guide][4] to configure Federator.ai. 

6. Refer to the [User Guide][8] for more details.


## Support

For support or requests, contact [ProphetStor support](mailto:support@prophetstor.com).


[1]: https://prophetstor.com/federator_ai/
[2]: https://youtu.be/AeSH8yGGA3Q
[3]: https://github.com/DataDog/watermarkpodautoscaler
[4]: https://prophetstor.com/wp-content/uploads/documentation/Federator.ai/Latest%20Version/ProphetStor%20Federator.ai%20Installation%20Guide.pdf
[5]: images/add_cluster_window.png
[6]: https://www.datadoghq.com/
[7]: https://docs.datadoghq.com/account_management/api-app-keys/
[8]: https://prophetstor.com/wp-content/uploads/documentation/Federator.ai/Latest%20Version/ProphetStor%20Federator.ai%20User%20Guide.pdf
[9]: https://app.datadoghq.com/account/settings#integrations/federatorai
