# Ozcode Production Debugger Integration

## Overview

Ozcode Production Debugger enables live debugging without requiring code changes. When an error occurs, Ozcode provides full-fidelity time-travel debug information with code-level visibility into the error execution flow, accelerating development velocity to enable a rapid resolution.

### Accelerating CI/CD 

Through live debugging in staging and testing environments, or in canary deployments, Ozcode puts data into the hands of developers short-circuiting the feedback loop from live environments back into development without requiring any changes to the code.

### Accelerating Incident Resolution

Ozcode proactively identifies errors and provides the relevant developers with all the data needed to understand and fix a bug thereby shortening MTTD, MTTD, and MTTR.

### Exceptions Overview
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/ozcode/images/exceptions-dashboard.png)

Exceptions are captured by Ozcode and displayed in the Ozcode DataDog dashboard. Simply click an exception to debug it.

### Debug Exceptions 
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/ozcode/images/exception-debug.png)

The debugging screen displays full-fidelity time-travel debug information, including local variables, method parameters and return values, color-coded conditional statements, network requests, and database queries across the whole call stack. This degree of code-level observability enables a quick root cause analysis and resolution of bugs. 

### Live Debugging with Dynamic Logs and Tracepoints 
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/ozcode/images/tracepoints.png)

Add live logs, metrics, and traces without having to go through the time-consuming cycle of change code --> build --> test --> release --> deploy a new version. Get a full capture of variables for any tracepoint without requiring any changes to the code.

### Pipe Logs, Metrics, and Traces into DataDog
![Screenshot1](https://raw.githubusercontent.com/DataDog/marketplace/master/ozcode/images/dynamic-logs.png)

Pipe logs, metrics, and traces directly into DataDog and correlate them through traceID and spanID. Common logging frameworks such as SeriLog, nLog and log4net are all supported. Through a point-in-time link provided by Ozcode, open up a new tab in the OzcodeUI to see a full time-travel debug information for an exception.

### Monitors

1. Tracepoints
2. Exceptions

### Dashboards

1. Ozcode Exceptions Dashboard
2. Ozcode Tracepoints Dashboard

## Setup

Follow the step-by-step instructions below to install and configure this check for an Agent running on a host. 

### Prerequisites

You must have the Datadog Agent installed and running. Additionally, you need to be able to connect to the server with the Datadog Agent installed.

### Installation

#### Step 1: Install Datadog .NET Tracer

1. Follow the following steps to install Datadog .Net Tracing agent for your [.Net Frameworkd][1a] or [.Net Core][1b] project on the machine.

2. Skip the steps for setting up environment variables to activate the .Net Tracer (See step 3)

#### Step 2: Install OzCode Agent

1. Go to https://app.oz-code.com and follow the instructions to install the agent on your local machine

2. Disable auto agent load on the machine
   ```
   cd %PROGRAM FILES%\OzCode\Production Debuger\Agent\config\
   OzCode.Configuration.Utility.exe disable
   ```

3. Manually inject the following environment variables

   For .Net Framework:

   Variable |  Value 
   --- | ---
   CLR_ENABLE_PROFILING | 1
   CLR_PROFILER | {DBE6D54B-4A04-4FD0-83EB-12A1A9DEC58B}
   CLR_PROFILER_PATH_32 | C:\Program Files\OzCode\Production Debugger Agent\agent\x32\OzCodeClrProfilerMultiplexer.dll
   CLR_PROFILER_PATH_64 | C:\Program Files\OzCode\Production Debugger Agent\agent\x64\OzCodeClrProfilerMultiplexer.dll
   CLR_PROFILERS | OZCODE;DD
   CLR_OZCODE_PROFILER | {DBE6D54B-4A04-4FD0-83EB-12A1A9DEC58B}
   CLR_OZCODE_PROFILER_PATH_32 | C:\Program Files\OzCode\Production Debugger Agent\agent\x32\OzCodeClrProfiler.dll
   CLR_OZCODE_PROFILER_PATH_64 | C:\Program Files\OzCode\Production Debugger Agent\agent\x64\OzCodeClrProfiler.dll
   CLR_OZCODE_ENABLE_PROFILING | 1
   CLR_OZCODE_REVERT_REJIT_CALL_ORDER | 0
   CLR_OZCODE_PRIORITY | 2.0
   CLR_OZCODE_HOME | C:\Program Files\OzCode\Production Debugger Agent\agent\net461
   CLR_PROFILER_HOME | C:\Program Files\OzCode\Production Debugger Agent\agent\net461
   CLR_DD_PROFILER | {846F5F1C-F9AE-4B07-969E-05C26BC060D8}
   CLR_DD_PROFILER_PATH | C:\Program Files\Datadog\\.NET Tracer\Datadog.Trace.ClrProfiler.Native.dll
   CLR_DD_ENABLE_PROFILING | 1
   CLR_DD_PRIORITY | 1.0
   CLR_DD_REVERT_REJIT_CALL_ORDER |0
   CLR_DD_HOME | C:\Program Files\Datadog\\.NET Tracer\net461
   OzCode_Agent_ForceLoad | true
   OzCode_Agent_ServerAddress | https://service.oz-code.com/
   OzCode_Agent_Token | < YOUR-OZCODE-APP-TOKEN >

   For .Net Core:

   Variable |  Value 
   --- | ---
   CORECLR_ENABLE_PROFILING | 1
   CORECLR_PROFILER | {3BF080FE-7DEB-4051-AEF1-BD3AB01F1883}
   CORECLR_PROFILER_PATH_32 | C:\Program Files\OzCode\Production Debugger Agent\agent\x32\OzCodeClrProfilerMultiplexer.dll
   CORECLR_PROFILER_PATH_64 | C:\Program Files\OzCode\Production Debugger Agent\agent\x64\OzCodeClrProfilerMultiplexer.dll
   CORECLR_PROFILERS | OZCODE;DD
   CORECLR_OZCODE_PROFILER | {09992526-3e32-4995-8d3d-a97c839393e1}
   CORECLR_OZCODE_PROFILER_PATH_32 | C:\Program Files\OzCode\Production Debugger Agent\agent\x32\OzCodeClrProfiler.dll
   CORECLR_OZCODE_PROFILER_PATH_64 | C:\Program Files\OzCode\Production Debugger Agent\agent\x64\OzCodeClrProfiler.dll
   CORECLR_OZCODE_ENABLE_PROFILING | 1
   CORECLR_OZCODE_REVERT_REJIT_CALL_ORDER | 0
   CORECLR_OZCODE_PRIORITY | 2.0
   CORECLR_OZCODE_HOME | C:\Program Files\OzCode\Production Debugger Agent\agent\netstandard2.0
   CORECLR_PROFILER_HOME | C:\Program Files\OzCode\Production Debugger Agent\agent\netstandard2.0
   CORECLR_DD_PROFILER | {846F5F1C-F9AE-4B07-969E-05C26BC060D8}
   CORECLR_DD_PROFILER_PATH | C:\Program Files\Datadog\\.NET Tracer\Datadog.Trace.ClrProfiler.Native.dll
   CORECLR_DD_ENABLE_PROFILING | 1
   CORECLR_DD_PRIORITY | 1.0
   CORECLR_DD_REVERT_REJIT_CALL_ORDER |0
   CORECLR_DD_HOME | C:\Program Files\Datadog\\.NET Tracer\netcoreapp3.1
   OzCode_Agent_ForceLoad | true
   OzCode_Agent_ServerAddress | https://service.oz-code.com/
   OzCode_Agent_Token | < YOUR-OZCODE-APP-TOKEN >

### Step 3: Activate datadog-ozcode Agent integration

1. install the datadog-ozcode Agent integration: 
   
   Windows:
   ```
   "%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" integration install --third-party datadog-ozcode==0.0.1
   ```

   Linux: 
   ```
   sudo -u dd‐agent datadog‐agent integration install --third-party datadog-ozcode==0.0.1
   ``` 
2. Install OzCode.ProductionDebugger.Client NuGet package to inject Datadog tracing

    1.  Capture DD_TRACE_ID as Contextual data:

    ```C#
    public class ActivityTrackingMiddleware
    {
        private readonly RequestDelegate _next;

        public ActivityTrackingMiddleware(RequestDelegate next)
        {
            _next = next;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            OzCodeContext.Current.SetTag("DD_TRACE_ID",CorrelationIdentifier.TraceId.ToString());

            // Call the next delegate/middleware in the pipeline
            await _next(context);
        }        
    }
    ```

    2. Send Tracepoints Hit to Datadog using logs

    ```C#
    public class TracepointEnricher : ILogEventEnricher
    {
        private TracepointHit _tracepointHit;
        public TracepointEnricher(TracepointHit tracepointHit)
        {
            _tracepointHit = tracepointHit;
        }

        public void Enrich(LogEvent logEvent, ILogEventPropertyFactory propertyFactory)
        {
            foreach (var kv in _tracepointHit.MessageProperties)
            {
                logEvent.AddOrUpdateProperty(new LogEventProperty(kv.Key, new ScalarValue(kv.Value)));
            }
            logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty("Context", _tracepointHit.ContexualData.Sanitize(), true));
            logEvent.AddOrUpdateProperty(propertyFactory.CreateProperty("Tracepoint", new
            {
                TracepointUrl = _tracepointHit.TracepointHitUrl,
                Timestamp = _tracepointHit.Timestamp,
                @Module = _tracepointHit.ModuleName,
                @Class = _tracepointHit.ClassName,
                @Method = _tracepointHit.MethodName
            }, true));
        }
    }    

    public static class Program
    {
        public static void Main() {
            //register Tracepoint integration
            OzCodeIntergations.OnTracepointHit.Register("Serilog", (tracepointHit) =>
            {
                using (LogContext.Push(new TracepointEnricher(tracepointHit)))
                {
                    Log.Logger.Information(tracepointHit.MessageTemplate);
                }
            });

            //....
        }
    }
    ```


### Configuration

1. Enable C# logging for your application to use dynamic tracing

2. Enable APM tracing
  
3. [Restart the Agent][2].

4. When using tracepoint log stream, add the following configruations at the app.datadoghq.com:
   1. Add Log pipeline with 
       * Date remapper from `Properties.Tracepoint.Timestamp`
       * TraceId remapper from `Properties.Context.DD_TRACE_ID` or `Properties.dd_trace_id`
   2. Create string log facet `@Properties.Tracepoint.Module`
   3. Create string log facet `@Properties.Tracepoint.Class`

### Validation

1. [Run the Agent's status subcommand][3] and look for `ozcode` under the Checks section.

    Alternatively, you can get detailed information about the integration using the following command.
    
    Windows: 
    ```
    "%PROGRAMFILES%\Datadog\Datadog Agent\bin\agent.exe" check ozcode
    ```

    Linux: 
    ```
    sudo ‐u dd‐agent datadog‐agent check ozcode
    ```


## Support
For support or feature requests, contact www.oz-code.com through the following channels:

- Support: support@oz-code.com
- Sales: sales@oz-code.com
- Phone: 781-708-2561

You can also get more information at one of the following links:

[Documentation][5]
[Q&A][6]
[Release Notes][7]


---
Made with ❤️ in Israel

---

This application is made available through the Marketplace and is supported by a Datadog Technology Partner. [Click here][4] to purchase this application.

[1a]: https://docs.datadoghq.com/tracing/setup_overview/setup/dotnet-core/?tab=windows
[1b]: https://docs.datadoghq.com/tracing/setup_overview/setup/dotnet-core/?tab=windows
[2]: https://docs.datadoghq.com/agent/guide/agent-commands/#start-stop-and-restart-the-agent
[3]: https://docs.datadoghq.com/agent/guide/agent-commands/#agent-status-and-information
[4]: https://app.datadoghq.com/marketplace/app/ozcode/pricing
[5]: https://oz-code.com/knowledge-base/production-debugger/documentation 
[6]: https://oz-code.com/knowledge-base/production-debugger/pd-q-and-a
[7]: https://oz-code.com/knowledge-base/production-debugger/pd-release-notes
