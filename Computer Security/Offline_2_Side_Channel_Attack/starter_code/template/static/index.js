function app() {
  return {
    /* This is the main app object containing all the application state and methods. */
    // The following properties are used to store the state of the application

    // results of cache latency measurements
    latencyResults: null,
    // local collection of trace data
    traceData: [],
    // Local collection of heapmap images
    heatmaps: [],

    // Current status message
    status: "",
    // Is any worker running?
    isCollecting: false,
    // Is the status message an error?
    statusIsError: false,
    // Show trace data in the UI?
    showingTraces: false,

    fetchResults() {
      console.log("fetchResults() called – no-op for now.");
    },


    // Collect latency data using warmup.js worker
    async collectLatencyData() {
      this.isCollecting = true;
      this.status = "Collecting latency data...";
      this.latencyResults = null;
      this.statusIsError = false;
      this.showingTraces = false;

      try {
        // Create a worker
        let worker = new Worker("warmup.js");

        // Start the measurement and wait for result
        const results = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });

        // Update results
        this.latencyResults = results;
        this.status = "Latency data collection complete!";

        // Terminate worker
        worker.terminate();
      } catch (error) {
        console.error("Error collecting latency data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Collect trace data using worker.js and send to backend
    async collectTraceData() {
      this.isCollecting = true;
      this.status = "Collecting trace data...";
      this.statusIsError = false;
      this.showingTraces = true;

      try {
        const worker = new Worker("worker.js");

        const trace = await new Promise((resolve) => {
          worker.onmessage = (e) => {
            console.log("Trace received from worker:", e.data);
            resolve(e.data);
          };
          worker.postMessage({ type: "sweep", payload: 10 });
        });

        worker.terminate();

        console.log("Sending trace to backend:", trace.length);

        const response = await fetch("/collect_trace", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ trace }),
        });

        const result = await response.json();
        console.log("Backend returned:", result);

        const { image_url } = result;

        if (image_url) {
          this.heatmaps.push(image_url);
          this.status = "Trace collected and heatmap generated!";
        } else {
          throw new Error("No image received from server.");
        }
      } catch (err) {
        console.error("Trace collection failed:", err);
        this.status = "Error during trace collection: " + err.message;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },


    // Download the trace data as JSON (array of arrays format for ML)
    async downloadTraces() {
      try {
        const res = await fetch("/download_traces");
        if (!res.ok) throw new Error("Failed to download traces");

        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "traces.json";
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Download failed:", err);
        this.status = "Download failed: " + err.message;
        this.statusIsError = true;
      }
    },

    // Clear all results from the server
    async clearResults() {
      try {
        const res = await fetch("/api/clear_results", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        if (!res.ok) throw new Error("Failed to clear results");
        this.traceData = [];
        this.heatmaps = [];
        this.status = "All results cleared!";
        this.statusIsError = false;
      } catch (err) {
        this.status = "Failed to clear results: " + err.message;
        this.statusIsError = true;
      }
    }

  };
}
