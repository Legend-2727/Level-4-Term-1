console.log("Worker loaded");

const LINESIZE = 64;

function readNlines(n) {
  const buffer = new Uint8Array(n * LINESIZE);
  const accesses = 10;
  const timings = [];

  for (let r = 0; r < accesses; r++) {
    const start = performance.now();
    for (let i = 0; i < buffer.length; i += LINESIZE) {
      buffer[i];
    }
    const end = performance.now();
    timings.push(end - start);
  }

  timings.sort((a, b) => a - b);
  const mid = Math.floor(timings.length / 2);
  return timings.length % 2 === 0
    ? (timings[mid - 1] + timings[mid]) / 2
    : timings[mid];
}

self.addEventListener("message", (e) => {
  console.log("Warmup worker received:", e.data);

  if (e.data === "start") {
    const results = {};
    for (let n = 1; n <= 10_000_000; n *= 10) {
      results[n] = readNlines(n);
    }
    console.log("Warmup sending results:", results);
    self.postMessage(results);
  }
});
