/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;
/* Find the L3 size by running `getconf -a | grep CACHE` */
const LLCSIZE = 32 * 1024 * 1024;
/* Collect traces for 10 seconds; you can vary this */
const TIME = 10000;
/* Collect traces every 10ms; you can vary this */
const P = 10;

function sweep(P) {
    const buffer = new Uint8Array(LLCSIZE);
    const K = Math.floor(TIME / P);
    const counts = [];

    for (let k = 0; k < K; k++) {
        let count = 0;
        const start = performance.now();

        while ((performance.now() - start) < P) {
            for (let i = 0; i < buffer.length; i += LINESIZE) {
                buffer[i];
            }
            count++;
        }

        counts.push(count);
    }

    return counts;
}

console.log("Trace worker loaded");

self.addEventListener("message", (e) => {
    console.log("Trace worker received:", e.data);

    if (e.data?.type === "sweep") {
        const result = sweep(e.data.payload || 10);
        console.log("Trace worker: sending back", result.length, "samples");
        self.postMessage(result);
    }
});
