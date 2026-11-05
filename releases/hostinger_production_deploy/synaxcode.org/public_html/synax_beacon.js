/**
 * SYNAX Telemetry Beacon v0.5.0 (`synax_beacon.js`)
 * Lightweight, privacy-first, cookie-less website analytics client.
 * Dispatches non-blocking telemetry pings to SYNAX Metrics Hub.
 */
(function() {
  if (typeof window === 'undefined') return;

  function sendPing() {
    try {
      const hostname = window.location.hostname || 'synaxcode.com';
      const path = window.location.pathname || '/';
      const referrer = document.referrer ? (new URL(document.referrer)).hostname : 'Doğrudan';
      const screenRes = `${window.screen.width}x${window.screen.height}`;
      const loadTimeMs = window.performance && window.performance.timing 
        ? Math.max(0, window.performance.timing.loadEventEnd - window.performance.timing.navigationStart)
        : Math.round(performance.now());

      const payload = {
        hostname: hostname,
        path: path,
        referrer: referrer,
        resolution: screenRes,
        latency_ms: loadTimeMs,
        geo: 'TR', // Default or detected by edge proxy
        timestamp: new Date().toISOString()
      };

      const dataStr = JSON.stringify(payload);
      const endpoint = '/api/telemetry/beacon';

      if (navigator.sendBeacon) {
        const blob = new Blob([dataStr], { type: 'application/json' });
        navigator.sendBeacon(endpoint, blob);
      } else if (window.fetch) {
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: dataStr,
          keepalive: true
        }).catch(function() {});
      }
    } catch (e) {
      // Fail silently to never affect user browsing
    }
  }

  // Send after window load to capture real page render timing
  if (document.readyState === 'complete') {
    setTimeout(sendPing, 200);
  } else {
    window.addEventListener('load', function() {
      setTimeout(sendPing, 200);
    });
  }
})();
